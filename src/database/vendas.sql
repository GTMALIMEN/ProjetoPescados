-- ============================================================
-- Radar Pescados IA — Etapa 4
-- Carga de Vendas Internas
-- ============================================================

CREATE TABLE IF NOT EXISTS staging.vendas_internas (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID REFERENCES app.etl_run(run_id),
    arquivo_origem TEXT,
    linha_origem INT,
    codigo_origem TEXT,
    numero_documento TEXT,
    numero_item TEXT,
    numero_pedido TEXT,
    data DATE,
    codigo_cliente TEXT,
    cliente TEXT,
    grupo_cliente TEXT,
    perfil_cliente TEXT,
    cpf_cnpj_hash TEXT,
    uf TEXT,
    municipio TEXT,
    codigo_ibge TEXT,
    regiao_comercial TEXT,
    codigo_produto TEXT,
    produto TEXT,
    grupo_produto TEXT,
    proteina TEXT,
    categoria TEXT,
    origem_produto TEXT,
    codigo_vendedor TEXT,
    vendedor TEXT,
    canal TEXT,
    valor_venda NUMERIC,
    volume_kg NUMERIC,
    quantidade NUMERIC,
    chave_venda_hash TEXT,
    processado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_staging_vendas_run
ON staging.vendas_internas (run_id);

CREATE INDEX IF NOT EXISTS idx_staging_vendas_hash
ON staging.vendas_internas (chave_venda_hash);

CREATE INDEX IF NOT EXISTS idx_staging_vendas_geo
ON staging.vendas_internas (uf, municipio, regiao_comercial);

-- Ajustes seguros na fato para rastreabilidade da carga
ALTER TABLE dw.fato_vendas
    ADD COLUMN IF NOT EXISTS arquivo_origem TEXT,
    ADD COLUMN IF NOT EXISTS linha_origem INT,
    ADD COLUMN IF NOT EXISTS chave_venda_hash TEXT;

-- Corrige compatibilidade com ON CONFLICT (chave_venda_hash).
-- A versão anterior usava índice parcial com WHERE chave_venda_hash IS NOT NULL,
-- e o PostgreSQL não inferia esse índice no ON CONFLICT simples.
DROP INDEX IF EXISTS dw.uq_fato_vendas_hash_text;
DROP INDEX IF EXISTS uq_fato_vendas_hash_text;

CREATE UNIQUE INDEX IF NOT EXISTS uq_fato_vendas_hash_text
ON dw.fato_vendas (chave_venda_hash);

-- Materialized view corrigida/recriada depois da carga
DROP MATERIALIZED VIEW IF EXISTS app.mv_vendas_mensal_geo;

CREATE MATERIALIZED VIEW app.mv_vendas_mensal_geo AS
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
ON app.mv_vendas_mensal_geo (
    mes,
    COALESCE(uf, ''),
    COALESCE(regiao_comercial, ''),
    COALESCE(municipio, ''),
    COALESCE(id_produto::TEXT, '')
);
