-- ============================================================
-- Radar Pescados IA — Etapa 12
-- Indicadores setoriais integrados aos Scores e Recomendações
-- ============================================================

-- ------------------------------------------------------------
-- Novas colunas nos scores regionais
-- ------------------------------------------------------------
ALTER TABLE app.fato_score_regional
    ADD COLUMN IF NOT EXISTS score_setorial NUMERIC CHECK (score_setorial BETWEEN 0 AND 100),
    ADD COLUMN IF NOT EXISTS score_competitividade_setorial NUMERIC CHECK (score_competitividade_setorial BETWEEN 0 AND 100),
    ADD COLUMN IF NOT EXISTS score_pressao_custo_setorial NUMERIC CHECK (score_pressao_custo_setorial BETWEEN 0 AND 100),
    ADD COLUMN IF NOT EXISTS score_risco_substituicao_setorial NUMERIC CHECK (score_risco_substituicao_setorial BETWEEN 0 AND 100);

CREATE INDEX IF NOT EXISTS idx_score_regional_setorial
ON app.fato_score_regional (score_setorial);

CREATE INDEX IF NOT EXISTS idx_score_regional_pressao_custo_setorial
ON app.fato_score_regional (score_pressao_custo_setorial);

-- ------------------------------------------------------------
-- Novas colunas nas recomendações
-- ------------------------------------------------------------
ALTER TABLE app.fato_recomendacao
    ADD COLUMN IF NOT EXISTS score_setorial NUMERIC CHECK (score_setorial BETWEEN 0 AND 100),
    ADD COLUMN IF NOT EXISTS score_competitividade_setorial NUMERIC CHECK (score_competitividade_setorial BETWEEN 0 AND 100),
    ADD COLUMN IF NOT EXISTS score_pressao_custo_setorial NUMERIC CHECK (score_pressao_custo_setorial BETWEEN 0 AND 100),
    ADD COLUMN IF NOT EXISTS score_risco_substituicao_setorial NUMERIC CHECK (score_risco_substituicao_setorial BETWEEN 0 AND 100);

CREATE INDEX IF NOT EXISTS idx_recomendacao_score_setorial
ON app.fato_recomendacao (score_setorial);

-- ------------------------------------------------------------
-- Recria MV de score atual
-- ------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS app.mv_recomendacao_atual;
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
    score_potencial,
    score_setorial,
    score_competitividade_setorial,
    score_pressao_custo_setorial,
    score_risco_substituicao_setorial,
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
-- Recria MV de recomendação atual
-- ------------------------------------------------------------
CREATE MATERIALIZED VIEW app.mv_recomendacao_atual AS
WITH ranked AS (
    SELECT
        r.*,
        ROW_NUMBER() OVER (
            PARTITION BY
                r.uf,
                r.regiao_comercial,
                r.municipio,
                r.produto,
                r.proteina
            ORDER BY
                r.data_criacao DESC,
                r.data_referencia DESC,
                r.id DESC
        ) AS rn
    FROM app.fato_recomendacao r
)
SELECT
    id,
    id_score,
    data_referencia,
    pais,
    uf,
    regiao_comercial,
    municipio,
    produto,
    proteina,
    cenario_1_10,
    tipo_recomendacao,
    acao_sugerida,
    justificativa,
    confianca,
    impacto_estimado,
    roi_estimado,
    score_vendedor,
    score_promotor,
    score_campanha,
    score_potencial,
    score_setorial,
    score_competitividade_setorial,
    score_pressao_custo_setorial,
    score_risco_substituicao_setorial,
    motor_decisao,
    status,
    principais_fatores,
    data_criacao
FROM ranked
WHERE rn = 1;

CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_recomendacao_atual
ON app.mv_recomendacao_atual (
    uf,
    regiao_comercial,
    municipio,
    produto,
    proteina
);

-- ------------------------------------------------------------
-- Pesos de documentação
-- ------------------------------------------------------------
INSERT INTO app.config_score_versao (
    nome_score,
    versao,
    status,
    data_ativacao
)
VALUES
    ('score_regional_com_potencial_setorial', 'v3', 'ativa', NOW()),
    ('risco_regional_com_setorial', 'v3', 'ativa', NOW())
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
    ('risco_regional_com_setorial', 'risco_regional_base', 0.70, 'v3', 'Etapa 12 — indicadores setoriais integrados', TRUE),
    ('risco_regional_com_setorial', 'score_setorial', 0.30, 'v3', 'Etapa 12 — indicadores setoriais integrados', TRUE),

    ('score_regional_com_potencial_setorial', 'score_oportunidade', 0.50, 'v3', 'Etapa 12 — indicadores setoriais integrados', TRUE),
    ('score_regional_com_potencial_setorial', 'risco_invertido', 0.25, 'v3', 'Etapa 12 — indicadores setoriais integrados', TRUE),
    ('score_regional_com_potencial_setorial', 'score_potencial', 0.15, 'v3', 'Etapa 12 — indicadores setoriais integrados', TRUE),
    ('score_regional_com_potencial_setorial', 'competitividade_setorial', 0.10, 'v3', 'Etapa 12 — indicadores setoriais integrados', TRUE)
ON CONFLICT DO NOTHING;
