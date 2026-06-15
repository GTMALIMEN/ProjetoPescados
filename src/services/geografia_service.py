import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


def listar_ufs() -> list[str]:
    engine = get_engine()

    sql = """
        SELECT DISTINCT uf
        FROM dw.dim_geografia
        WHERE uf IS NOT NULL
        ORDER BY uf
    """

    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn)

    return df["uf"].dropna().tolist()


def listar_regioes_comerciais(uf: str | None = None) -> list[str]:
    engine = get_engine()

    if uf:
        sql = """
            SELECT DISTINCT regiao_comercial
            FROM dw.dim_geografia
            WHERE uf = :uf
              AND regiao_comercial IS NOT NULL
            ORDER BY regiao_comercial
        """
        params = {"uf": uf}
    else:
        sql = """
            SELECT DISTINCT regiao_comercial
            FROM dw.dim_geografia
            WHERE regiao_comercial IS NOT NULL
            ORDER BY regiao_comercial
        """
        params = {}

    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params=params)

    return df["regiao_comercial"].dropna().tolist()


def carregar_municipios(uf: str | None = None, regiao_comercial: str | None = None) -> pd.DataFrame:
    engine = get_engine()

    filtros = []
    params = {}

    if uf:
        filtros.append("uf = :uf")
        params["uf"] = uf

    if regiao_comercial:
        filtros.append("regiao_comercial = :regiao_comercial")
        params["regiao_comercial"] = regiao_comercial

    where_clause = ""
    if filtros:
        where_clause = "WHERE " + " AND ".join(filtros)

    sql = f"""
        SELECT
            codigo_ibge,
            uf,
            nome_uf,
            municipio,
            regiao_brasil,
            sigla_regiao_brasil,
            mesorregiao,
            microrregiao,
            regiao_comercial,
            fonte,
            data_atualizacao
        FROM dw.dim_geografia
        {where_clause}
        ORDER BY uf, regiao_comercial, municipio
    """

    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params=params)

    return df


def resumo_geografia() -> pd.DataFrame:
    engine = get_engine()

    sql = """
        SELECT
            uf,
            nome_uf,
            regiao_brasil,
            COUNT(*) AS qtd_municipios
        FROM dw.dim_geografia
        GROUP BY uf, nome_uf, regiao_brasil
        ORDER BY uf
    """

    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn)

    return df


def resumo_regiao_comercial(uf: str | None = None) -> pd.DataFrame:
    engine = get_engine()

    if uf:
        sql = """
            SELECT
                uf,
                regiao_comercial,
                COUNT(*) AS qtd_municipios
            FROM dw.dim_geografia
            WHERE uf = :uf
              AND regiao_comercial IS NOT NULL
            GROUP BY uf, regiao_comercial
            ORDER BY qtd_municipios DESC, regiao_comercial
        """
        params = {"uf": uf}
    else:
        sql = """
            SELECT
                uf,
                regiao_comercial,
                COUNT(*) AS qtd_municipios
            FROM dw.dim_geografia
            WHERE regiao_comercial IS NOT NULL
            GROUP BY uf, regiao_comercial
            ORDER BY uf, qtd_municipios DESC, regiao_comercial
        """
        params = {}

    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params=params)

    return df
