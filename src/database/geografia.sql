-- ============================================================
-- Radar Pescados IA — Etapa 2
-- IBGE Localidades + Geografia
-- Correção: campos de ID como BIGINT e limpeza de NaN no ETL.
-- ============================================================

-- ------------------------------------------------------------
-- Staging UFs IBGE
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.ibge_ufs (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID REFERENCES app.etl_run(run_id),
    id_uf BIGINT,
    sigla_uf TEXT,
    nome_uf TEXT,
    id_regiao BIGINT,
    sigla_regiao TEXT,
    nome_regiao TEXT,
    processado_em TIMESTAMP DEFAULT NOW()
);

-- Migração segura para bases já criadas
ALTER TABLE staging.ibge_ufs
    ALTER COLUMN id_uf TYPE BIGINT,
    ALTER COLUMN id_regiao TYPE BIGINT;

CREATE INDEX IF NOT EXISTS idx_staging_ibge_ufs_run
ON staging.ibge_ufs (run_id);

CREATE INDEX IF NOT EXISTS idx_staging_ibge_ufs_sigla
ON staging.ibge_ufs (sigla_uf);

-- ------------------------------------------------------------
-- Staging Municípios IBGE
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.ibge_municipios (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID REFERENCES app.etl_run(run_id),
    codigo_ibge TEXT,
    municipio TEXT,
    id_microrregiao BIGINT,
    microrregiao TEXT,
    id_mesorregiao BIGINT,
    mesorregiao TEXT,
    id_uf BIGINT,
    sigla_uf TEXT,
    nome_uf TEXT,
    id_regiao BIGINT,
    sigla_regiao TEXT,
    nome_regiao TEXT,
    processado_em TIMESTAMP DEFAULT NOW()
);

-- Migração segura para bases já criadas
ALTER TABLE staging.ibge_municipios
    ALTER COLUMN id_microrregiao TYPE BIGINT,
    ALTER COLUMN id_mesorregiao TYPE BIGINT,
    ALTER COLUMN id_uf TYPE BIGINT,
    ALTER COLUMN id_regiao TYPE BIGINT;

CREATE INDEX IF NOT EXISTS idx_staging_ibge_municipios_run
ON staging.ibge_municipios (run_id);

CREATE INDEX IF NOT EXISTS idx_staging_ibge_municipios_codigo
ON staging.ibge_municipios (codigo_ibge);

CREATE INDEX IF NOT EXISTS idx_staging_ibge_municipios_uf
ON staging.ibge_municipios (sigla_uf);

-- ------------------------------------------------------------
-- Dimensão Geográfica
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_geografia (
    id_geografia SERIAL PRIMARY KEY,
    codigo_ibge TEXT UNIQUE,
    pais TEXT DEFAULT 'Brasil',
    uf TEXT,
    nome_uf TEXT,
    municipio TEXT,
    regiao_brasil TEXT,
    sigla_regiao_brasil TEXT,
    mesorregiao TEXT,
    microrregiao TEXT,
    regiao_intermediaria TEXT,
    regiao_imediata TEXT,
    regiao_metropolitana TEXT,
    regiao_comercial TEXT,
    latitude NUMERIC,
    longitude NUMERIC,
    fonte TEXT DEFAULT 'IBGE',
    data_atualizacao TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dim_geografia_uf
ON dw.dim_geografia (uf);

CREATE INDEX IF NOT EXISTS idx_dim_geografia_municipio
ON dw.dim_geografia (municipio);

CREATE INDEX IF NOT EXISTS idx_dim_geografia_regiao_comercial
ON dw.dim_geografia (regiao_comercial);

-- ------------------------------------------------------------
-- Regiões comerciais manuais
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.dim_regiao_comercial (
    id SERIAL PRIMARY KEY,
    uf TEXT NOT NULL,
    regiao_comercial TEXT NOT NULL,
    municipio TEXT NOT NULL,
    codigo_ibge TEXT,
    prioridade INT,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT NOW(),
    UNIQUE (uf, regiao_comercial, municipio)
);

CREATE INDEX IF NOT EXISTS idx_regiao_comercial_uf
ON app.dim_regiao_comercial (uf);

CREATE INDEX IF NOT EXISTS idx_regiao_comercial_codigo_ibge
ON app.dim_regiao_comercial (codigo_ibge);
