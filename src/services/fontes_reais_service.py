import pandas as pd
from sqlalchemy import text
from src.database.connection import get_engine


def carregar_fontes_reais_resumo() -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            fonte,
            qtd_registros,
            qtd_indicadores,
            qtd_produtos,
            primeira_data,
            ultima_data
        FROM app.vw_fontes_reais_setoriais
        ORDER BY fonte
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn)


def carregar_fontes_reais_cargas(limit: int = 50) -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            fonte,
            origem,
            status,
            registros_lidos,
            registros_dw,
            detalhe,
            data_execucao
        FROM app.vw_fontes_reais_ultimas_cargas
        LIMIT :limit
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"limit": limit})


def carregar_comex_series() -> pd.DataFrame:
    """
    Consulta diretamente a fato para evitar erro caso a view mensal antiga ainda
    não tenha sido recriada com a coluna fonte.
    """
    engine = get_engine()
    sql = """
        SELECT
            DATE_TRUNC('month', data)::DATE AS mes,
            produto,
            indicador,
            unidade,
            AVG(valor) AS valor_medio
        FROM dw.fato_indicador_setorial
        WHERE fonte = 'Comex Stat'
           OR indicador LIKE 'importacao_%'
           OR indicador LIKE 'preco_medio_importacao_%'
        GROUP BY
            DATE_TRUNC('month', data)::DATE,
            produto,
            indicador,
            unidade
        ORDER BY mes, produto, indicador
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn)


def carregar_config_ncm() -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            grupo_pescado,
            ncm,
            descricao,
            ativo
        FROM app.config_ncm_pescado
        ORDER BY grupo_pescado, ncm
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn)



def _safe_view(view_name: str, fallback_sql: str) -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        exists = conn.execute(text("SELECT to_regclass(:name) IS NOT NULL"), {"name": view_name}).scalar()
        if not exists:
            return pd.DataFrame()
        return pd.read_sql(text(fallback_sql), conn)


def carregar_comex_status_atual() -> pd.DataFrame:
    return _safe_view(
        "app.vw_comex_stat_status_atual",
        "SELECT * FROM app.vw_comex_stat_status_atual"
    )


def carregar_fontes_reais_cargas_sucesso(limit: int = 20) -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        exists = conn.execute(text("SELECT to_regclass('app.vw_fontes_reais_cargas_sucesso') IS NOT NULL")).scalar()
        if not exists:
            return pd.DataFrame()
        return pd.read_sql(
            text("SELECT * FROM app.vw_fontes_reais_cargas_sucesso LIMIT :limit"),
            conn,
            params={"limit": limit},
        )


def carregar_fontes_reais_cargas_erro(limit: int = 20) -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        exists = conn.execute(text("SELECT to_regclass('app.vw_fontes_reais_cargas_erro') IS NOT NULL")).scalar()
        if not exists:
            return pd.DataFrame()
        return pd.read_sql(
            text("SELECT * FROM app.vw_fontes_reais_cargas_erro LIMIT :limit"),
            conn,
            params={"limit": limit},
        )
