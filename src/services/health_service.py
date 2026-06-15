import pandas as pd
from sqlalchemy import text
from src.database.connection import get_engine


def _relation_exists(conn, relation_name: str) -> bool:
    return bool(conn.execute(text("SELECT to_regclass(:name) IS NOT NULL"), {"name": relation_name}).scalar())


def carregar_saude_sistema() -> dict:
    engine = get_engine()
    sql = "SELECT * FROM app.vw_saude_sistema"
    with engine.begin() as conn:
        row = conn.execute(text(sql)).mappings().first()
    return dict(row or {})


def carregar_ultimas_execucoes(limit: int = 50) -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            run_id::TEXT AS run_id,
            fonte,
            tipo_execucao,
            ambiente,
            status,
            iniciado_em,
            finalizado_em,
            duracao_segundos,
            mensagem
        FROM app.vw_etl_ultimas_execucoes
        LIMIT :limit
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"limit": limit})


def carregar_resumo_fonte() -> pd.DataFrame:
    """Resumo operacional atual: considera somente a última carga de cada fonte/indicador."""
    engine = get_engine()
    sql = """
        SELECT
            fonte,
            status,
            qtd_execucoes,
            ultima_execucao,
            duracao_media_segundos
        FROM app.vw_etl_resumo_fonte
        ORDER BY fonte, status
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn)


def carregar_resumo_fonte_historico() -> pd.DataFrame:
    """Resumo histórico: mantém erros antigos para auditoria."""
    engine = get_engine()
    sql = """
        SELECT
            fonte,
            status,
            qtd_execucoes,
            ultima_execucao,
            duracao_media_segundos
        FROM app.vw_etl_resumo_fonte_historico
        ORDER BY fonte, status
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn)


def carregar_status_atual(limit: int = 100) -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            id,
            run_id::TEXT AS run_id,
            fonte,
            indicador,
            codigo_serie,
            status,
            mensagem,
            qtd_registros,
            qtd_raw,
            qtd_staging,
            qtd_dw,
            qtd_rejeitados,
            tempo_execucao_segundos,
            data_execucao
        FROM app.vw_etl_status_atual
        LIMIT :limit
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"limit": limit})


def carregar_controle_carga(limit: int = 100) -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            id,
            run_id::TEXT AS run_id,
            fonte,
            indicador,
            codigo_serie,
            status,
            mensagem,
            qtd_registros,
            qtd_raw,
            qtd_staging,
            qtd_dw,
            qtd_rejeitados,
            tempo_execucao_segundos,
            data_execucao
        FROM app.vw_etl_controle_carga
        LIMIT :limit
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"limit": limit})


def carregar_data_quality(limit: int = 100) -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            id,
            run_id::TEXT AS run_id,
            fonte,
            tabela,
            regra,
            status,
            qtd_linhas_afetadas,
            detalhe,
            data_validacao
        FROM app.data_quality_resultado
        ORDER BY data_validacao DESC
        LIMIT :limit
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"limit": limit})


def carregar_data_quality_resumo() -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            fonte,
            tabela,
            regra,
            status,
            qtd_validacoes,
            linhas_afetadas,
            ultima_validacao
        FROM app.vw_data_quality_resumo
        ORDER BY ultima_validacao DESC
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn)


def carregar_erros_recentes(limit: int = 50) -> pd.DataFrame:
    """Erros ativos: somente itens cujo último status ainda é erro."""
    engine = get_engine()
    sql = """
        SELECT
            run_id::TEXT AS run_id,
            fonte,
            indicador,
            codigo_serie,
            status,
            mensagem,
            qtd_raw,
            qtd_staging,
            qtd_dw,
            qtd_rejeitados,
            tempo_execucao_segundos,
            data_execucao
        FROM app.vw_etl_erros_ativos
        LIMIT :limit
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"limit": limit})


def carregar_erros_historicos(limit: int = 50) -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            run_id::TEXT AS run_id,
            fonte,
            tipo_execucao,
            ambiente,
            status,
            iniciado_em,
            finalizado_em,
            mensagem
        FROM app.vw_etl_ultimas_execucoes
        WHERE status <> 'SUCESSO'
        ORDER BY iniciado_em DESC
        LIMIT :limit
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"limit": limit})


def carregar_tamanhos_tabelas() -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            schemaname AS schema,
            relname AS tabela,
            n_live_tup AS linhas_estimadas,
            n_dead_tup AS linhas_mortas,
            last_vacuum,
            last_autovacuum,
            last_analyze,
            last_autoanalyze
        FROM pg_stat_user_tables
        WHERE schemaname IN ('raw', 'staging', 'dw', 'app', 'ml')
        ORDER BY schemaname, relname
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn)
