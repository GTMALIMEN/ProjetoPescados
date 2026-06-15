-- ============================================================
-- Radar Pescados IA — Etapa 10
-- Radar de Proteínas e Grãos / Pressão de Custo
-- ============================================================

CREATE TABLE IF NOT EXISTS staging.indicador_setorial (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID REFERENCES app.etl_run(run_id),
    arquivo_origem TEXT,
    linha_origem INT,
    data DATE NOT NULL,
    fonte TEXT NOT NULL,
    indicador TEXT NOT NULL,
    categoria TEXT,
    subcategoria TEXT,
    produto TEXT,
    uf TEXT,
    regiao TEXT,
    valor NUMERIC,
    unidade TEXT,
    periodicidade TEXT,
    natural_key_hash TEXT,
    processado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_staging_indicador_setorial_run
ON staging.indicador_setorial (run_id);

CREATE INDEX IF NOT EXISTS idx_staging_indicador_setorial_indicador
ON staging.indicador_setorial (indicador, data);

CREATE TABLE IF NOT EXISTS dw.fato_indicador_setorial (
    id BIGSERIAL PRIMARY KEY,
    data DATE NOT NULL,
    fonte TEXT NOT NULL,
    indicador TEXT NOT NULL,
    categoria TEXT NOT NULL DEFAULT '',
    subcategoria TEXT NOT NULL DEFAULT '',
    produto TEXT NOT NULL DEFAULT '',
    uf TEXT NOT NULL DEFAULT '',
    regiao TEXT NOT NULL DEFAULT '',
    valor NUMERIC,
    unidade TEXT,
    periodicidade TEXT,
    natural_key_hash TEXT UNIQUE,
    data_coleta TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fato_indicador_setorial_data
ON dw.fato_indicador_setorial (data);

CREATE INDEX IF NOT EXISTS idx_fato_indicador_setorial_categoria
ON dw.fato_indicador_setorial (categoria, produto, indicador);

CREATE INDEX IF NOT EXISTS idx_fato_indicador_setorial_uf
ON dw.fato_indicador_setorial (uf, data);

CREATE TABLE IF NOT EXISTS app.fato_indice_setorial (
    id BIGSERIAL PRIMARY KEY,
    data_referencia DATE NOT NULL,
    uf TEXT NOT NULL DEFAULT '',
    indice TEXT NOT NULL,
    score NUMERIC CHECK (score BETWEEN 0 AND 100),
    cenario_1_10 INT CHECK (cenario_1_10 BETWEEN 1 AND 10),
    confianca NUMERIC CHECK (confianca BETWEEN 0 AND 100),
    metodo TEXT,
    principais_fatores JSONB,
    data_calculo TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_fato_indice_setorial UNIQUE (
        data_referencia,
        uf,
        indice
    )
);

CREATE INDEX IF NOT EXISTS idx_indice_setorial_uf_indice
ON app.fato_indice_setorial (uf, indice, data_referencia);

CREATE TABLE IF NOT EXISTS app.fato_alerta_setorial (
    id BIGSERIAL PRIMARY KEY,
    data_referencia DATE NOT NULL,
    uf TEXT NOT NULL DEFAULT '',
    tipo_alerta TEXT NOT NULL,
    severidade TEXT CHECK (severidade IN ('baixo', 'medio', 'alto', 'critico')),
    titulo TEXT,
    mensagem TEXT,
    score_relacionado NUMERIC CHECK (score_relacionado BETWEEN 0 AND 100),
    status TEXT DEFAULT 'ativo',
    principais_fatores JSONB,
    data_criacao TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_alerta_setorial UNIQUE (
        data_referencia,
        uf,
        tipo_alerta
    )
);

CREATE INDEX IF NOT EXISTS idx_alerta_setorial_uf_status
ON app.fato_alerta_setorial (uf, status, data_referencia);

DROP MATERIALIZED VIEW IF EXISTS app.mv_indice_setorial_atual;

CREATE MATERIALIZED VIEW app.mv_indice_setorial_atual AS
WITH ranked AS (
    SELECT
        i.*,
        ROW_NUMBER() OVER (
            PARTITION BY i.uf, i.indice
            ORDER BY i.data_calculo DESC, i.data_referencia DESC, i.id DESC
        ) AS rn
    FROM app.fato_indice_setorial i
)
SELECT
    id,
    data_referencia,
    uf,
    indice,
    score,
    cenario_1_10,
    confianca,
    metodo,
    principais_fatores,
    data_calculo
FROM ranked
WHERE rn = 1;

CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_indice_setorial_atual
ON app.mv_indice_setorial_atual (uf, indice);

DROP MATERIALIZED VIEW IF EXISTS app.mv_alerta_setorial_atual;

CREATE MATERIALIZED VIEW app.mv_alerta_setorial_atual AS
WITH ranked AS (
    SELECT
        a.*,
        ROW_NUMBER() OVER (
            PARTITION BY a.uf, a.tipo_alerta
            ORDER BY a.data_criacao DESC, a.data_referencia DESC, a.id DESC
        ) AS rn
    FROM app.fato_alerta_setorial a
)
SELECT
    id,
    data_referencia,
    uf,
    tipo_alerta,
    severidade,
    titulo,
    mensagem,
    score_relacionado,
    status,
    principais_fatores,
    data_criacao
FROM ranked
WHERE rn = 1;

CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_alerta_setorial_atual
ON app.mv_alerta_setorial_atual (uf, tipo_alerta);

DROP VIEW IF EXISTS app.vw_indicador_setorial_mensal CASCADE;

CREATE OR REPLACE VIEW app.vw_indicador_setorial_mensal AS
SELECT
    DATE_TRUNC('month', data)::DATE AS mes,
    fonte,
    uf,
    categoria,
    subcategoria,
    produto,
    indicador,
    unidade,
    AVG(valor) AS valor_medio,
    MIN(valor) AS valor_minimo,
    MAX(valor) AS valor_maximo,
    COUNT(*) AS qtd_observacoes
FROM dw.fato_indicador_setorial
GROUP BY
    DATE_TRUNC('month', data)::DATE,
    fonte,
    uf,
    categoria,
    subcategoria,
    produto,
    indicador,
    unidade;

DROP VIEW IF EXISTS app.vw_saude_setorial CASCADE;

CREATE OR REPLACE VIEW app.vw_saude_setorial AS
SELECT
    (SELECT COUNT(*) FROM dw.fato_indicador_setorial) AS qtd_indicadores_setoriais,
    (SELECT COUNT(*) FROM app.fato_indice_setorial) AS qtd_indices_setoriais,
    (SELECT COUNT(*) FROM app.fato_alerta_setorial) AS qtd_alertas_setoriais,
    (SELECT MAX(data) FROM dw.fato_indicador_setorial) AS ultima_data_indicador_setorial;
