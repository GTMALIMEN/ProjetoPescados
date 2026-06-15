import pandas as pd
from sqlalchemy import text
from src.database.connection import get_engine


def carregar_recomendacoes_atuais(uf: str | None = "MG") -> pd.DataFrame:
    engine = get_engine()
    if uf:
        sql = """
            SELECT id, id_score, data_referencia, uf, regiao_comercial, municipio,
                   produto, proteina, cenario_1_10, tipo_recomendacao, acao_sugerida,
                   justificativa, confianca, impacto_estimado, roi_estimado,
                   score_vendedor, score_promotor, score_campanha, score_potencial,
                   score_setorial, score_competitividade_setorial, score_pressao_custo_setorial,
                   score_risco_substituicao_setorial, motor_decisao, status, data_criacao
            FROM app.mv_recomendacao_atual
            WHERE uf = :uf
            ORDER BY cenario_1_10 DESC, score_potencial DESC, confianca DESC, regiao_comercial
        """
        params = {"uf": uf}
    else:
        sql = """
            SELECT id, id_score, data_referencia, uf, regiao_comercial, municipio,
                   produto, proteina, cenario_1_10, tipo_recomendacao, acao_sugerida,
                   justificativa, confianca, impacto_estimado, roi_estimado,
                   score_vendedor, score_promotor, score_campanha, score_potencial,
                   score_setorial, score_competitividade_setorial, score_pressao_custo_setorial,
                   score_risco_substituicao_setorial, motor_decisao, status, data_criacao
            FROM app.mv_recomendacao_atual
            ORDER BY cenario_1_10 DESC, score_potencial DESC, confianca DESC, uf, regiao_comercial
        """
        params = {}
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params=params)


def resumo_recomendacoes(uf: str = "MG") -> dict:
    engine = get_engine()
    sql = """
        SELECT
            COUNT(*) AS qtd_recomendacoes,
            AVG(confianca) AS confianca_media,
            AVG(cenario_1_10) AS cenario_medio,
            AVG(score_potencial) AS potencial_medio,
            AVG(score_setorial) AS setorial_medio,
            AVG(score_competitividade_setorial) AS competitividade_media,
            AVG(score_pressao_custo_setorial) AS pressao_custo_media,
            AVG(score_risco_substituicao_setorial) AS substituicao_media,
            COUNT(*) FILTER (WHERE tipo_recomendacao = 'adicionar_vendedor') AS qtd_vendedor,
            COUNT(*) FILTER (WHERE tipo_recomendacao = 'adicionar_promotor') AS qtd_promotor,
            COUNT(*) FILTER (WHERE tipo_recomendacao = 'campanha_marketing') AS qtd_campanha,
            COUNT(*) FILTER (WHERE tipo_recomendacao = 'monitorar') AS qtd_monitorar,
            COUNT(*) FILTER (WHERE tipo_recomendacao = 'corrigir_mix_preco') AS qtd_corrigir,
            COUNT(*) FILTER (WHERE tipo_recomendacao = 'aguardar_dados_reais') AS qtd_aguardar
        FROM app.mv_recomendacao_atual
        WHERE uf = :uf
    """
    with engine.begin() as conn:
        row = conn.execute(text(sql), {"uf": uf}).mappings().first()
    return dict(row or {})


def recomendacoes_por_tipo(uf: str = "MG") -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            tipo_recomendacao,
            motor_decisao,
            COUNT(*) AS qtd,
            AVG(confianca) AS confianca_media,
            AVG(cenario_1_10) AS cenario_medio,
            AVG(score_potencial) AS potencial_medio,
            AVG(score_setorial) AS setorial_medio
        FROM app.mv_recomendacao_atual
        WHERE uf = :uf
        GROUP BY tipo_recomendacao, motor_decisao
        ORDER BY qtd DESC, tipo_recomendacao, motor_decisao
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"uf": uf})


def recomendacoes_por_regiao(uf: str = "MG") -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT regiao_comercial, tipo_recomendacao, motor_decisao, cenario_1_10, confianca,
               score_vendedor, score_promotor, score_campanha, score_potencial,
               score_setorial, score_competitividade_setorial, score_pressao_custo_setorial,
               score_risco_substituicao_setorial, roi_estimado
        FROM app.mv_recomendacao_atual
        WHERE uf = :uf
        ORDER BY cenario_1_10 DESC, score_potencial DESC, confianca DESC, regiao_comercial
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"uf": uf})
