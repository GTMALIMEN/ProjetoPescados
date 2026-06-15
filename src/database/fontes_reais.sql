-- ============================================================
-- Radar Pescados IA — Etapa 11
-- Fontes reais setoriais: Comex Stat, CONAB e CEPEA
-- ============================================================

CREATE TABLE IF NOT EXISTS app.config_fonte_real_setorial (
    id SERIAL PRIMARY KEY,
    fonte TEXT NOT NULL UNIQUE,
    tipo_integracao TEXT NOT NULL,
    url_referencia TEXT,
    status TEXT DEFAULT 'ativa',
    observacao TEXT,
    data_criacao TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.config_ncm_pescado (
    id SERIAL PRIMARY KEY,
    grupo_pescado TEXT NOT NULL,
    ncm TEXT NOT NULL,
    descricao TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT NOW(),
    UNIQUE (grupo_pescado, ncm)
);

CREATE TABLE IF NOT EXISTS raw.comexstat_payload (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID REFERENCES app.etl_run(run_id),
    endpoint TEXT,
    request_payload JSONB,
    response_payload JSONB,
    status_http INT,
    data_coleta TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_raw_comexstat_payload_run
ON raw.comexstat_payload (run_id);

CREATE TABLE IF NOT EXISTS app.etl_fonte_real_resumo (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID REFERENCES app.etl_run(run_id),
    fonte TEXT NOT NULL,
    origem TEXT,
    status TEXT,
    registros_lidos INT DEFAULT 0,
    registros_dw INT DEFAULT 0,
    detalhe TEXT,
    data_execucao TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_etl_fonte_real_resumo_fonte
ON app.etl_fonte_real_resumo (fonte, data_execucao DESC);

CREATE OR REPLACE VIEW app.vw_fontes_reais_setoriais AS
SELECT
    fonte,
    COUNT(*) AS qtd_registros,
    COUNT(DISTINCT indicador) AS qtd_indicadores,
    COUNT(DISTINCT produto) AS qtd_produtos,
    MIN(data) AS primeira_data,
    MAX(data) AS ultima_data
FROM dw.fato_indicador_setorial
WHERE fonte IN ('Comex Stat', 'CONAB', 'CEPEA')
GROUP BY fonte
ORDER BY fonte;

CREATE OR REPLACE VIEW app.vw_fontes_reais_ultimas_cargas AS
SELECT
    fonte,
    origem,
    status,
    registros_lidos,
    registros_dw,
    detalhe,
    data_execucao
FROM app.etl_fonte_real_resumo
ORDER BY data_execucao DESC;

INSERT INTO app.config_fonte_real_setorial (
    fonte,
    tipo_integracao,
    url_referencia,
    status,
    observacao
)
VALUES
    (
        'Comex Stat',
        'api',
        'https://api-comexstat.mdic.gov.br/docs',
        'ativa',
        'API oficial de estatísticas de comércio exterior. Usada para importação de pescados por NCM.'
    ),
    (
        'CONAB',
        'arquivo_download',
        'https://portaldeinformacoes.conab.gov.br/download-arquivos.html',
        'ativa',
        'Arquivos de preços agropecuários baixados do portal da CONAB e carregados no DW.'
    ),
    (
        'CEPEA',
        'arquivo_excel',
        'https://cepea.org.br/br/consultas-ao-banco-de-dados-do-site.aspx',
        'ativa',
        'Planilhas exportadas pelo site CEPEA e carregadas no DW.'
    )
ON CONFLICT (fonte)
DO UPDATE SET
    tipo_integracao = EXCLUDED.tipo_integracao,
    url_referencia = EXCLUDED.url_referencia,
    status = EXCLUDED.status,
    observacao = EXCLUDED.observacao;

-- NCMs iniciais e editáveis. São códigos representativos para começar a integração.
-- Ajuste conforme a classificação fiscal usada pela empresa.
INSERT INTO app.config_ncm_pescado (
    grupo_pescado,
    ncm,
    descricao,
    ativo
)
VALUES
    ('salmao', '03021400', 'Salmões do Atlântico e do Danúbio, frescos ou refrigerados', TRUE),
    ('salmao', '03031300', 'Salmões congelados', TRUE),
    ('salmao', '03048100', 'Filés congelados de salmão', TRUE),

    ('bacalhau', '03025100', 'Bacalhaus frescos ou refrigerados', TRUE),
    ('bacalhau', '03036300', 'Bacalhaus congelados', TRUE),
    ('bacalhau', '03055100', 'Bacalhaus secos, mesmo salgados', TRUE),
    ('bacalhau', '03056200', 'Bacalhaus salgados ou em salmoura', TRUE),

    ('camarao', '03061710', 'Camarões congelados', TRUE),
    ('camarao', '03061790', 'Outros camarões congelados', TRUE),
    ('camarao', '03061610', 'Camarões de água fria congelados', TRUE)
ON CONFLICT (grupo_pescado, ncm)
DO UPDATE SET
    descricao = EXCLUDED.descricao,
    ativo = EXCLUDED.ativo;
