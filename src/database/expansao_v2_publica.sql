
-- ============================================================
-- Radar Pescados IA V2 — Expansão pública / IBGE / bases de mercado
-- Versão corrigida: sem zeros falsos e com chaves robustas.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS dw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS app.fato_expansao_municipio (
    codigo_ibge TEXT PRIMARY KEY,
    uf TEXT,
    nome_uf TEXT,
    municipio TEXT,
    mesorregiao TEXT,
    microrregiao TEXT,
    regiao_comercial TEXT,

    populacao NUMERIC,
    pib NUMERIC,
    pib_per_capita NUMERIC,
    idh NUMERIC,
    renda_media NUMERIC,

    pct_masculina NUMERIC,
    pct_feminina NUMERIC,
    pct_0_14 NUMERIC,
    pct_15_29 NUMERIC,
    pct_30_44 NUMERIC,
    pct_45_59 NUMERIC,
    pct_60_plus NUMERIC,

    renda_classe_a NUMERIC,
    renda_classe_b NUMERIC,
    renda_classe_c NUMERIC,
    renda_classe_de NUMERIC,

    supermercados NUMERIC,
    restaurantes NUMERIC,
    peixarias NUMERIC,
    outros_pdv NUMERIC,

    fonte_populacao TEXT,
    fonte_pib TEXT,
    fonte_idh TEXT,
    fonte_renda TEXT,
    fonte_demografia TEXT,
    fonte_pdv TEXT,

    status_dados TEXT DEFAULT 'parcial',
    observacao TEXT,
    data_atualizacao TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fato_expansao_municipio_uf
ON app.fato_expansao_municipio (uf, microrregiao);

CREATE INDEX IF NOT EXISTS idx_fato_expansao_municipio_regiao
ON app.fato_expansao_municipio (uf, regiao_comercial);

CREATE OR REPLACE VIEW app.vw_expansao_municipio AS
SELECT
    COALESCE(e.codigo_ibge, g.codigo_ibge) AS codigo_ibge,
    COALESCE(e.uf, g.uf) AS uf,
    COALESCE(e.nome_uf, g.nome_uf) AS nome_uf,
    COALESCE(e.municipio, g.municipio) AS municipio,
    COALESCE(e.mesorregiao, g.mesorregiao) AS mesorregiao,
    COALESCE(e.microrregiao, g.microrregiao) AS microrregiao,
    COALESCE(e.regiao_comercial, g.regiao_comercial) AS regiao_comercial,

    e.populacao,
    e.pib,
    e.pib_per_capita,
    e.idh,
    e.renda_media,

    e.pct_masculina,
    e.pct_feminina,
    e.pct_0_14,
    e.pct_15_29,
    e.pct_30_44,
    e.pct_45_59,
    e.pct_60_plus,

    e.renda_classe_a,
    e.renda_classe_b,
    e.renda_classe_c,
    e.renda_classe_de,

    e.supermercados,
    e.restaurantes,
    e.peixarias,
    e.outros_pdv,

    e.fonte_populacao,
    e.fonte_pib,
    e.fonte_idh,
    e.fonte_renda,
    e.fonte_demografia,
    e.fonte_pdv,

    e.status_dados,
    e.observacao,
    e.data_atualizacao
FROM dw.dim_geografia g
LEFT JOIN app.fato_expansao_municipio e
    ON e.codigo_ibge = g.codigo_ibge;

CREATE TABLE IF NOT EXISTS app.fato_ceagesp_pescados (
    id BIGSERIAL PRIMARY KEY,
    chave_registro TEXT UNIQUE,
    data_coleta TIMESTAMP DEFAULT NOW(),
    data_referencia DATE,
    categoria TEXT DEFAULT 'Pescados',
    produto TEXT,
    classificacao TEXT,
    unidade TEXT,
    preco_minimo NUMERIC,
    preco_comum NUMERIC,
    preco_maximo NUMERIC,
    fonte TEXT DEFAULT 'CEAGESP',
    url_fonte TEXT,
    hash_carga TEXT,
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ceagesp_pescados_data_produto
ON app.fato_ceagesp_pescados (data_referencia DESC, produto);

CREATE TABLE IF NOT EXISTS app.fato_compra_manual (
    id BIGSERIAL PRIMARY KEY,
    data DATE,
    mes DATE,
    fornecedor TEXT,
    marca TEXT,
    produto TEXT,
    categoria TEXT,
    preco_compra NUMERIC,
    quantidade_comprada NUMERIC,
    unidade TEXT,
    observacao TEXT,
    data_carga TIMESTAMP DEFAULT NOW(),
    fonte_arquivo TEXT,
    hash_linha TEXT UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_compra_manual_produto_data
ON app.fato_compra_manual (produto, data);

CREATE TABLE IF NOT EXISTS app.fato_previa_vendedores (
    id BIGSERIAL PRIMARY KEY,
    vendedor TEXT,
    produto TEXT,
    preco NUMERIC,
    data_venda DATE,
    quantidade_vendida NUMERIC,
    receita_total NUMERIC,
    cliente TEXT,
    regiao TEXT,
    observacao TEXT,
    data_carga TIMESTAMP DEFAULT NOW(),
    fonte TEXT DEFAULT 'manual',
    hash_linha TEXT UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_previa_vendedores_produto_data
ON app.fato_previa_vendedores (produto, data_venda);

CREATE OR REPLACE VIEW app.vw_diagnostico_v2_plano AS
SELECT 'expansao_populacao' AS item,
       COUNT(*) FILTER (WHERE populacao IS NOT NULL) AS qtd_preenchida,
       COUNT(*) AS qtd_total,
       CASE WHEN COUNT(*) FILTER (WHERE populacao IS NOT NULL) > 0 THEN 'OK' ELSE 'PENDENTE' END AS status
FROM app.vw_expansao_municipio
WHERE uf IN ('MG','SP','RJ','ES')
UNION ALL
SELECT 'expansao_pib',
       COUNT(*) FILTER (WHERE pib IS NOT NULL),
       COUNT(*),
       CASE WHEN COUNT(*) FILTER (WHERE pib IS NOT NULL) > 0 THEN 'OK' ELSE 'PENDENTE_CARGA_IBGE_SIDRA' END
FROM app.vw_expansao_municipio
WHERE uf IN ('MG','SP','RJ','ES')
UNION ALL
SELECT 'expansao_idh',
       COUNT(*) FILTER (WHERE idh IS NOT NULL),
       COUNT(*),
       CASE WHEN COUNT(*) FILTER (WHERE idh IS NOT NULL) > 0 THEN 'OK' ELSE 'PENDENTE_FONTE_EXTERNA' END
FROM app.vw_expansao_municipio
WHERE uf IN ('MG','SP','RJ','ES')
UNION ALL
SELECT 'expansao_demografia_censo',
       COUNT(*) FILTER (WHERE pct_masculina IS NOT NULL OR pct_feminina IS NOT NULL),
       COUNT(*),
       CASE WHEN COUNT(*) FILTER (WHERE pct_masculina IS NOT NULL OR pct_feminina IS NOT NULL) > 0 THEN 'OK' ELSE 'PENDENTE_CENSO_DEMOGRAFIA' END
FROM app.vw_expansao_municipio
WHERE uf IN ('MG','SP','RJ','ES')
UNION ALL
SELECT 'expansao_pdv',
       COUNT(*) FILTER (WHERE supermercados IS NOT NULL OR restaurantes IS NOT NULL OR peixarias IS NOT NULL),
       COUNT(*),
       CASE WHEN COUNT(*) FILTER (WHERE supermercados IS NOT NULL OR restaurantes IS NOT NULL OR peixarias IS NOT NULL) > 0 THEN 'OK' ELSE 'PENDENTE_BASE_PDV' END
FROM app.vw_expansao_municipio
WHERE uf IN ('MG','SP','RJ','ES')
UNION ALL
SELECT 'ceagesp_pescados',
       COUNT(*),
       COUNT(*),
       CASE WHEN COUNT(*) > 0 THEN 'OK' ELSE 'PENDENTE_CARGA' END
FROM app.fato_ceagesp_pescados
UNION ALL
SELECT 'base_compra_manual',
       COUNT(*),
       COUNT(*),
       CASE WHEN COUNT(*) > 0 THEN 'OK' ELSE 'PENDENTE_IMPORTACAO' END
FROM app.fato_compra_manual
UNION ALL
SELECT 'previa_vendedores',
       COUNT(*),
       COUNT(*),
       CASE WHEN COUNT(*) > 0 THEN 'OK' ELSE 'PENDENTE_IMPORTACAO' END
FROM app.fato_previa_vendedores;
