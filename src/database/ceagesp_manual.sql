
-- ============================================================
-- CEAGESP Manual — tabela histórica e diagnóstico
-- ============================================================

CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS app.fato_ceagesp_pescados (
    id BIGSERIAL PRIMARY KEY,
    chave_registro TEXT,
    data_coleta TIMESTAMP DEFAULT NOW(),
    data_referencia DATE,
    categoria TEXT DEFAULT 'Pescados',
    produto TEXT,
    classificacao TEXT,
    unidade TEXT,
    preco_minimo NUMERIC,
    preco_comum NUMERIC,
    preco_maximo NUMERIC,
    fonte TEXT DEFAULT 'CEAGESP Manual',
    url_fonte TEXT,
    hash_carga TEXT,
    criado_em TIMESTAMP DEFAULT NOW()
);

ALTER TABLE app.fato_ceagesp_pescados
    ADD COLUMN IF NOT EXISTS chave_registro TEXT,
    ADD COLUMN IF NOT EXISTS observacao TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_fato_ceagesp_pescados_chave_registro_unique'
    ) THEN
        ALTER TABLE app.fato_ceagesp_pescados
        ADD CONSTRAINT uq_fato_ceagesp_pescados_chave_registro_unique UNIQUE (chave_registro);
    END IF;
EXCEPTION
    WHEN duplicate_table THEN NULL;
    WHEN duplicate_object THEN NULL;
END $$;

CREATE INDEX IF NOT EXISTS idx_ceagesp_pescados_data_produto
ON app.fato_ceagesp_pescados (data_referencia DESC, produto);

CREATE OR REPLACE VIEW app.vw_ceagesp_pescados_historico AS
SELECT
    data_referencia,
    categoria,
    produto,
    classificacao,
    unidade,
    preco_minimo,
    preco_comum,
    preco_maximo,
    fonte,
    url_fonte,
    observacao,
    data_coleta
FROM app.fato_ceagesp_pescados
ORDER BY data_referencia DESC, produto;

-- Diagnóstico V2 ajustado: CEAGESP agora é manual/controlado.
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
       CASE WHEN COUNT(*) FILTER (WHERE idh IS NOT NULL) > 0 THEN 'OK' ELSE 'PENDENTE_CARGA_AUTOMATICA' END
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
