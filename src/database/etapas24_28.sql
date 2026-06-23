
-- ============================================================
-- Radar Pescados IA — Etapas 24 a 28
-- 24 Censo/Demografia/Renda
-- 25 PDV Proxy
-- 26 Comex refinado
-- 27 Base de compra manual
-- 28 Prévia vendedores
-- ============================================================

CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS dw;
CREATE SCHEMA IF NOT EXISTS raw;

-- Campos de expansão já existiam em versões anteriores, mas ficam aqui
-- para garantir compatibilidade com bancos antigos.
ALTER TABLE app.fato_expansao_municipio
    ADD COLUMN IF NOT EXISTS pct_masculina NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_feminina NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_0_14 NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_15_29 NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_30_44 NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_45_59 NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_60_plus NUMERIC,
    ADD COLUMN IF NOT EXISTS renda_media NUMERIC,
    ADD COLUMN IF NOT EXISTS renda_classe_a NUMERIC,
    ADD COLUMN IF NOT EXISTS renda_classe_b NUMERIC,
    ADD COLUMN IF NOT EXISTS renda_classe_c NUMERIC,
    ADD COLUMN IF NOT EXISTS renda_classe_de NUMERIC,
    ADD COLUMN IF NOT EXISTS supermercados NUMERIC,
    ADD COLUMN IF NOT EXISTS restaurantes NUMERIC,
    ADD COLUMN IF NOT EXISTS peixarias NUMERIC,
    ADD COLUMN IF NOT EXISTS outros_pdv NUMERIC,
    ADD COLUMN IF NOT EXISTS fonte_renda TEXT,
    ADD COLUMN IF NOT EXISTS fonte_demografia TEXT,
    ADD COLUMN IF NOT EXISTS fonte_pdv TEXT;

CREATE TABLE IF NOT EXISTS app.fato_demografia_renda_municipio (
    codigo_ibge TEXT PRIMARY KEY,
    uf TEXT,
    municipio TEXT,
    ano INTEGER DEFAULT 2022,

    populacao NUMERIC,
    pct_masculina NUMERIC,
    pct_feminina NUMERIC,
    pct_0_14 NUMERIC,
    pct_15_29 NUMERIC,
    pct_30_44 NUMERIC,
    pct_45_59 NUMERIC,
    pct_60_plus NUMERIC,

    renda_media NUMERIC,
    renda_classe_a NUMERIC,
    renda_classe_b NUMERIC,
    renda_classe_c NUMERIC,
    renda_classe_de NUMERIC,

    fonte_demografia TEXT,
    fonte_renda TEXT,
    metodo TEXT,
    nivel_confianca INTEGER,
    data_atualizacao TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_demografia_renda_uf
ON app.fato_demografia_renda_municipio (uf);

CREATE TABLE IF NOT EXISTS app.fato_pdv_proxy_municipio (
    codigo_ibge TEXT PRIMARY KEY,
    uf TEXT,
    municipio TEXT,
    supermercados NUMERIC,
    restaurantes NUMERIC,
    peixarias NUMERIC,
    outros_pdv NUMERIC,
    fonte_pdv TEXT,
    metodo TEXT,
    nivel_confianca INTEGER,
    payload_json JSONB,
    data_atualizacao TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pdv_proxy_uf
ON app.fato_pdv_proxy_municipio (uf);

DROP VIEW IF EXISTS app.vw_demografia_renda_municipio CASCADE;

CREATE OR REPLACE VIEW app.vw_demografia_renda_municipio AS
SELECT *
FROM app.fato_demografia_renda_municipio
ORDER BY uf, municipio;

DROP VIEW IF EXISTS app.vw_pdv_proxy_municipio CASCADE;

CREATE OR REPLACE VIEW app.vw_pdv_proxy_municipio AS
SELECT *
FROM app.fato_pdv_proxy_municipio
ORDER BY uf, municipio;

DROP VIEW IF EXISTS app.vw_comex_stat_status_atual CASCADE;

CREATE OR REPLACE VIEW app.vw_comex_stat_status_atual AS
WITH ultimo_sucesso AS (
    SELECT *
    FROM app.etl_fonte_real_resumo
    WHERE fonte = 'Comex Stat'
      AND status = 'SUCESSO'
    ORDER BY data_execucao DESC
    LIMIT 1
),
ultimo_erro AS (
    SELECT *
    FROM app.etl_fonte_real_resumo
    WHERE fonte = 'Comex Stat'
      AND status <> 'SUCESSO'
    ORDER BY data_execucao DESC
    LIMIT 1
),
resumo AS (
    SELECT
        'Comex Stat'::TEXT AS fonte,
        COUNT(*)::INT AS qtd_registros_dw,
        COUNT(DISTINCT indicador)::INT AS qtd_indicadores,
        COUNT(DISTINCT produto)::INT AS qtd_produtos,
        MIN(data)::DATE AS primeira_data,
        MAX(data)::DATE AS ultima_data
    FROM dw.fato_indicador_setorial
    WHERE fonte = 'Comex Stat'
       OR indicador LIKE 'importacao_%'
       OR indicador LIKE 'preco_medio_importacao_%'
)
SELECT
    r.fonte,
    CASE
        WHEN r.qtd_registros_dw > 0 THEN 'OK_COM_DADOS'
        WHEN s.status = 'SUCESSO' THEN 'OK_SEM_DADOS'
        WHEN e.status IS NOT NULL THEN 'ERRO_SEM_CARGA_VALIDA'
        ELSE 'SEM_EXECUCAO'
    END AS status_atual,
    r.qtd_registros_dw,
    r.qtd_indicadores,
    r.qtd_produtos,
    r.primeira_data,
    r.ultima_data,
    s.data_execucao AS ultima_carga_sucesso,
    s.registros_lidos AS sucesso_registros_lidos,
    s.registros_dw AS sucesso_registros_dw,
    s.detalhe AS sucesso_detalhe,
    e.data_execucao AS ultimo_erro_data,
    e.status AS ultimo_erro_status,
    e.detalhe AS ultimo_erro_detalhe
FROM resumo r
LEFT JOIN ultimo_sucesso s ON TRUE
LEFT JOIN ultimo_erro e ON TRUE;

DROP VIEW IF EXISTS app.vw_fontes_reais_cargas_sucesso CASCADE;

CREATE OR REPLACE VIEW app.vw_fontes_reais_cargas_sucesso AS
SELECT
    fonte,
    origem,
    status,
    registros_lidos,
    registros_dw,
    detalhe,
    data_execucao
FROM app.etl_fonte_real_resumo
WHERE status = 'SUCESSO'
ORDER BY data_execucao DESC;

DROP VIEW IF EXISTS app.vw_fontes_reais_cargas_erro CASCADE;

CREATE OR REPLACE VIEW app.vw_fontes_reais_cargas_erro AS
SELECT
    fonte,
    origem,
    status,
    registros_lidos,
    registros_dw,
    detalhe,
    data_execucao
FROM app.etl_fonte_real_resumo
WHERE status <> 'SUCESSO'
ORDER BY data_execucao DESC;

DROP VIEW IF EXISTS app.vw_compra_manual_resumo CASCADE;

CREATE OR REPLACE VIEW app.vw_compra_manual_resumo AS
SELECT
    COUNT(*) AS qtd_registros,
    COUNT(DISTINCT produto) AS qtd_produtos,
    COUNT(DISTINCT marca) AS qtd_marcas,
    COUNT(DISTINCT fornecedor) AS qtd_fornecedores,
    MIN(data) AS primeira_data,
    MAX(data) AS ultima_data,
    AVG(preco_compra) AS preco_medio_geral
FROM app.fato_compra_manual;

DROP VIEW IF EXISTS app.vw_previa_vendedores_resumo CASCADE;

CREATE OR REPLACE VIEW app.vw_previa_vendedores_resumo AS
SELECT
    COUNT(*) AS qtd_registros,
    COUNT(DISTINCT vendedor) AS qtd_vendedores,
    COUNT(DISTINCT produto) AS qtd_produtos,
    MIN(data_venda) AS primeira_data,
    MAX(data_venda) AS ultima_data,
    SUM(quantidade_vendida) AS quantidade_total,
    SUM(receita_total) AS receita_total
FROM app.fato_previa_vendedores;

DROP VIEW IF EXISTS app.vw_diagnostico_v2_plano CASCADE;

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
SELECT 'expansao_idh_atlas_brasil',
       COUNT(*) FILTER (WHERE idh IS NOT NULL),
       COUNT(*),
       CASE WHEN COUNT(*) FILTER (WHERE idh IS NOT NULL) = COUNT(*) THEN 'OK' ELSE 'PARCIAL' END
FROM app.vw_expansao_municipio
WHERE uf IN ('MG','SP','RJ','ES')

UNION ALL
SELECT 'expansao_demografia_censo',
       COUNT(*) FILTER (
           WHERE pct_masculina IS NOT NULL
             AND pct_feminina IS NOT NULL
             AND pct_0_14 IS NOT NULL
             AND pct_15_29 IS NOT NULL
             AND pct_30_44 IS NOT NULL
             AND pct_45_59 IS NOT NULL
             AND pct_60_plus IS NOT NULL
       ),
       COUNT(*),
       CASE
           WHEN COUNT(*) FILTER (WHERE pct_masculina IS NOT NULL AND pct_feminina IS NOT NULL) = COUNT(*) THEN 'OK'
           WHEN COUNT(*) FILTER (WHERE pct_masculina IS NOT NULL OR pct_feminina IS NOT NULL) > 0 THEN 'PARCIAL'
           ELSE 'PENDENTE_CENSO_DEMOGRAFIA'
       END
FROM app.vw_expansao_municipio
WHERE uf IN ('MG','SP','RJ','ES')

UNION ALL
SELECT 'expansao_renda_censo',
       COUNT(*) FILTER (WHERE renda_media IS NOT NULL),
       COUNT(*),
       CASE
           WHEN COUNT(*) FILTER (WHERE renda_media IS NOT NULL) = COUNT(*) THEN 'OK'
           WHEN COUNT(*) FILTER (WHERE renda_media IS NOT NULL) > 0 THEN 'PARCIAL'
           ELSE 'PENDENTE_RENDA'
       END
FROM app.vw_expansao_municipio
WHERE uf IN ('MG','SP','RJ','ES')

UNION ALL
SELECT 'expansao_pdv',
       COUNT(*) FILTER (WHERE supermercados IS NOT NULL OR restaurantes IS NOT NULL OR peixarias IS NOT NULL),
       COUNT(*),
       CASE
           WHEN COUNT(*) FILTER (WHERE fonte_pdv ILIKE '%proxy%') > 0 THEN 'OK_PROXY_ESTIMADO'
           WHEN COUNT(*) FILTER (WHERE supermercados IS NOT NULL OR restaurantes IS NOT NULL OR peixarias IS NOT NULL) > 0 THEN 'OK'
           ELSE 'PENDENTE_BASE_PDV'
       END
FROM app.vw_expansao_municipio
WHERE uf IN ('MG','SP','RJ','ES')

UNION ALL
SELECT 'comex_stat_refinado',
       COALESCE(MAX(qtd_registros_dw), 0),
       COALESCE(MAX(qtd_registros_dw), 0),
       COALESCE(MAX(status_atual), 'SEM_EXECUCAO')
FROM app.vw_comex_stat_status_atual

UNION ALL
SELECT 'ceagesp_pescados_manual',
       COUNT(*),
       COUNT(*),
       CASE WHEN COUNT(*) > 0 THEN 'OK' ELSE 'PENDENTE_IMPORTACAO_MANUAL' END
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
