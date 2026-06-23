
CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS raw;
CREATE TABLE IF NOT EXISTS raw.fonte_automatica_payload (id BIGSERIAL PRIMARY KEY, fonte TEXT NOT NULL, endpoint TEXT, status TEXT, detalhe TEXT, payload_json JSONB, criado_em TIMESTAMP DEFAULT NOW());
CREATE TABLE IF NOT EXISTS app.fato_idhm_municipal (codigo_ibge TEXT PRIMARY KEY, municipio TEXT, uf TEXT, ano INTEGER, idhm NUMERIC, idhm_renda NUMERIC, idhm_longevidade NUMERIC, idhm_educacao NUMERIC, ranking INTEGER, fonte TEXT DEFAULT 'Atlas Brasil / PNUD', url_fonte TEXT, data_carga TIMESTAMP DEFAULT NOW());
CREATE INDEX IF NOT EXISTS idx_fato_idhm_municipal_uf ON app.fato_idhm_municipal (uf, idhm DESC);
ALTER TABLE app.fato_expansao_municipio ADD COLUMN IF NOT EXISTS idhm_ano INTEGER, ADD COLUMN IF NOT EXISTS idhm_renda NUMERIC, ADD COLUMN IF NOT EXISTS idhm_longevidade NUMERIC, ADD COLUMN IF NOT EXISTS idhm_educacao NUMERIC;
ALTER TABLE app.fato_ceagesp_pescados ADD COLUMN IF NOT EXISTS chave_registro TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS uq_fato_ceagesp_pescados_chave ON app.fato_ceagesp_pescados (chave_registro) WHERE chave_registro IS NOT NULL;
CREATE OR REPLACE VIEW app.vw_idhm_municipal AS SELECT codigo_ibge, municipio, uf, ano, idhm, idhm_renda, idhm_longevidade, idhm_educacao, ranking, fonte, url_fonte, data_carga FROM app.fato_idhm_municipal;
DROP VIEW IF EXISTS app.vw_diagnostico_v2_plano CASCADE;

CREATE OR REPLACE VIEW app.vw_diagnostico_v2_plano AS
SELECT 'expansao_populacao' AS item, COUNT(*) FILTER (WHERE populacao IS NOT NULL) AS qtd_preenchida, COUNT(*) AS qtd_total, CASE WHEN COUNT(*) FILTER (WHERE populacao IS NOT NULL)>0 THEN 'OK' ELSE 'PENDENTE' END AS status FROM app.vw_expansao_municipio WHERE uf IN ('MG','SP','RJ','ES')
UNION ALL SELECT 'expansao_pib', COUNT(*) FILTER (WHERE pib IS NOT NULL), COUNT(*), CASE WHEN COUNT(*) FILTER (WHERE pib IS NOT NULL)>0 THEN 'OK' ELSE 'PENDENTE_CARGA_IBGE_SIDRA' END FROM app.vw_expansao_municipio WHERE uf IN ('MG','SP','RJ','ES')
UNION ALL SELECT 'expansao_idh_atlas_brasil', COUNT(*) FILTER (WHERE idh IS NOT NULL), COUNT(*), CASE WHEN COUNT(*) FILTER (WHERE idh IS NOT NULL)>0 THEN 'OK' ELSE 'PENDENTE_CARGA_AUTOMATICA' END FROM app.vw_expansao_municipio WHERE uf IN ('MG','SP','RJ','ES')
UNION ALL SELECT 'expansao_demografia_censo', COUNT(*) FILTER (WHERE pct_masculina IS NOT NULL OR pct_feminina IS NOT NULL), COUNT(*), CASE WHEN COUNT(*) FILTER (WHERE pct_masculina IS NOT NULL OR pct_feminina IS NOT NULL)>0 THEN 'OK' ELSE 'PENDENTE_CENSO_DEMOGRAFIA' END FROM app.vw_expansao_municipio WHERE uf IN ('MG','SP','RJ','ES')
UNION ALL SELECT 'expansao_pdv', COUNT(*) FILTER (WHERE supermercados IS NOT NULL OR restaurantes IS NOT NULL OR peixarias IS NOT NULL), COUNT(*), CASE WHEN COUNT(*) FILTER (WHERE supermercados IS NOT NULL OR restaurantes IS NOT NULL OR peixarias IS NOT NULL)>0 THEN 'OK' ELSE 'PENDENTE_BASE_PDV' END FROM app.vw_expansao_municipio WHERE uf IN ('MG','SP','RJ','ES')
UNION ALL SELECT 'ceagesp_pescados_automatico', COUNT(*), COUNT(*), CASE WHEN COUNT(*)>0 THEN 'OK' ELSE 'PENDENTE_CARGA_AUTOMATICA' END FROM app.fato_ceagesp_pescados
UNION ALL SELECT 'base_compra_manual', COUNT(*), COUNT(*), CASE WHEN COUNT(*)>0 THEN 'OK' ELSE 'PENDENTE_IMPORTACAO' END FROM app.fato_compra_manual
UNION ALL SELECT 'previa_vendedores', COUNT(*), COUNT(*), CASE WHEN COUNT(*)>0 THEN 'OK' ELSE 'PENDENTE_IMPORTACAO' END FROM app.fato_previa_vendedores;
