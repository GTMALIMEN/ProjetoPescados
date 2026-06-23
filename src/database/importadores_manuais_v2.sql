CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.importacao_manual_log (
    id BIGSERIAL PRIMARY KEY,
    tipo_importacao TEXT NOT NULL,
    arquivo TEXT,
    status TEXT NOT NULL,
    registros_lidos INTEGER DEFAULT 0,
    registros_processados INTEGER DEFAULT 0,
    registros_rejeitados INTEGER DEFAULT 0,
    detalhe TEXT,
    executado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_importacao_manual_log_tipo_data
ON app.importacao_manual_log (tipo_importacao, executado_em DESC);

DROP VIEW IF EXISTS app.vw_importacao_manual_resumo CASCADE;

CREATE OR REPLACE VIEW app.vw_importacao_manual_resumo AS
SELECT
    tipo_importacao,
    status,
    COUNT(*) AS qtd_execucoes,
    MAX(executado_em) AS ultima_execucao,
    SUM(COALESCE(registros_processados, 0)) AS registros_processados
FROM app.importacao_manual_log
GROUP BY tipo_importacao, status;
