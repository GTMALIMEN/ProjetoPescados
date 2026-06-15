from sqlalchemy import text
from sqlalchemy.engine import Engine
import pandas as pd


KEY_COLS = [
    "codigo_serie",
    "pais",
    "uf",
    "municipio",
    "regiao_ibge",
    "regiao_comercial",
]


def upsert_fato_serie_historica(engine: Engine, df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    df = df.copy()

    # As colunas da chave natural são NOT NULL DEFAULT '' no banco.
    # Como enviamos valores explicitamente no INSERT, precisamos trocar None/NaN por ''.
    for col in KEY_COLS:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)

    if "pais" in df.columns:
        df["pais"] = df["pais"].replace("", "Brasil")

    registros = df.to_dict(orient="records")

    sql = text("""
        INSERT INTO dw.fato_serie_historica (
            data,
            fonte,
            codigo_serie,
            indicador,
            categoria,
            subcategoria,
            pais,
            uf,
            municipio,
            regiao_ibge,
            regiao_comercial,
            valor,
            unidade,
            periodicidade,
            data_inicio_fonte,
            data_fim_fonte
        )
        VALUES (
            :data,
            :fonte,
            :codigo_serie,
            :indicador,
            :categoria,
            :subcategoria,
            :pais,
            :uf,
            :municipio,
            :regiao_ibge,
            :regiao_comercial,
            :valor,
            :unidade,
            :periodicidade,
            :data_inicio_fonte,
            :data_fim_fonte
        )
        ON CONFLICT (
            data,
            fonte,
            codigo_serie,
            indicador,
            pais,
            uf,
            municipio,
            regiao_ibge,
            regiao_comercial
        )
        DO UPDATE SET
            valor = EXCLUDED.valor,
            unidade = EXCLUDED.unidade,
            periodicidade = EXCLUDED.periodicidade,
            data_inicio_fonte = EXCLUDED.data_inicio_fonte,
            data_fim_fonte = EXCLUDED.data_fim_fonte,
            data_coleta = NOW();
    """)

    with engine.begin() as conn:
        conn.execute(sql, registros)

    return len(registros)
