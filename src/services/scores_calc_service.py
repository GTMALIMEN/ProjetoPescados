from __future__ import annotations

import argparse
import json
import math

import numpy as np
import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine
from src.utils.logs import get_logger


logger = get_logger(__name__)


def clamp(value: float, min_value: float = 0, max_value: float = 100) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return float(max(min_value, min(max_value, value)))


def scenario_1_10(score: float) -> int:
    if score is None or pd.isna(score):
        return 1
    return max(1, min(10, math.ceil(float(score) / 10.0)))


def normalize_series(s: pd.Series, invert: bool = False, neutral_if_constant: float = 50.0) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce").fillna(0)
    p5 = s.quantile(0.05)
    p95 = s.quantile(0.95)

    if p95 == p5:
        out = pd.Series([neutral_if_constant] * len(s), index=s.index, dtype=float)
    else:
        out = ((s - p5) / (p95 - p5)) * 100
        out = out.clip(lower=0, upper=100)

    if invert:
        out = 100 - out

    return out


def table_exists(engine, regclass: str) -> bool:
    with engine.begin() as conn:
        return bool(conn.execute(text("SELECT to_regclass(:name) IS NOT NULL"), {"name": regclass}).scalar())


def get_latest_macro(engine) -> dict:
    with engine.begin() as conn:
        dolar = pd.read_sql(text("""
            SELECT data, valor
            FROM dw.fato_serie_historica
            WHERE indicador = 'Dólar venda'
            ORDER BY data
        """), conn)

        ipca_alim = pd.read_sql(text("""
            SELECT data, valor
            FROM dw.fato_serie_historica
            WHERE indicador = 'IPCA alimentação e bebidas'
            ORDER BY data
        """), conn)

    dolar_var_90d = 0.0
    dolar_ultimo = None

    if len(dolar) >= 2:
        dolar["data"] = pd.to_datetime(dolar["data"])
        dolar = dolar.sort_values("data")
        ultimo = dolar.iloc[-1]
        data_ref_90 = ultimo["data"] - pd.Timedelta(days=90)
        anteriores = dolar[dolar["data"] <= data_ref_90]

        dolar_ultimo = float(ultimo["valor"])
        if not anteriores.empty:
            base = float(anteriores.iloc[-1]["valor"])
            if base:
                dolar_var_90d = ((dolar_ultimo / base) - 1) * 100

    ipca_alim_12m = 0.0
    if len(ipca_alim) > 0:
        ipca_alim_12m = float(pd.to_numeric(ipca_alim["valor"], errors="coerce").tail(12).sum())

    dolar_risk = clamp((max(dolar_var_90d, 0) / 15) * 100)
    ipca_risk = clamp((max(ipca_alim_12m, 0) / 10) * 100)
    pressao_macro = clamp((0.55 * dolar_risk) + (0.45 * ipca_risk))

    return {
        "dolar_ultimo": dolar_ultimo,
        "dolar_var_90d": dolar_var_90d,
        "ipca_alimentos_12m": ipca_alim_12m,
        "pressao_macro_norm": pressao_macro,
    }


def load_potencial_regional(engine, uf: str = "MG") -> pd.DataFrame:
    if not table_exists(engine, "app.mv_potencial_regional_atual"):
        return pd.DataFrame(columns=[
            "uf", "regiao_comercial", "score_potencial",
            "populacao_estimada", "venda_per_capita",
            "clientes_por_100k", "confianca_potencial"
        ])

    sql = """
        SELECT
            uf,
            COALESCE(regiao_comercial, 'Sem região') AS regiao_comercial,
            score_potencial,
            populacao_estimada,
            venda_per_capita,
            clientes_por_100k,
            confianca AS confianca_potencial
        FROM app.mv_potencial_regional_atual
        WHERE uf = :uf
    """

    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"uf": uf})


def load_indices_setoriais(engine, uf: str = "MG") -> dict:
    """
    Retorna os índices setoriais atuais.
    Interpretação:
    - competitividade_pescado: quanto maior, melhor para pescado.
    - pressao_custo_racao: quanto maior, maior risco.
    - risco_substituicao_proteinas: quanto maior, maior risco.
    """
    defaults = {
        "competitividade_pescado": 50.0,
        "pressao_custo_racao": 50.0,
        "risco_substituicao_proteinas": 50.0,
    }

    if not table_exists(engine, "app.mv_indice_setorial_atual"):
        return defaults

    sql = """
        SELECT indice, score
        FROM app.mv_indice_setorial_atual
        WHERE uf = :uf
    """

    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params={"uf": uf})

    if df.empty:
        return defaults

    out = defaults.copy()
    for _, row in df.iterrows():
        out[str(row["indice"])] = float(row["score"] or defaults.get(row["indice"], 50.0))

    return out


def load_base_regional(engine, uf: str = "MG") -> pd.DataFrame:
    with engine.begin() as conn:
        geo = pd.read_sql(text("""
            SELECT
                uf,
                COALESCE(regiao_comercial, 'Sem região') AS regiao_comercial,
                COUNT(*) AS qtd_municipios
            FROM dw.dim_geografia
            WHERE uf = :uf
            GROUP BY uf, COALESCE(regiao_comercial, 'Sem região')
            ORDER BY regiao_comercial
        """), conn, params={"uf": uf})

        vendas = pd.read_sql(text("""
            SELECT
                uf,
                COALESCE(regiao_comercial, 'Sem região') AS regiao_comercial,
                DATE_TRUNC('month', data)::DATE AS mes,
                SUM(valor_venda) AS valor_venda,
                SUM(volume_kg) AS volume_kg,
                COUNT(DISTINCT id_cliente) AS qtd_clientes
            FROM dw.fato_vendas
            WHERE uf = :uf
            GROUP BY uf, COALESCE(regiao_comercial, 'Sem região'), DATE_TRUNC('month', data)::DATE
            ORDER BY mes
        """), conn, params={"uf": uf})

    if geo.empty:
        raise ValueError(f"Nenhuma geografia encontrada para UF={uf}. Rode IBGE e regiões comerciais primeiro.")

    if vendas.empty:
        base = geo.copy()
        base["valor_venda"] = 0.0
        base["volume_kg"] = 0.0
        base["qtd_clientes"] = 0
        base["qtd_meses_venda"] = 0
        base["queda_vendas_pct"] = 0.0
        base["queda_volume_pct"] = 0.0
        base["tem_vendas"] = False
        base["data_referencia"] = pd.Timestamp.today().date()
    else:
        vendas["mes"] = pd.to_datetime(vendas["mes"])
        ultimo_mes = vendas["mes"].max()
        vendas_ult = vendas[vendas["mes"] == ultimo_mes].copy()

        vendas_ant = vendas[vendas["mes"] < ultimo_mes].copy()
        if not vendas_ant.empty:
            media_ant = (
                vendas_ant
                .groupby(["uf", "regiao_comercial"], as_index=False)
                .agg(
                    media_venda_ant=("valor_venda", "mean"),
                    media_volume_ant=("volume_kg", "mean"),
                    qtd_meses_venda=("mes", "nunique"),
                )
            )
        else:
            media_ant = pd.DataFrame(columns=["uf", "regiao_comercial", "media_venda_ant", "media_volume_ant", "qtd_meses_venda"])

        base = geo.merge(
            vendas_ult[["uf", "regiao_comercial", "valor_venda", "volume_kg", "qtd_clientes"]],
            on=["uf", "regiao_comercial"],
            how="left",
        ).merge(
            media_ant,
            on=["uf", "regiao_comercial"],
            how="left",
        )

        for col in ["valor_venda", "volume_kg", "qtd_clientes", "media_venda_ant", "media_volume_ant", "qtd_meses_venda"]:
            if col not in base.columns:
                base[col] = 0
            base[col] = pd.to_numeric(base[col], errors="coerce").fillna(0)

        base["queda_vendas_pct"] = np.where(
            base["media_venda_ant"] > 0,
            ((base["media_venda_ant"] - base["valor_venda"]) / base["media_venda_ant"]) * 100,
            0,
        )
        base["queda_volume_pct"] = np.where(
            base["media_volume_ant"] > 0,
            ((base["media_volume_ant"] - base["volume_kg"]) / base["media_volume_ant"]) * 100,
            0,
        )

        base["queda_vendas_pct"] = base["queda_vendas_pct"].clip(lower=0)
        base["queda_volume_pct"] = base["queda_volume_pct"].clip(lower=0)
        base["tem_vendas"] = base["valor_venda"] > 0
        base["data_referencia"] = ultimo_mes.date()

    potencial = load_potencial_regional(engine, uf=uf)
    if not potencial.empty:
        base = base.merge(potencial, on=["uf", "regiao_comercial"], how="left")
        base["tem_potencial"] = base["score_potencial"].notna()
    else:
        base["score_potencial"] = np.nan
        base["populacao_estimada"] = np.nan
        base["venda_per_capita"] = np.nan
        base["clientes_por_100k"] = np.nan
        base["confianca_potencial"] = np.nan
        base["tem_potencial"] = False

    base["score_potencial"] = pd.to_numeric(base["score_potencial"], errors="coerce").fillna(50)
    base["confianca_potencial"] = pd.to_numeric(base["confianca_potencial"], errors="coerce").fillna(0)
    base["populacao_estimada"] = pd.to_numeric(base["populacao_estimada"], errors="coerce").fillna(0)
    base["venda_per_capita"] = pd.to_numeric(base["venda_per_capita"], errors="coerce").fillna(0)
    base["clientes_por_100k"] = pd.to_numeric(base["clientes_por_100k"], errors="coerce").fillna(0)

    return base


def calcular_scores(uf: str = "MG") -> pd.DataFrame:
    engine = get_engine()
    base = load_base_regional(engine, uf=uf)
    macro = get_latest_macro(engine)
    setorial = load_indices_setoriais(engine, uf=uf)

    competitividade = float(setorial.get("competitividade_pescado", 50))
    pressao_custo = float(setorial.get("pressao_custo_racao", 50))
    risco_substituicao = float(setorial.get("risco_substituicao_proteinas", 50))

    # Score setorial é risco agregado. Quanto maior, pior.
    score_setorial = clamp(
        0.40 * (100 - competitividade) +
        0.35 * pressao_custo +
        0.25 * risco_substituicao
    )

    base["vendas_norm"] = normalize_series(base["valor_venda"], neutral_if_constant=35)
    base["volume_norm"] = normalize_series(base["volume_kg"], neutral_if_constant=35)
    base["clientes_norm"] = normalize_series(base["qtd_clientes"], neutral_if_constant=35)
    base["municipios_norm"] = normalize_series(base["qtd_municipios"], neutral_if_constant=50)

    cobertura = base["qtd_clientes"] / base["qtd_municipios"].replace(0, np.nan)
    cobertura = cobertura.fillna(0)
    base["baixa_cobertura_norm"] = normalize_series(cobertura, invert=True, neutral_if_constant=75)

    if bool(base["tem_potencial"].any()):
        base["score_oportunidade"] = (
            0.20 * base["vendas_norm"] +
            0.15 * base["volume_norm"] +
            0.15 * base["clientes_norm"] +
            0.10 * base["municipios_norm"] +
            0.15 * base["baixa_cobertura_norm"] +
            0.25 * base["score_potencial"]
        ).apply(clamp)
    else:
        base["score_oportunidade"] = (
            0.25 * base["vendas_norm"] +
            0.20 * base["volume_norm"] +
            0.20 * base["clientes_norm"] +
            0.15 * base["municipios_norm"] +
            0.20 * base["baixa_cobertura_norm"]
        ).apply(clamp)

    base["queda_vendas_norm"] = normalize_series(base["queda_vendas_pct"], neutral_if_constant=0)
    base["queda_volume_norm"] = normalize_series(base["queda_volume_pct"], neutral_if_constant=0)
    base["pressao_macro_norm"] = macro["pressao_macro_norm"]
    base["baixa_base_dados_norm"] = np.where(base["tem_vendas"], 10, 80)

    base["score_risco_base"] = (
        0.40 * base["queda_vendas_norm"] +
        0.25 * base["queda_volume_norm"] +
        0.25 * base["pressao_macro_norm"] +
        0.10 * base["baixa_base_dados_norm"]
    ).apply(clamp)

    base["score_setorial"] = score_setorial
    base["score_competitividade_setorial"] = competitividade
    base["score_pressao_custo_setorial"] = pressao_custo
    base["score_risco_substituicao_setorial"] = risco_substituicao

    # Risco final mistura risco regional com risco setorial.
    base["score_risco"] = (
        0.70 * base["score_risco_base"] +
        0.30 * base["score_setorial"]
    ).apply(clamp)

    base["risco_invertido"] = 100 - base["score_risco"]

    base["score_final"] = (
        0.50 * base["score_oportunidade"] +
        0.25 * base["risco_invertido"] +
        0.15 * base["score_potencial"] +
        0.10 * base["score_competitividade_setorial"]
    ).apply(clamp)

    base["cenario_1_10"] = base["score_final"].apply(scenario_1_10)

    base["confianca"] = np.where(
        base["tem_vendas"] & (base["qtd_meses_venda"] >= 2),
        70,
        np.where(base["tem_vendas"], 55, 35)
    )

    base["confianca"] = np.where(
        base["tem_potencial"],
        np.minimum(base["confianca"] + 10, 85),
        base["confianca"]
    )

    if setorial:
        base["confianca"] = np.minimum(base["confianca"] + 5, 90)

    base["score_pressao_custo"] = pressao_custo
    base["score_competitividade"] = competitividade
    base["score_sensibilidade_dolar"] = None
    base["metodo"] = "score_regional_com_potencial_setorial_v3"

    fatores = []
    for _, row in base.iterrows():
        fatores.append(json.dumps([
            {
                "fator": "vendas_regionais",
                "descricao": "Faturamento e volume da região no último mês disponível",
                "peso": 0.25,
                "direcao": "positiva",
                "impacto": float(row["vendas_norm"]),
                "unidade": "score",
                "confianca": int(row["confianca"]),
            },
            {
                "fator": "potencial_regional",
                "descricao": "Potencial calculado com população, venda per capita e clientes por 100 mil habitantes",
                "peso": 0.25,
                "direcao": "positiva",
                "impacto": float(row["score_potencial"]),
                "unidade": "score",
                "confianca": int(row["confianca_potencial"] or 0),
            },
            {
                "fator": "competitividade_pescado",
                "descricao": "Competitividade do pescado contra proteínas concorrentes. Quanto menor, pior.",
                "peso": 0.15,
                "direcao": "positiva",
                "impacto": float(competitividade),
                "unidade": "score",
                "confianca": 85,
            },
            {
                "fator": "pressao_custo_racao",
                "descricao": "Pressão de custo por grãos, farinha de peixe e dólar. Quanto maior, pior.",
                "peso": 0.15,
                "direcao": "negativa",
                "impacto": float(pressao_custo),
                "unidade": "score",
                "confianca": 85,
            },
            {
                "fator": "risco_substituicao_proteinas",
                "descricao": "Risco de migração de consumo entre pescado e proteínas concorrentes.",
                "peso": 0.10,
                "direcao": "negativa",
                "impacto": float(risco_substituicao),
                "unidade": "score",
                "confianca": 85,
            },
            {
                "fator": "pressao_macro",
                "descricao": "Pressão macro calculada por dólar e IPCA alimentos",
                "peso": 0.10,
                "direcao": "negativa",
                "impacto": float(row["pressao_macro_norm"]),
                "unidade": "score",
                "confianca": 60,
            },
        ], ensure_ascii=False))

    base["principais_fatores"] = fatores

    cols = [
        "data_referencia",
        "uf",
        "regiao_comercial",
        "score_oportunidade",
        "score_risco",
        "score_pressao_custo",
        "score_competitividade",
        "score_sensibilidade_dolar",
        "score_potencial",
        "score_setorial",
        "score_competitividade_setorial",
        "score_pressao_custo_setorial",
        "score_risco_substituicao_setorial",
        "score_final",
        "cenario_1_10",
        "confianca",
        "metodo",
        "principais_fatores",
        "valor_venda",
        "volume_kg",
        "qtd_clientes",
        "qtd_municipios",
        "populacao_estimada",
        "venda_per_capita",
        "clientes_por_100k",
        "queda_vendas_pct",
        "queda_volume_pct",
    ]

    return base[cols].sort_values("score_final", ascending=False)


def salvar_scores(df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    records = []
    for _, row in df.iterrows():
        records.append({
            "data_referencia": row["data_referencia"],
            "pais": "Brasil",
            "uf": row["uf"] or "",
            "regiao_ibge": "",
            "regiao_comercial": row["regiao_comercial"] or "",
            "municipio": "",
            "produto": "",
            "proteina": "",
            "score_oportunidade": float(row["score_oportunidade"]),
            "score_risco": float(row["score_risco"]),
            "score_pressao_custo": float(row["score_pressao_custo"]) if pd.notna(row["score_pressao_custo"]) else None,
            "score_competitividade": float(row["score_competitividade"]) if pd.notna(row["score_competitividade"]) else None,
            "score_sensibilidade_dolar": None,
            "score_potencial": float(row["score_potencial"]) if pd.notna(row["score_potencial"]) else None,
            "score_setorial": float(row["score_setorial"]) if pd.notna(row["score_setorial"]) else None,
            "score_competitividade_setorial": float(row["score_competitividade_setorial"]) if pd.notna(row["score_competitividade_setorial"]) else None,
            "score_pressao_custo_setorial": float(row["score_pressao_custo_setorial"]) if pd.notna(row["score_pressao_custo_setorial"]) else None,
            "score_risco_substituicao_setorial": float(row["score_risco_substituicao_setorial"]) if pd.notna(row["score_risco_substituicao_setorial"]) else None,
            "score_final": float(row["score_final"]),
            "cenario_1_10": int(row["cenario_1_10"]),
            "confianca": float(row["confianca"]),
            "metodo": row["metodo"],
            "principais_fatores": row["principais_fatores"],
        })

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.fato_score_regional (
                data_referencia,
                pais,
                uf,
                regiao_ibge,
                regiao_comercial,
                municipio,
                produto,
                proteina,
                score_oportunidade,
                score_risco,
                score_pressao_custo,
                score_competitividade,
                score_sensibilidade_dolar,
                score_potencial,
                score_setorial,
                score_competitividade_setorial,
                score_pressao_custo_setorial,
                score_risco_substituicao_setorial,
                score_final,
                cenario_1_10,
                confianca,
                metodo,
                principais_fatores
            )
            VALUES (
                :data_referencia,
                :pais,
                :uf,
                :regiao_ibge,
                :regiao_comercial,
                :municipio,
                :produto,
                :proteina,
                :score_oportunidade,
                :score_risco,
                :score_pressao_custo,
                :score_competitividade,
                :score_sensibilidade_dolar,
                :score_potencial,
                :score_setorial,
                :score_competitividade_setorial,
                :score_pressao_custo_setorial,
                :score_risco_substituicao_setorial,
                :score_final,
                :cenario_1_10,
                :confianca,
                :metodo,
                CAST(:principais_fatores AS JSONB)
            )
            ON CONFLICT (
                data_referencia,
                pais,
                uf,
                regiao_ibge,
                regiao_comercial,
                municipio,
                produto,
                proteina
            )
            DO UPDATE SET
                score_oportunidade = EXCLUDED.score_oportunidade,
                score_risco = EXCLUDED.score_risco,
                score_pressao_custo = EXCLUDED.score_pressao_custo,
                score_competitividade = EXCLUDED.score_competitividade,
                score_sensibilidade_dolar = EXCLUDED.score_sensibilidade_dolar,
                score_potencial = EXCLUDED.score_potencial,
                score_setorial = EXCLUDED.score_setorial,
                score_competitividade_setorial = EXCLUDED.score_competitividade_setorial,
                score_pressao_custo_setorial = EXCLUDED.score_pressao_custo_setorial,
                score_risco_substituicao_setorial = EXCLUDED.score_risco_substituicao_setorial,
                score_final = EXCLUDED.score_final,
                cenario_1_10 = EXCLUDED.cenario_1_10,
                confianca = EXCLUDED.confianca,
                metodo = EXCLUDED.metodo,
                principais_fatores = EXCLUDED.principais_fatores,
                data_calculo = NOW();
        """), records)

        conn.execute(text("REFRESH MATERIALIZED VIEW app.mv_score_regional_atual"))

    return len(records)


def main():
    parser = argparse.ArgumentParser(description="Calcular score regional integrado com potencial e setor")
    parser.add_argument("--uf", default="MG", help="UF para calcular score. Padrão: MG")
    parser.add_argument("--salvar", action="store_true", help="Salvar no banco")
    args = parser.parse_args()

    df = calcular_scores(uf=args.uf)

    print("\nScores calculados:")
    print(df[[
        "uf",
        "regiao_comercial",
        "score_potencial",
        "score_setorial",
        "score_competitividade_setorial",
        "score_pressao_custo_setorial",
        "score_risco_substituicao_setorial",
        "score_oportunidade",
        "score_risco",
        "score_final",
        "cenario_1_10",
        "confianca",
    ]].to_string(index=False))

    if args.salvar:
        qtd = salvar_scores(df)
        print(f"\n✅ Scores salvos/atualizados: {qtd}")


if __name__ == "__main__":
    main()
