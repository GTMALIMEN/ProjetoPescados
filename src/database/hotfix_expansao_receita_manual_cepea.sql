
-- ============================================================
-- Hotfix Expansão + Receita Manual + CEPEA/CEAGESP
-- ============================================================

CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS dw;
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS app.fato_receita_manual_expansao (
    id BIGSERIAL PRIMARY KEY,
    parceiro TEXT,
    cidade TEXT,
    estado TEXT,
    data_competencia DATE,
    mes DATE,
    grupo_produto TEXT,
    categoria_pescado TEXT,
    vlr_total_liquido NUMERIC,
    fonte_arquivo TEXT,
    hash_linha TEXT,
    data_carga TIMESTAMP DEFAULT NOW()
);

ALTER TABLE app.fato_receita_manual_expansao
    ADD COLUMN IF NOT EXISTS parceiro TEXT,
    ADD COLUMN IF NOT EXISTS cidade TEXT,
    ADD COLUMN IF NOT EXISTS estado TEXT,
    ADD COLUMN IF NOT EXISTS data_competencia DATE,
    ADD COLUMN IF NOT EXISTS mes DATE,
    ADD COLUMN IF NOT EXISTS grupo_produto TEXT,
    ADD COLUMN IF NOT EXISTS categoria_pescado TEXT,
    ADD COLUMN IF NOT EXISTS vlr_total_liquido NUMERIC,
    ADD COLUMN IF NOT EXISTS fonte_arquivo TEXT,
    ADD COLUMN IF NOT EXISTS hash_linha TEXT,
    ADD COLUMN IF NOT EXISTS data_carga TIMESTAMP DEFAULT NOW();

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_fato_receita_manual_expansao_hash_linha'
    ) THEN
        ALTER TABLE app.fato_receita_manual_expansao
        ADD CONSTRAINT uq_fato_receita_manual_expansao_hash_linha UNIQUE (hash_linha);
    END IF;
EXCEPTION
    WHEN duplicate_table THEN NULL;
    WHEN duplicate_object THEN NULL;
END $$;

CREATE INDEX IF NOT EXISTS idx_receita_manual_expansao_estado_cidade
ON app.fato_receita_manual_expansao (estado, cidade);

CREATE INDEX IF NOT EXISTS idx_receita_manual_expansao_data
ON app.fato_receita_manual_expansao (data_competencia DESC);

CREATE INDEX IF NOT EXISTS idx_receita_manual_expansao_categoria
ON app.fato_receita_manual_expansao (categoria_pescado);

CREATE OR REPLACE VIEW app.vw_receita_manual_expansao AS
SELECT
    parceiro,
    cidade,
    estado,
    data_competencia,
    mes,
    grupo_produto,
    categoria_pescado,
    vlr_total_liquido,
    fonte_arquivo,
    data_carga
FROM app.fato_receita_manual_expansao
ORDER BY data_competencia DESC, estado, cidade, parceiro;

CREATE OR REPLACE VIEW app.vw_receita_manual_expansao_resumo AS
SELECT
    COUNT(*) AS qtd_registros,
    COUNT(DISTINCT parceiro) AS qtd_parceiros,
    COUNT(DISTINCT cidade || '-' || estado) AS qtd_cidades,
    COUNT(DISTINCT grupo_produto) AS qtd_grupos_produto,
    MIN(data_competencia) AS primeira_data,
    MAX(data_competencia) AS ultima_data,
    SUM(vlr_total_liquido) AS receita_total
FROM app.fato_receita_manual_expansao;
