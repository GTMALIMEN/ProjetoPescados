import pandas as pd
from sqlalchemy import text
from src.database.connection import get_engine


def _relation_exists(conn, relation_name: str) -> bool:
    return bool(conn.execute(text("SELECT to_regclass(:relation_name) IS NOT NULL"), {"relation_name": relation_name}).scalar())


def carregar_potencial_atual(uf: str = "MG") -> pd.DataFrame:
    engine = get_engine()

    sql = """
        SELECT
            data_referencia,
            uf,
            regiao_comercial,
            populacao_estimada,
            qtd_municipios,
            faturamento,
            volume_kg,
            qtd_clientes,
            qtd_produtos,
            venda_per_capita,
            clientes_por_100k,
            score_populacao,
            score_baixa_penetracao,
            score_baixa_cobertura,
            score_potencial,
            cenario_1_10,
            confianca,
            data_calculo
        FROM app.mv_potencial_regional_atual
        WHERE uf = :uf
        ORDER BY score_potencial DESC
    """

    with engine.begin() as conn:
        if not _relation_exists(conn, "app.mv_potencial_regional_atual"):
            return pd.DataFrame()
        return pd.read_sql(text(sql), conn, params={"uf": uf})


def resumo_potencial(uf: str = "MG") -> dict:
    engine = get_engine()

    sql = """
        SELECT
            COUNT(*) AS qtd_regioes,
            SUM(populacao_estimada) AS populacao_total,
            SUM(faturamento) AS faturamento_total,
            AVG(score_potencial) AS score_medio,
            AVG(confianca) AS confianca_media,
            MAX(cenario_1_10) AS melhor_cenario
        FROM app.mv_potencial_regional_atual
        WHERE uf = :uf
    """

    with engine.begin() as conn:
        if not _relation_exists(conn, "app.mv_potencial_regional_atual"):
            return {
                "qtd_regioes": 0,
                "populacao_total": 0,
                "faturamento_total": 0,
                "score_medio": 0,
                "confianca_media": 0,
                "melhor_cenario": None,
            }
        row = conn.execute(text(sql), {"uf": uf}).mappings().first()

    return dict(row or {})
