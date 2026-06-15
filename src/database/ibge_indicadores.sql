-- ============================================================
-- Radar Pescados IA — Etapa 8
-- IBGE População + Potencial Regional
-- ============================================================

-- ------------------------------------------------------------
-- Staging SIDRA municipal
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.ibge_sidra_municipal (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID REFERENCES app.etl_run(run_id),
    fonte TEXT DEFAULT 'IBGE/SIDRA',
    tabela_sidra TEXT,
    variavel_codigo TEXT,
    variavel_nome TEXT,
    periodo TEXT,
    codigo_ibge TEXT,
    municipio TEXT,
    uf TEXT,
    indicador TEXT,
    categoria TEXT,
    valor NUMERIC,
    unidade TEXT,
    processado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_staging_sidra_run
ON staging.ibge_sidra_municipal (run_id);

CREATE INDEX IF NOT EXISTS idx_staging_sidra_codigo
ON staging.ibge_sidra_municipal (codigo_ibge);

CREATE INDEX IF NOT EXISTS idx_staging_sidra_indicador
ON staging.ibge_sidra_municipal (indicador, periodo);

-- ------------------------------------------------------------
-- Indicador municipal genérico
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.fato_indicador_municipal (
    id BIGSERIAL PRIMARY KEY,
    data_referencia DATE NOT NULL,
    fonte TEXT NOT NULL DEFAULT 'IBGE/SIDRA',
    tabela_sidra TEXT NOT NULL,
    variavel_codigo TEXT NOT NULL,
    variavel_nome TEXT,
    indicador TEXT NOT NULL,
    categoria TEXT,
    pais TEXT DEFAULT 'Brasil',
    uf TEXT,
    codigo_ibge TEXT NOT NULL,
    municipio TEXT,
    valor NUMERIC,
    unidade TEXT,
    data_coleta TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_indicador_municipal UNIQUE (
        data_referencia,
        fonte,
        tabela_sidra,
        variavel_codigo,
        indicador,
        codigo_ibge
    )
);

CREATE INDEX IF NOT EXISTS idx_indicador_municipal_geo
ON dw.fato_indicador_municipal (uf, codigo_ibge, indicador, data_referencia);

CREATE INDEX IF NOT EXISTS idx_indicador_municipal_indicador
ON dw.fato_indicador_municipal (indicador, data_referencia);

-- ------------------------------------------------------------
-- Fato de potencial regional
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.fato_potencial_regional (
    id BIGSERIAL PRIMARY KEY,
    data_referencia DATE NOT NULL,
    uf TEXT NOT NULL DEFAULT '',
    regiao_comercial TEXT NOT NULL DEFAULT '',
    populacao_estimada NUMERIC,
    qtd_municipios INT,
    faturamento NUMERIC,
    volume_kg NUMERIC,
    qtd_clientes INT,
    qtd_produtos INT,
    venda_per_capita NUMERIC,
    clientes_por_100k NUMERIC,
    score_populacao NUMERIC CHECK (score_populacao BETWEEN 0 AND 100),
    score_baixa_penetracao NUMERIC CHECK (score_baixa_penetracao BETWEEN 0 AND 100),
    score_baixa_cobertura NUMERIC CHECK (score_baixa_cobertura BETWEEN 0 AND 100),
    score_potencial NUMERIC CHECK (score_potencial BETWEEN 0 AND 100),
    cenario_1_10 INT CHECK (cenario_1_10 BETWEEN 1 AND 10),
    confianca NUMERIC CHECK (confianca BETWEEN 0 AND 100),
    principais_fatores JSONB,
    data_calculo TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_potencial_regional UNIQUE (
        data_referencia,
        uf,
        regiao_comercial
    )
);

CREATE INDEX IF NOT EXISTS idx_potencial_regional_uf
ON app.fato_potencial_regional (uf, score_potencial DESC, data_referencia DESC);

DROP MATERIALIZED VIEW IF EXISTS app.mv_potencial_regional_atual;

CREATE MATERIALIZED VIEW app.mv_potencial_regional_atual AS
WITH ranked AS (
    SELECT
        p.*,
        ROW_NUMBER() OVER (
            PARTITION BY p.uf, p.regiao_comercial
            ORDER BY p.data_calculo DESC, p.data_referencia DESC, p.id DESC
        ) AS rn
    FROM app.fato_potencial_regional p
)
SELECT
    id,
    data_referencia,
    uf,
    regiao_comercial,
    populacao_estimada,
    qtd_municipios,
    faturamento,
    volume_kg,
    qtd_clientes,
    qtd_produtos,
    venda_per_capita,
    clientes_por_100k,
    score_populacao,
    score_baixa_penetracao,
    score_baixa_cobertura,
    score_potencial,
    cenario_1_10,
    confianca,
    principais_fatores,
    data_calculo
FROM ranked
WHERE rn = 1;

CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_potencial_regional_atual
ON app.mv_potencial_regional_atual (uf, regiao_comercial);

-- ------------------------------------------------------------
-- View de indicadores municipais com geografia comercial
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW app.vw_indicador_municipal_geo AS
SELECT
    im.data_referencia,
    im.fonte,
    im.tabela_sidra,
    im.variavel_codigo,
    im.variavel_nome,
    im.indicador,
    im.categoria,
    im.uf,
    im.codigo_ibge,
    im.municipio,
    dg.regiao_comercial,
    dg.regiao_brasil,
    dg.mesorregiao,
    dg.microrregiao,
    im.valor,
    im.unidade,
    im.data_coleta
FROM dw.fato_indicador_municipal im
LEFT JOIN dw.dim_geografia dg
    ON im.codigo_ibge = dg.codigo_ibge;
