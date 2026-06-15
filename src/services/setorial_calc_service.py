from __future__ import annotations

import argparse
import json
import math

import numpy as np
import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


def clamp(value: float, min_value: float = 0, max_value: float = 100) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return float(max(min_value, min(max_value, value)))


def scenario_1_10(score: float) -> int:
    if score is None or pd.isna(score):
        return 1
    return max(1, min(10, math.ceil(float(score) / 10)))


def normalize_last_position(series: pd.Series, invert: bool = False, neutral: float = 50) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < 2:
        return neutral

    p5 = s.quantile(0.05)
    p95 = s.quantile(0.95)
    last = s.iloc[-1]

    if p95 == p5:
        score = neutral
    else:
        score = ((last - p5) / (p95 - p5)) * 100
        score = clamp(score)

    if invert:
        score = 100 - score

    return clamp(score)


def pct_change_last(series: pd.Series, months: int = 3) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) <= months:
        return 0.0
    base = float(s.iloc[-months-1])
    last = float(s.iloc[-1])
    if base == 0:
        return 0.0
    return ((last / base) - 1) * 100


def carregar_series_setoriais(uf: str = "MG") -> pd.DataFrame:
    engine = get_engine()

    sql = """
        SELECT
            DATE_TRUNC('month', data)::DATE AS mes,
            COALESCE(NULLIF(uf, ''), 'BR') AS uf,
            indicador,
            produto,
            categoria,
            AVG(valor) AS valor
        FROM dw.fato_indicador_setorial
        WHERE COALESCE(NULLIF(uf, ''), 'BR') IN (:uf, 'BR')
        GROUP BY DATE_TRUNC('month', data)::DATE, COALESCE(NULLIF(uf, ''), 'BR'), indicador, produto, categoria
        ORDER BY mes
    """

    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params={"uf": uf})

    return df


def carregar_dolar_mensal() -> pd.DataFrame:
    engine = get_engine()

    sql = """
        SELECT
            DATE_TRUNC('month', data)::DATE AS mes,
            AVG(valor) AS valor
        FROM dw.fato_serie_historica
        WHERE indicador = 'Dólar venda'
        GROUP BY DATE_TRUNC('month', data)::DATE
        ORDER BY mes
    """

    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn)

    if df.empty:
        return df

    df["indicador"] = "dolar_venda"
    df["produto"] = "Dólar"
    df["categoria"] = "cambio"
    df["uf"] = "BR"
    return df[["mes", "uf", "indicador", "produto", "categoria", "valor"]]


def preparar_pivot(uf: str = "MG") -> pd.DataFrame:
    df = carregar_series_setoriais(uf=uf)
    dolar = carregar_dolar_mensal()

    if not dolar.empty:
        df = pd.concat([df, dolar], ignore_index=True)

    if df.empty:
        raise ValueError("Nenhum indicador setorial encontrado. Rode a carga do arquivo exemplo primeiro.")

    # Prioriza série da UF. Se não existir, usa BR.
    chosen = []
    for indicador, group in df.groupby("indicador"):
        g_uf = group[group["uf"] == uf]
        if not g_uf.empty:
            chosen.append(g_uf)
        else:
            chosen.append(group[group["uf"] == "BR"])

    df2 = pd.concat(chosen, ignore_index=True)
    pivot = df2.pivot_table(index="mes", columns="indicador", values="valor", aggfunc="mean").sort_index()
    return pivot


def calcular_indices_setoriais(uf: str = "MG") -> tuple[pd.DataFrame, pd.DataFrame]:
    pivot = preparar_pivot(uf=uf)

    required_proteins = ["preco_tilapia_kg", "preco_frango_kg", "preco_suino_kg", "preco_bovino_kg", "preco_ovos_duzia"]
    required_costs = ["preco_milho_sc", "preco_soja_sc", "preco_farelo_soja_ton", "preco_fish_meal_ton", "dolar_venda"]

    data_ref = pd.to_datetime(pivot.index.max()).date()

    # Competitividade: quanto menor o preço relativo da tilápia contra concorrentes, melhor.
    ratios = pd.DataFrame(index=pivot.index)
    if all(col in pivot.columns for col in ["preco_tilapia_kg", "preco_frango_kg"]):
        ratios["tilapia_frango"] = pivot["preco_tilapia_kg"] / pivot["preco_frango_kg"]
    if all(col in pivot.columns for col in ["preco_tilapia_kg", "preco_suino_kg"]):
        ratios["tilapia_suino"] = pivot["preco_tilapia_kg"] / pivot["preco_suino_kg"]
    if all(col in pivot.columns for col in ["preco_tilapia_kg", "preco_bovino_kg"]):
        ratios["tilapia_bovino"] = pivot["preco_tilapia_kg"] / pivot["preco_bovino_kg"]
    if all(col in pivot.columns for col in ["preco_tilapia_kg", "preco_ovos_duzia"]):
        ratios["tilapia_ovos"] = pivot["preco_tilapia_kg"] / pivot["preco_ovos_duzia"]

    comp_scores = []
    comp_factors = []
    for col in ratios.columns:
        score = normalize_last_position(ratios[col], invert=True, neutral=50)
        comp_scores.append(score)
        comp_factors.append({
            "fator": col,
            "descricao": "Preço relativo da tilápia contra proteína concorrente. Quanto menor, mais competitivo.",
            "impacto": score,
            "direcao": "positiva",
            "unidade": "score",
        })

    score_competitividade = float(np.mean(comp_scores)) if comp_scores else 50.0

    # Pressão de custo: variações de insumos em 3 meses.
    cost_weights = {
        "preco_milho_sc": 0.20,
        "preco_soja_sc": 0.20,
        "preco_farelo_soja_ton": 0.20,
        "preco_fish_meal_ton": 0.25,
        "dolar_venda": 0.15,
    }
    cost_score = 0.0
    cost_weight_sum = 0.0
    cost_factors = []

    for indicador, peso in cost_weights.items():
        if indicador not in pivot.columns:
            continue
        var_3m = pct_change_last(pivot[indicador], months=3)
        # variação de +15% em 3 meses = pressão máxima.
        score = clamp((max(var_3m, 0) / 15) * 100)
        cost_score += peso * score
        cost_weight_sum += peso
        cost_factors.append({
            "fator": indicador,
            "descricao": "Variação de 3 meses do insumo/câmbio usado na pressão de custo.",
            "variacao_3m_pct": var_3m,
            "impacto": score,
            "peso": peso,
            "direcao": "negativa",
            "unidade": "%",
        })

    score_pressao_custo = cost_score / cost_weight_sum if cost_weight_sum else 50.0
    score_pressao_custo = clamp(score_pressao_custo)

    # Risco de substituição: frango caindo e tilápia subindo aumenta risco.
    tilapia_3m = pct_change_last(pivot["preco_tilapia_kg"], 3) if "preco_tilapia_kg" in pivot.columns else 0
    frango_3m = pct_change_last(pivot["preco_frango_kg"], 3) if "preco_frango_kg" in pivot.columns else 0
    suino_3m = pct_change_last(pivot["preco_suino_kg"], 3) if "preco_suino_kg" in pivot.columns else 0

    substituicao_raw = max(tilapia_3m, 0) + max(-frango_3m, 0) * 1.4 + max(-suino_3m, 0) * 0.8
    score_substituicao = clamp((substituicao_raw / 12) * 100)

    sub_factors = [
        {
            "fator": "tilapia_3m",
            "descricao": "Variação da tilápia em 3 meses.",
            "impacto": tilapia_3m,
            "direcao": "negativa",
            "unidade": "%",
        },
        {
            "fator": "frango_3m",
            "descricao": "Queda do frango aumenta risco de substituição contra pescado.",
            "impacto": frango_3m,
            "direcao": "negativa",
            "unidade": "%",
        },
        {
            "fator": "suino_3m",
            "descricao": "Queda do suíno também pressiona substituição.",
            "impacto": suino_3m,
            "direcao": "negativa",
            "unidade": "%",
        },
    ]

    confianca = min(85, 35 + int((len(pivot.dropna(how="all")) / 24) * 50))

    indices = pd.DataFrame([
        {
            "data_referencia": data_ref,
            "uf": uf,
            "indice": "competitividade_pescado",
            "score": clamp(score_competitividade),
            "cenario_1_10": scenario_1_10(score_competitividade),
            "confianca": confianca,
            "metodo": "competitividade_proteinas_v1",
            "principais_fatores": json.dumps(comp_factors, ensure_ascii=False),
        },
        {
            "data_referencia": data_ref,
            "uf": uf,
            "indice": "pressao_custo_racao",
            "score": clamp(score_pressao_custo),
            "cenario_1_10": scenario_1_10(score_pressao_custo),
            "confianca": confianca,
            "metodo": "pressao_custo_v1",
            "principais_fatores": json.dumps(cost_factors, ensure_ascii=False),
        },
        {
            "data_referencia": data_ref,
            "uf": uf,
            "indice": "risco_substituicao_proteinas",
            "score": clamp(score_substituicao),
            "cenario_1_10": scenario_1_10(score_substituicao),
            "confianca": confianca,
            "metodo": "risco_substituicao_v1",
            "principais_fatores": json.dumps(sub_factors, ensure_ascii=False),
        },
    ])

    alertas = []
    if score_pressao_custo >= 70:
        alertas.append({
            "data_referencia": data_ref,
            "uf": uf,
            "tipo_alerta": "pressao_custo_alta",
            "severidade": "alto" if score_pressao_custo < 85 else "critico",
            "titulo": "Pressão de custo elevada",
            "mensagem": "Milho, soja, farelo, farinha de peixe ou dólar indicam pressão de custo para pescados/aquicultura.",
            "score_relacionado": clamp(score_pressao_custo),
            "status": "ativo",
            "principais_fatores": json.dumps(cost_factors, ensure_ascii=False),
        })

    if score_substituicao >= 65:
        alertas.append({
            "data_referencia": data_ref,
            "uf": uf,
            "tipo_alerta": "risco_substituicao_proteinas",
            "severidade": "medio" if score_substituicao < 80 else "alto",
            "titulo": "Risco de substituição entre proteínas",
            "mensagem": "Movimento relativo entre tilápia, frango e suíno sugere risco de substituição no varejo.",
            "score_relacionado": clamp(score_substituicao),
            "status": "ativo",
            "principais_fatores": json.dumps(sub_factors, ensure_ascii=False),
        })

    if score_competitividade <= 40:
        alertas.append({
            "data_referencia": data_ref,
            "uf": uf,
            "tipo_alerta": "competitividade_pescado_baixa",
            "severidade": "medio" if score_competitividade > 25 else "alto",
            "titulo": "Pescado perdendo competitividade relativa",
            "mensagem": "Preço relativo da tilápia/pescado ficou desfavorável contra proteínas concorrentes.",
            "score_relacionado": clamp(100 - score_competitividade),
            "status": "ativo",
            "principais_fatores": json.dumps(comp_factors, ensure_ascii=False),
        })

    alertas_df = pd.DataFrame(alertas)
    return indices, alertas_df


def salvar_indices_alertas(indices: pd.DataFrame, alertas: pd.DataFrame) -> tuple[int, int]:
    engine = get_engine()

    with engine.begin() as conn:
        if not indices.empty:
            conn.execute(text("""
                INSERT INTO app.fato_indice_setorial (
                    data_referencia, uf, indice, score, cenario_1_10, confianca,
                    metodo, principais_fatores
                )
                VALUES (
                    :data_referencia, :uf, :indice, :score, :cenario_1_10, :confianca,
                    :metodo, CAST(:principais_fatores AS JSONB)
                )
                ON CONFLICT (data_referencia, uf, indice)
                DO UPDATE SET
                    score = EXCLUDED.score,
                    cenario_1_10 = EXCLUDED.cenario_1_10,
                    confianca = EXCLUDED.confianca,
                    metodo = EXCLUDED.metodo,
                    principais_fatores = EXCLUDED.principais_fatores,
                    data_calculo = NOW();
            """), indices.to_dict(orient="records"))

        if not alertas.empty:
            conn.execute(text("""
                INSERT INTO app.fato_alerta_setorial (
                    data_referencia, uf, tipo_alerta, severidade, titulo, mensagem,
                    score_relacionado, status, principais_fatores
                )
                VALUES (
                    :data_referencia, :uf, :tipo_alerta, :severidade, :titulo, :mensagem,
                    :score_relacionado, :status, CAST(:principais_fatores AS JSONB)
                )
                ON CONFLICT (data_referencia, uf, tipo_alerta)
                DO UPDATE SET
                    severidade = EXCLUDED.severidade,
                    titulo = EXCLUDED.titulo,
                    mensagem = EXCLUDED.mensagem,
                    score_relacionado = EXCLUDED.score_relacionado,
                    status = EXCLUDED.status,
                    principais_fatores = EXCLUDED.principais_fatores,
                    data_criacao = NOW();
            """), alertas.to_dict(orient="records"))

        conn.execute(text("REFRESH MATERIALIZED VIEW app.mv_indice_setorial_atual"))
        conn.execute(text("REFRESH MATERIALIZED VIEW app.mv_alerta_setorial_atual"))

    return len(indices), len(alertas)


def main():
    parser = argparse.ArgumentParser(description="Calcular índices setoriais de proteínas e grãos")
    parser.add_argument("--uf", default="MG", help="UF para cálculo. Padrão: MG")
    parser.add_argument("--salvar", action="store_true", help="Salvar no banco")
    args = parser.parse_args()

    indices, alertas = calcular_indices_setoriais(uf=args.uf)

    print("\nÍndices setoriais calculados:")
    print(indices[["uf", "indice", "score", "cenario_1_10", "confianca"]].to_string(index=False))

    if not alertas.empty:
        print("\nAlertas gerados:")
        print(alertas[["uf", "tipo_alerta", "severidade", "titulo", "score_relacionado"]].to_string(index=False))
    else:
        print("\nNenhum alerta crítico gerado.")

    if args.salvar:
        qtd_indices, qtd_alertas = salvar_indices_alertas(indices, alertas)
        print(f"\n✅ Índices salvos/atualizados: {qtd_indices}")
        print(f"✅ Alertas salvos/atualizados: {qtd_alertas}")


if __name__ == "__main__":
    main()
