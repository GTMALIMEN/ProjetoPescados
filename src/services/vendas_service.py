import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


def resumo_vendas() -> dict:
    engine = get_engine()

    sql = """
        SELECT
            COALESCE(SUM(valor_venda), 0) AS faturamento,
            COALESCE(SUM(volume_kg), 0) AS volume_kg,
            COALESCE(SUM(quantidade), 0) AS quantidade,
            COUNT(*) AS linhas,
            COUNT(DISTINCT id_cliente) AS clientes,
            COUNT(DISTINCT id_produto) AS produtos,
            COUNT(DISTINCT id_vendedor) AS vendedores
        FROM dw.fato_vendas
    """

    with engine.begin() as conn:
        row = conn.execute(text(sql)).mappings().first()

    return dict(row or {})


def vendas_mensais() -> pd.DataFrame:
    engine = get_engine()

    sql = """
        SELECT
            mes,
            SUM(valor_venda) AS valor_venda,
            SUM(volume_kg) AS volume_kg,
            SUM(quantidade) AS quantidade,
            SUM(qtd_clientes) AS qtd_clientes
        FROM app.mv_vendas_mensal_geo
        GROUP BY mes
        ORDER BY mes
    """

    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn)

    return df


def vendas_por_regiao_mg() -> pd.DataFrame:
    engine = get_engine()

    sql = """
        SELECT
            COALESCE(regiao_comercial, 'Sem região') AS regiao_comercial,
            SUM(valor_venda) AS valor_venda,
            SUM(volume_kg) AS volume_kg,
            COUNT(DISTINCT id_cliente) AS qtd_clientes
        FROM dw.fato_vendas
        WHERE uf = 'MG'
        GROUP BY COALESCE(regiao_comercial, 'Sem região')
        ORDER BY valor_venda DESC
    """

    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn)

    return df


def vendas_por_produto(limit: int = 20) -> pd.DataFrame:
    engine = get_engine()

    sql = """
        SELECT
            dp.produto,
            dp.proteina,
            SUM(fv.valor_venda) AS valor_venda,
            SUM(fv.volume_kg) AS volume_kg
        FROM dw.fato_vendas fv
        LEFT JOIN dw.dim_produto dp ON fv.id_produto = dp.id_produto
        GROUP BY dp.produto, dp.proteina
        ORDER BY valor_venda DESC
        LIMIT :limit
    """

    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params={"limit": limit})

    return df


def vendas_por_vendedor() -> pd.DataFrame:
    engine = get_engine()

    sql = """
        SELECT
            COALESCE(dv.vendedor, 'Sem vendedor') AS vendedor,
            SUM(fv.valor_venda) AS valor_venda,
            SUM(fv.volume_kg) AS volume_kg,
            COUNT(DISTINCT fv.id_cliente) AS qtd_clientes
        FROM dw.fato_vendas fv
        LEFT JOIN dw.dim_vendedor dv ON fv.id_vendedor = dv.id_vendedor
        GROUP BY COALESCE(dv.vendedor, 'Sem vendedor')
        ORDER BY valor_venda DESC
    """

    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn)

    return df
