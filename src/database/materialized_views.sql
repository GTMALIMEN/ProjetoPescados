-- Materialized views iniciais.
-- A primeira criação pode gerar MV vazia. Depois de carregar vendas/scores,
-- executar REFRESH MATERIALIZED VIEW.

CREATE MATERIALIZED VIEW IF NOT EXISTS app.mv_vendas_mensal_geo AS
SELECT
    DATE_TRUNC('month', data)::DATE AS mes,
    uf,
    regiao_comercial,
    municipio,
    id_produto,
    SUM(valor_venda) AS valor_venda,
    SUM(volume_kg) AS volume_kg,
    SUM(quantidade) AS quantidade,
    COUNT(DISTINCT id_cliente) AS qtd_clientes,
    CASE
        WHEN SUM(volume_kg) = 0 OR SUM(volume_kg) IS NULL THEN NULL
        ELSE SUM(valor_venda) / SUM(volume_kg)
    END AS preco_medio_kg
FROM dw.fato_vendas
GROUP BY
    DATE_TRUNC('month', data)::DATE,
    uf,
    regiao_comercial,
    municipio,
    id_produto;

CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_vendas_mensal_geo
ON app.mv_vendas_mensal_geo (mes, uf, regiao_comercial, municipio, id_produto);
