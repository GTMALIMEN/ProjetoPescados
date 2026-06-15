from __future__ import annotations

import argparse
import json
import math

import numpy as np
import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


def _relation_exists(conn, relation_name: str) -> bool:
    return bool(conn.execute(text("SELECT to_regclass(:relation_name) IS NOT NULL"), {"relation_name": relation_name}).scalar())


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


def carregar_base_potencial(uf: str = "MG") -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        if not _relation_exists(conn, "dw.fato_indicador_municipal"):
            raise ValueError(
                "A tabela dw.fato_indicador_municipal ainda não existe. Rode: python scripts\\hotfix_potencial_mv.py"
            )

        pop = pd.read_sql(text("""
            WITH ultima AS (
                SELECT MAX(data_referencia) AS data_ref
                FROM dw.fato_indicador_municipal
                WHERE indicador = 'População residente estimada'
                  AND uf = :uf
            )
            SELECT
                im.data_referencia,
                im.uf,
                COALESCE(g.regiao_comercial, 'Sem região') AS regiao_comercial,
                COUNT(DISTINCT im.codigo_ibge) AS qtd_municipios,
                SUM(im.valor) AS populacao_estimada
            FROM dw.fato_indicador_municipal im
            INNER JOIN ultima u ON im.data_referencia = u.data_ref
            LEFT JOIN dw.dim_geografia g ON im.codigo_ibge = g.codigo_ibge
            WHERE im.indicador = 'População residente estimada'
              AND im.uf = :uf
            GROUP BY im.data_referencia, im.uf, COALESCE(g.regiao_comercial, 'Sem região')
        """), conn, params={"uf": uf})

        vendas = pd.read_sql(text("""
            SELECT
                uf,
                COALESCE(regiao_comercial, 'Sem região') AS regiao_comercial,
                COALESCE(SUM(valor_venda), 0) AS faturamento,
                COALESCE(SUM(volume_kg), 0) AS volume_kg,
                COUNT(DISTINCT id_cliente) AS qtd_clientes,
                COUNT(DISTINCT id_produto) AS qtd_produtos
            FROM dw.fato_vendas
            WHERE uf = :uf
            GROUP BY uf, COALESCE(regiao_comercial, 'Sem região')
        """), conn, params={"uf": uf})

    if pop.empty:
        raise ValueError("Nenhuma população estimada encontrada. Rode: python scripts/run_ibge_populacao.py")

    base = pop.merge(vendas, on=["uf", "regiao_comercial"], how="left")
    for col in ["faturamento", "volume_kg", "qtd_clientes", "qtd_produtos"]:
        base[col] = pd.to_numeric(base[col], errors="coerce").fillna(0)

    base["venda_per_capita"] = np.where(
        base["populacao_estimada"] > 0,
        base["faturamento"] / base["populacao_estimada"],
        0,
    )
    base["clientes_por_100k"] = np.where(
        base["populacao_estimada"] > 0,
        (base["qtd_clientes"] / base["populacao_estimada"]) * 100000,
        0,
    )
    return base


def calcular_potencial_regional(uf: str = "MG") -> pd.DataFrame:
    base = carregar_base_potencial(uf=uf)

    base["score_populacao"] = normalize_series(base["populacao_estimada"], neutral_if_constant=50)
    base["score_baixa_penetracao"] = normalize_series(base["venda_per_capita"], invert=True, neutral_if_constant=80)
    base["score_baixa_cobertura"] = normalize_series(base["clientes_por_100k"], invert=True, neutral_if_constant=80)

    # Potencial = tamanho do mercado + baixa penetração + baixa cobertura.
    base["score_potencial"] = (
        0.40 * base["score_populacao"] +
        0.35 * base["score_baixa_penetracao"] +
        0.25 * base["score_baixa_cobertura"]
    ).apply(clamp)

    base["cenario_1_10"] = base["score_potencial"].apply(scenario_1_10)

    # Confiança: população oficial dá base boa, mas vendas exemplo/pequenas reduzem a confiança comercial.
    base["confianca"] = np.where(
        base["qtd_clientes"] >= 10,
        75,
        np.where(base["qtd_clientes"] > 0, 55, 45)
    )

    fatores = []
    for _, row in base.iterrows():
        fatores.append(json.dumps([
            {
                "fator": "populacao_estimada",
                "descricao": "Tamanho populacional da região comercial",
                "peso": 0.40,
                "direcao": "positiva",
                "impacto": float(row["populacao_estimada"] or 0),
                "unidade": "pessoas",
                "confianca": 90,
            },
            {
                "fator": "venda_per_capita",
                "descricao": "Quanto menor a venda por habitante, maior a oportunidade não explorada",
                "peso": 0.35,
                "direcao": "inversa",
                "impacto": float(row["venda_per_capita"] or 0),
                "unidade": "R$/hab",
                "confianca": int(row["confianca"]),
            },
            {
                "fator": "clientes_por_100k",
                "descricao": "Quanto menor a cobertura de clientes por 100 mil habitantes, maior a oportunidade",
                "peso": 0.25,
                "direcao": "inversa",
                "impacto": float(row["clientes_por_100k"] or 0),
                "unidade": "clientes/100k hab",
                "confianca": int(row["confianca"]),
            },
        ], ensure_ascii=False))

    base["principais_fatores"] = fatores
    return base.sort_values("score_potencial", ascending=False)


def salvar_potencial(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    records = []
    for _, row in df.iterrows():
        records.append({
            "data_referencia": row["data_referencia"],
            "uf": row["uf"],
            "regiao_comercial": row["regiao_comercial"],
            "populacao_estimada": float(row["populacao_estimada"] or 0),
            "qtd_municipios": int(row["qtd_municipios"] or 0),
            "faturamento": float(row["faturamento"] or 0),
            "volume_kg": float(row["volume_kg"] or 0),
            "qtd_clientes": int(row["qtd_clientes"] or 0),
            "qtd_produtos": int(row["qtd_produtos"] or 0),
            "venda_per_capita": float(row["venda_per_capita"] or 0),
            "clientes_por_100k": float(row["clientes_por_100k"] or 0),
            "score_populacao": float(row["score_populacao"]),
            "score_baixa_penetracao": float(row["score_baixa_penetracao"]),
            "score_baixa_cobertura": float(row["score_baixa_cobertura"]),
            "score_potencial": float(row["score_potencial"]),
            "cenario_1_10": int(row["cenario_1_10"]),
            "confianca": float(row["confianca"]),
            "principais_fatores": row["principais_fatores"],
        })

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.fato_potencial_regional (
                data_referencia, uf, regiao_comercial, populacao_estimada,
                qtd_municipios, faturamento, volume_kg, qtd_clientes, qtd_produtos,
                venda_per_capita, clientes_por_100k, score_populacao,
                score_baixa_penetracao, score_baixa_cobertura, score_potencial,
                cenario_1_10, confianca, principais_fatores
            )
            VALUES (
                :data_referencia, :uf, :regiao_comercial, :populacao_estimada,
                :qtd_municipios, :faturamento, :volume_kg, :qtd_clientes, :qtd_produtos,
                :venda_per_capita, :clientes_por_100k, :score_populacao,
                :score_baixa_penetracao, :score_baixa_cobertura, :score_potencial,
                :cenario_1_10, :confianca, CAST(:principais_fatores AS JSONB)
            )
            ON CONFLICT (data_referencia, uf, regiao_comercial)
            DO UPDATE SET
                populacao_estimada = EXCLUDED.populacao_estimada,
                qtd_municipios = EXCLUDED.qtd_municipios,
                faturamento = EXCLUDED.faturamento,
                volume_kg = EXCLUDED.volume_kg,
                qtd_clientes = EXCLUDED.qtd_clientes,
                qtd_produtos = EXCLUDED.qtd_produtos,
                venda_per_capita = EXCLUDED.venda_per_capita,
                clientes_por_100k = EXCLUDED.clientes_por_100k,
                score_populacao = EXCLUDED.score_populacao,
                score_baixa_penetracao = EXCLUDED.score_baixa_penetracao,
                score_baixa_cobertura = EXCLUDED.score_baixa_cobertura,
                score_potencial = EXCLUDED.score_potencial,
                cenario_1_10 = EXCLUDED.cenario_1_10,
                confianca = EXCLUDED.confianca,
                principais_fatores = EXCLUDED.principais_fatores,
                data_calculo = NOW();
        """), records)
        conn.execute(text("REFRESH MATERIALIZED VIEW app.mv_potencial_regional_atual"))
    return len(records)


def main():
    parser = argparse.ArgumentParser(description="Calcular potencial regional")
    parser.add_argument("--uf", default="MG")
    parser.add_argument("--salvar", action="store_true")
    args = parser.parse_args()

    df = calcular_potencial_regional(uf=args.uf)
    print("\nPotencial regional calculado:")
    print(df[[
        "uf", "regiao_comercial", "populacao_estimada", "faturamento",
        "venda_per_capita", "score_potencial", "cenario_1_10", "confianca"
    ]].to_string(index=False))

    if args.salvar:
        qtd = salvar_potencial(df)
        print(f"\n✅ Potenciais salvos/atualizados: {qtd}")


if __name__ == "__main__":
    main()
