-- ============================================================
-- Radar Pescados IA — Etapa 9
-- Integração do Potencial Regional nos Scores e Recomendações
-- ============================================================

-- ------------------------------------------------------------
-- Novas colunas nos scores
-- ------------------------------------------------------------
ALTER TABLE app.fato_score_regional
    ADD COLUMN IF NOT EXISTS score_potencial NUMERIC CHECK (score_potencial BETWEEN 0 AND 100);

CREATE INDEX IF NOT EXISTS idx_score_regional_potencial
ON app.fato_score_regional (score_potencial);

-- ------------------------------------------------------------
-- Novas colunas nas recomendações
-- ------------------------------------------------------------
ALTER TABLE app.fato_recomendacao
    ADD COLUMN IF NOT EXISTS score_potencial NUMERIC CHECK (score_potencial BETWEEN 0 AND 100),
    ADD COLUMN IF NOT EXISTS motor_decisao TEXT;

CREATE INDEX IF NOT EXISTS idx_recomendacao_motor_decisao
ON app.fato_recomendacao (motor_decisao);

-- ------------------------------------------------------------
-- Recria MV de score atual incluindo score_potencial
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
    score_potencial,
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
-- Recria MV de recomendação atual incluindo potencial e motor de decisão
-- ------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS app.mv_recomendacao_atual;

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
-- Pesos/documentação de configuração da nova lógica
-- ------------------------------------------------------------
INSERT INTO app.config_score_versao (
    nome_score,
    versao,
    status,
    data_ativacao
)
VALUES
    ('oportunidade_regional_com_potencial', 'v2', 'ativa', NOW()),
    ('score_final_com_potencial', 'v2', 'ativa', NOW())
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
    ('oportunidade_regional_com_potencial', 'vendas_norm', 0.20, 'v2', 'Etapa 9 — integração potencial regional', TRUE),
    ('oportunidade_regional_com_potencial', 'volume_norm', 0.15, 'v2', 'Etapa 9 — integração potencial regional', TRUE),
    ('oportunidade_regional_com_potencial', 'clientes_norm', 0.15, 'v2', 'Etapa 9 — integração potencial regional', TRUE),
    ('oportunidade_regional_com_potencial', 'municipios_norm', 0.10, 'v2', 'Etapa 9 — integração potencial regional', TRUE),
    ('oportunidade_regional_com_potencial', 'baixa_cobertura_norm', 0.15, 'v2', 'Etapa 9 — integração potencial regional', TRUE),
    ('oportunidade_regional_com_potencial', 'score_potencial', 0.25, 'v2', 'Etapa 9 — integração potencial regional', TRUE),

    ('score_final_com_potencial', 'score_oportunidade', 0.55, 'v2', 'Etapa 9 — integração potencial regional', TRUE),
    ('score_final_com_potencial', 'risco_invertido', 0.30, 'v2', 'Etapa 9 — integração potencial regional', TRUE),
    ('score_final_com_potencial', 'score_potencial', 0.15, 'v2', 'Etapa 9 — integração potencial regional', TRUE)
ON CONFLICT DO NOTHING;
