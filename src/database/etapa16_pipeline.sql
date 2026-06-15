-- ============================================================
-- Radar Pescados IA — Etapa 16
-- Pipeline Mestre / Orquestração
-- ============================================================

CREATE TABLE IF NOT EXISTS app.pipeline_execucao (
    id BIGSERIAL PRIMARY KEY,
    pipeline_id UUID NOT NULL,
    nome_pipeline TEXT NOT NULL DEFAULT 'pipeline_full',
    uf TEXT DEFAULT 'MG',
    ambiente TEXT DEFAULT 'local',
    status TEXT NOT NULL CHECK (status IN ('INICIADO', 'SUCESSO', 'ERRO', 'PARCIAL', 'CANCELADO')),
    iniciado_em TIMESTAMP DEFAULT NOW(),
    finalizado_em TIMESTAMP,
    tempo_total_segundos NUMERIC,
    usuario TEXT,
    parametros JSONB,
    mensagem TEXT
);

CREATE INDEX IF NOT EXISTS idx_pipeline_execucao_pipeline_id
ON app.pipeline_execucao (pipeline_id);

CREATE INDEX IF NOT EXISTS idx_pipeline_execucao_status
ON app.pipeline_execucao (status, iniciado_em DESC);

CREATE TABLE IF NOT EXISTS app.pipeline_etapa_execucao (
    id BIGSERIAL PRIMARY KEY,
    pipeline_id UUID NOT NULL,
    ordem INT NOT NULL,
    nome_etapa TEXT NOT NULL,
    comando TEXT,
    obrigatoria BOOLEAN DEFAULT TRUE,
    status TEXT NOT NULL CHECK (status IN ('PENDENTE', 'INICIADO', 'SUCESSO', 'ERRO', 'IGNORADO')),
    iniciado_em TIMESTAMP,
    finalizado_em TIMESTAMP,
    tempo_segundos NUMERIC,
    stdout TEXT,
    stderr TEXT,
    mensagem TEXT
);

CREATE INDEX IF NOT EXISTS idx_pipeline_etapa_execucao_pipeline_id
ON app.pipeline_etapa_execucao (pipeline_id, ordem);

CREATE INDEX IF NOT EXISTS idx_pipeline_etapa_execucao_status
ON app.pipeline_etapa_execucao (status, iniciado_em DESC);

CREATE OR REPLACE VIEW app.vw_pipeline_ultimas_execucoes AS
SELECT
    id,
    pipeline_id,
    nome_pipeline,
    uf,
    ambiente,
    status,
    iniciado_em,
    finalizado_em,
    tempo_total_segundos,
    usuario,
    mensagem
FROM app.pipeline_execucao
ORDER BY iniciado_em DESC, id DESC;

CREATE OR REPLACE VIEW app.vw_pipeline_etapas_recentes AS
SELECT
    e.pipeline_id,
    p.nome_pipeline,
    p.status AS status_pipeline,
    e.ordem,
    e.nome_etapa,
    e.obrigatoria,
    e.status,
    e.tempo_segundos,
    e.mensagem,
    e.iniciado_em,
    e.finalizado_em
FROM app.pipeline_etapa_execucao e
LEFT JOIN app.pipeline_execucao p
    ON p.pipeline_id = e.pipeline_id
ORDER BY e.iniciado_em DESC, e.pipeline_id, e.ordem;

CREATE OR REPLACE VIEW app.vw_pipeline_saude AS
SELECT
    COUNT(*) AS qtd_execucoes,
    COUNT(*) FILTER (WHERE status = 'SUCESSO') AS qtd_sucesso,
    COUNT(*) FILTER (WHERE status = 'ERRO') AS qtd_erro,
    COUNT(*) FILTER (WHERE status = 'PARCIAL') AS qtd_parcial,
    MAX(iniciado_em) AS ultima_execucao,
    MAX(finalizado_em) AS ultimo_fim,
    AVG(tempo_total_segundos) AS tempo_medio_segundos
FROM app.pipeline_execucao;
