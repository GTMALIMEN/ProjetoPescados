-- ============================================================
-- Radar Pescados IA — Etapa 13
-- Simulador What-if / Sandbox
-- ============================================================

CREATE TABLE IF NOT EXISTS app.fato_simulacao_whatif (
    id BIGSERIAL PRIMARY KEY,
    data_simulacao TIMESTAMP DEFAULT NOW(),
    uf TEXT NOT NULL DEFAULT 'MG',
    regiao_comercial TEXT NOT NULL DEFAULT '',
    nome_cenario TEXT,
    usuario TEXT,
    parametros JSONB,
    resultado JSONB,
    score_atual NUMERIC,
    score_simulado NUMERIC,
    delta_score NUMERIC,
    cenario_atual INT,
    cenario_simulado INT,
    recomendacao_atual TEXT,
    recomendacao_simulada TEXT,
    motor_decisao_simulado TEXT
);

CREATE INDEX IF NOT EXISTS idx_fato_simulacao_whatif_data
ON app.fato_simulacao_whatif (data_simulacao DESC);

CREATE INDEX IF NOT EXISTS idx_fato_simulacao_whatif_regiao
ON app.fato_simulacao_whatif (uf, regiao_comercial);

CREATE OR REPLACE VIEW app.vw_whatif_ultimas_simulacoes AS
SELECT
    id,
    data_simulacao,
    uf,
    regiao_comercial,
    nome_cenario,
    score_atual,
    score_simulado,
    delta_score,
    cenario_atual,
    cenario_simulado,
    recomendacao_atual,
    recomendacao_simulada,
    motor_decisao_simulado
FROM app.fato_simulacao_whatif
ORDER BY data_simulacao DESC;

CREATE OR REPLACE VIEW app.vw_whatif_resumo_regiao AS
SELECT
    uf,
    regiao_comercial,
    COUNT(*) AS qtd_simulacoes,
    AVG(delta_score) AS delta_medio,
    MAX(delta_score) AS melhor_delta,
    MIN(delta_score) AS pior_delta,
    MAX(data_simulacao) AS ultima_simulacao
FROM app.fato_simulacao_whatif
GROUP BY uf, regiao_comercial;
