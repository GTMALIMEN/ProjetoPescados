import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


def listar_indicadores_disponiveis() -> list[str]:
    engine = get_engine()

    sql = """
        SELECT DISTINCT indicador
        FROM dw.fato_serie_historica
        ORDER BY indicador
    """

    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn)

    return df["indicador"].dropna().tolist()


def carregar_series_dw(indicador: str | None = None) -> pd.DataFrame:
    engine = get_engine()

    if indicador:
        sql = """
            SELECT
                data,
                fonte,
                codigo_serie,
                indicador,
                categoria,
                valor,
                unidade,
                periodicidade
            FROM dw.fato_serie_historica
            WHERE indicador = :indicador
            ORDER BY data
        """
        params = {"indicador": indicador}
    else:
        sql = """
            SELECT
                data,
                fonte,
                codigo_serie,
                indicador,
                categoria,
                valor,
                unidade,
                periodicidade
            FROM dw.fato_serie_historica
            ORDER BY data
        """
        params = {}

    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params=params)

    return df
