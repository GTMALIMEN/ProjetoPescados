-- ============================================================
-- Radar Pescados IA — Etapa 15
-- Relatório Executivo Automático
-- ============================================================

CREATE TABLE IF NOT EXISTS app.fato_relatorio_executivo (
    id BIGSERIAL PRIMARY KEY,
    data_geracao TIMESTAMP DEFAULT NOW(),
    periodo_inicio DATE,
    periodo_fim DATE,
    uf TEXT NOT NULL DEFAULT 'MG',
    tipo_relatorio TEXT NOT NULL DEFAULT 'executivo',
    titulo TEXT NOT NULL,
    resumo_executivo TEXT,
    mensagem_whatsapp TEXT,
    html_relatorio TEXT,
    caminho_excel TEXT,
    caminho_html TEXT,
    parametros JSONB,
    indicadores JSONB,
    status TEXT DEFAULT 'gerado' CHECK (status IN ('gerado', 'enviado', 'arquivado', 'erro')),
    usuario TEXT
);

CREATE INDEX IF NOT EXISTS idx_relatorio_executivo_data
ON app.fato_relatorio_executivo (data_geracao DESC);

CREATE INDEX IF NOT EXISTS idx_relatorio_executivo_uf
ON app.fato_relatorio_executivo (uf, data_geracao DESC);

CREATE OR REPLACE VIEW app.vw_relatorios_executivos_recentes AS
SELECT
    id,
    data_geracao,
    periodo_inicio,
    periodo_fim,
    uf,
    tipo_relatorio,
    titulo,
    status,
    usuario,
    caminho_excel,
    caminho_html
FROM app.fato_relatorio_executivo
ORDER BY data_geracao DESC, id DESC;

CREATE OR REPLACE VIEW app.vw_relatorio_executivo_ultimo AS
SELECT *
FROM app.fato_relatorio_executivo
ORDER BY data_geracao DESC, id DESC
LIMIT 1;
