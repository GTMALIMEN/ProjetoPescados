CREATE INDEX IF NOT EXISTS idx_serie_data
ON dw.fato_serie_historica (data);

CREATE INDEX IF NOT EXISTS idx_serie_fonte_indicador_data
ON dw.fato_serie_historica (fonte, indicador, data);

CREATE INDEX IF NOT EXISTS idx_serie_geo
ON dw.fato_serie_historica (pais, uf, municipio, regiao_comercial);

CREATE INDEX IF NOT EXISTS idx_vendas_data
ON dw.fato_vendas (data);

CREATE INDEX IF NOT EXISTS idx_vendas_geo
ON dw.fato_vendas (uf, municipio, regiao_comercial);

CREATE INDEX IF NOT EXISTS idx_vendas_produto
ON dw.fato_vendas (id_produto);

CREATE INDEX IF NOT EXISTS idx_vendas_cliente
ON dw.fato_vendas (id_cliente);

CREATE INDEX IF NOT EXISTS idx_vendas_vendedor
ON dw.fato_vendas (id_vendedor);
