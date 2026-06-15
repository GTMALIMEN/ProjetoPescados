-- ============================================================
-- Radar Pescados IA — Etapa 5
-- Score Inicial de Oportunidade e Risco
-- ============================================================

-- ------------------------------------------------------------
-- Versões de score
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.config_score_versao (
    id SERIAL PRIMARY KEY,
    nome_score TEXT NOT NULL,
    versao TEXT NOT NULL,
    status TEXT CHECK (status IN ('rascunho', 'validada', 'ativa', 'arquivada')),
    data_criacao TIMESTAMP DEFAULT NOW(),
    data_ativacao TIMESTAMP,
    UNIQUE (nome_score, versao)
);

-- ------------------------------------------------------------
-- Pesos dos scores
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.config_pesos_score (
    id SERIAL PRIMARY KEY,
    nome_score TEXT NOT NULL,
    variavel TEXT NOT NULL,
    peso NUMERIC NOT NULL CHECK (peso >= 0),
    versao TEXT DEFAULT 'v1',
    data_inicio_vigencia DATE DEFAULT CURRENT_DATE,
    data_fim_vigencia DATE,
    motivo_alteracao TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT NOW(),
    UNIQUE (nome_score, variavel, versao)
);

-- ------------------------------------------------------------
-- Fato score regional
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.fato_score_regional (
    id BIGSERIAL PRIMARY KEY,
    data_referencia DATE NOT NULL,
    pais TEXT NOT NULL DEFAULT 'Brasil',
    uf TEXT NOT NULL DEFAULT '',
    regiao_ibge TEXT NOT NULL DEFAULT '',
    regiao_comercial TEXT NOT NULL DEFAULT '',
    municipio TEXT NOT NULL DEFAULT '',
    produto TEXT NOT NULL DEFAULT '',
    proteina TEXT NOT NULL DEFAULT '',
    score_oportunidade NUMERIC CHECK (score_oportunidade BETWEEN 0 AND 100),
    score_risco NUMERIC CHECK (score_risco BETWEEN 0 AND 100),
    score_pressao_custo NUMERIC CHECK (score_pressao_custo BETWEEN 0 AND 100),
    score_competitividade NUMERIC CHECK (score_competitividade BETWEEN 0 AND 100),
    score_sensibilidade_dolar NUMERIC CHECK (score_sensibilidade_dolar BETWEEN 0 AND 100),
    score_final NUMERIC CHECK (score_final BETWEEN 0 AND 100),
    cenario_1_10 INT CHECK (cenario_1_10 BETWEEN 1 AND 10),
    confianca NUMERIC CHECK (confianca BETWEEN 0 AND 100),
    metodo TEXT,
    principais_fatores JSONB,
    data_calculo TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_fato_score_regional_natural UNIQUE (
        data_referencia,
        pais,
        uf,
        regiao_ibge,
        regiao_comercial,
        municipio,
        produto,
        proteina
    )
);

CREATE INDEX IF NOT EXISTS idx_score_regional_data
ON app.fato_score_regional (data_referencia);

CREATE INDEX IF NOT EXISTS idx_score_regional_uf_regiao
ON app.fato_score_regional (uf, regiao_comercial, data_referencia);

CREATE INDEX IF NOT EXISTS idx_score_regional_cenario
ON app.fato_score_regional (cenario_1_10);

-- ------------------------------------------------------------
-- Materialized view score regional atual
-- Usa o cálculo mais recente, não necessariamente a maior data_referencia.
-- ------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS app.mv_score_regional_atual;

CREATE MATERIALIZED VIEW app.mv_score_regional_atual AS
WITH ranked AS (
    SELECT
        s.*,
        ROW_NUMBER() OVER (
            PARTITION BY
                s.uf,
                s.regiao_comercial,
                s.municipio,
                s.produto,
                s.proteina
            ORDER BY
                s.data_calculo DESC,
                s.data_referencia DESC,
                s.id DESC
        ) AS rn
    FROM app.fato_score_regional s
)
SELECT
    id,
    data_referencia,
    pais,
    uf,
    regiao_ibge,
    regiao_comercial,
    municipio,
    produto,
    proteina,
    score_oportunidade,
    score_risco,
    score_pressao_custo,
    score_competitividade,
    score_sensibilidade_dolar,
    score_final,
    cenario_1_10,
    confianca,
    metodo,
    principais_fatores,
    data_calculo
FROM ranked
WHERE rn = 1;

CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_score_regional_atual
ON app.mv_score_regional_atual (
    uf,
    regiao_comercial,
    municipio,
    produto,
    proteina
);

-- ------------------------------------------------------------
-- Seeds de pesos iniciais
-- ------------------------------------------------------------
INSERT INTO app.config_score_versao (
    nome_score,
    versao,
    status,
    data_ativacao
)
VALUES
    ('oportunidade_regional_inicial', 'v1', 'ativa', NOW()),
    ('risco_regional_inicial', 'v1', 'ativa', NOW()),
    ('score_final_inicial', 'v1', 'ativa', NOW())
ON CONFLICT DO NOTHING;

INSERT INTO app.config_pesos_score (
    nome_score,
    variavel,
    peso,
    versao,
    motivo_alteracao,
    ativo
)
VALUES
    ('oportunidade_regional_inicial', 'vendas_norm', 0.25, 'v1', 'Seed inicial Etapa 5', TRUE),
    ('oportunidade_regional_inicial', 'volume_norm', 0.20, 'v1', 'Seed inicial Etapa 5', TRUE),
    ('oportunidade_regional_inicial', 'clientes_norm', 0.20, 'v1', 'Seed inicial Etapa 5', TRUE),
    ('oportunidade_regional_inicial', 'municipios_norm', 0.15, 'v1', 'Seed inicial Etapa 5', TRUE),
    ('oportunidade_regional_inicial', 'baixa_cobertura_norm', 0.20, 'v1', 'Seed inicial Etapa 5', TRUE),

    ('risco_regional_inicial', 'queda_vendas_norm', 0.40, 'v1', 'Seed inicial Etapa 5', TRUE),
    ('risco_regional_inicial', 'queda_volume_norm', 0.25, 'v1', 'Seed inicial Etapa 5', TRUE),
    ('risco_regional_inicial', 'pressao_macro_norm', 0.25, 'v1', 'Seed inicial Etapa 5', TRUE),
    ('risco_regional_inicial', 'baixa_base_dados_norm', 0.10, 'v1', 'Seed inicial Etapa 5', TRUE),

    ('score_final_inicial', 'score_oportunidade', 0.60, 'v1', 'Seed inicial Etapa 5', TRUE),
    ('score_final_inicial', 'risco_invertido', 0.40, 'v1', 'Seed inicial Etapa 5', TRUE)
ON CONFLICT DO NOTHING;
