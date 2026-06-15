import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


def carregar_scores_atuais(uf: str | None = "MG") -> pd.DataFrame:
    engine = get_engine()

    if uf:
        sql = """
            SELECT
                data_referencia,
                uf,
                regiao_comercial,
                municipio,
                produto,
                proteina,
                score_oportunidade,
                score_risco,
                score_pressao_custo,
                score_competitividade,
                score_potencial,
                score_setorial,
                score_competitividade_setorial,
                score_pressao_custo_setorial,
                score_risco_substituicao_setorial,
                score_final,
                cenario_1_10,
                confianca,
                metodo,
                data_calculo
            FROM app.mv_score_regional_atual
            WHERE uf = :uf
            ORDER BY score_final DESC
        """
        params = {"uf": uf}
    else:
        sql = """
            SELECT
                data_referencia,
                uf,
                regiao_comercial,
                municipio,
                produto,
                proteina,
                score_oportunidade,
                score_risco,
                score_pressao_custo,
                score_competitividade,
                score_potencial,
                score_setorial,
                score_competitividade_setorial,
                score_pressao_custo_setorial,
                score_risco_substituicao_setorial,
                score_final,
                cenario_1_10,
                confianca,
                metodo,
                data_calculo
            FROM app.mv_score_regional_atual
            ORDER BY score_final DESC
        """
        params = {}

    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params=params)


def resumo_scores(uf: str = "MG") -> dict:
    engine = get_engine()

    sql = """
        SELECT
            COUNT(*) AS qtd_regioes,
            AVG(score_final) AS score_medio,
            AVG(score_oportunidade) AS oportunidade_media,
            AVG(score_risco) AS risco_medio,
            AVG(score_potencial) AS potencial_medio,
            AVG(score_setorial) AS setorial_medio,
            AVG(score_competitividade_setorial) AS competitividade_media,
            AVG(score_pressao_custo_setorial) AS pressao_custo_media,
            AVG(score_risco_substituicao_setorial) AS substituicao_media,
            AVG(confianca) AS confianca_media,
            MAX(cenario_1_10) AS melhor_cenario,
            MIN(cenario_1_10) AS pior_cenario
        FROM app.mv_score_regional_atual
        WHERE uf = :uf
    """

    with engine.begin() as conn:
        row = conn.execute(text(sql), {"uf": uf}).mappings().first()

    return dict(row or {})
