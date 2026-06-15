-- ============================================================
-- Radar Pescados IA — Etapa 14
-- Alertas Ativos e Plano de Ação
-- ============================================================

CREATE TABLE IF NOT EXISTS app.config_alerta_ativo (
    id SERIAL PRIMARY KEY,
    tipo_alerta TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    area_responsavel TEXT NOT NULL,
    descricao TEXT,
    limite_alerta NUMERIC,
    limite_critico NUMERIC,
    direcao TEXT CHECK (direcao IN ('maior_pior', 'menor_pior', 'queda_pior', 'manual')),
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.fato_alerta_ativo (
    id BIGSERIAL PRIMARY KEY,
    data_referencia DATE NOT NULL,
    uf TEXT NOT NULL DEFAULT 'MG',
    regiao_comercial TEXT NOT NULL DEFAULT '',
    area_responsavel TEXT NOT NULL,
    tipo_alerta TEXT NOT NULL,
    severidade TEXT NOT NULL CHECK (severidade IN ('baixo', 'medio', 'alto', 'critico')),
    status TEXT NOT NULL DEFAULT 'ativo' CHECK (status IN ('ativo', 'em_analise', 'resolvido', 'ignorado')),
    titulo TEXT NOT NULL,
    mensagem TEXT,
    score_relacionado NUMERIC,
    recomendacao_sugerida TEXT,
    origem TEXT,
    principais_fatores JSONB,
    data_criacao TIMESTAMP DEFAULT NOW(),
    data_atualizacao TIMESTAMP DEFAULT NOW(),
    data_resolucao TIMESTAMP,
    CONSTRAINT uq_alerta_ativo UNIQUE (
        data_referencia,
        uf,
        regiao_comercial,
        tipo_alerta,
        origem
    )
);

CREATE INDEX IF NOT EXISTS idx_alerta_ativo_status
ON app.fato_alerta_ativo (status, severidade, data_referencia DESC);

CREATE INDEX IF NOT EXISTS idx_alerta_ativo_area
ON app.fato_alerta_ativo (area_responsavel, status, severidade);

CREATE INDEX IF NOT EXISTS idx_alerta_ativo_regiao
ON app.fato_alerta_ativo (uf, regiao_comercial, status);

CREATE TABLE IF NOT EXISTS app.historico_alerta_ativo (
    id BIGSERIAL PRIMARY KEY,
    id_alerta BIGINT REFERENCES app.fato_alerta_ativo(id),
    status_anterior TEXT,
    status_novo TEXT,
    comentario TEXT,
    usuario TEXT,
    data_evento TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.config_notificacao_alerta (
    id SERIAL PRIMARY KEY,
    area_responsavel TEXT NOT NULL UNIQUE,
    canal TEXT DEFAULT 'painel',
    destino TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    observacao TEXT,
    data_criacao TIMESTAMP DEFAULT NOW()
);

CREATE OR REPLACE VIEW app.vw_alertas_ativos_atual AS
SELECT
    id,
    data_referencia,
    uf,
    regiao_comercial,
    area_responsavel,
    tipo_alerta,
    severidade,
    status,
    titulo,
    mensagem,
    score_relacionado,
    recomendacao_sugerida,
    origem,
    principais_fatores,
    data_criacao,
    data_atualizacao
FROM app.fato_alerta_ativo
WHERE status IN ('ativo', 'em_analise')
ORDER BY
    CASE severidade
        WHEN 'critico' THEN 1
        WHEN 'alto' THEN 2
        WHEN 'medio' THEN 3
        ELSE 4
    END,
    data_referencia DESC,
    area_responsavel,
    regiao_comercial;

CREATE OR REPLACE VIEW app.vw_alertas_resumo_area AS
SELECT
    area_responsavel,
    COUNT(*) FILTER (WHERE status IN ('ativo', 'em_analise')) AS qtd_abertos,
    COUNT(*) FILTER (WHERE status = 'ativo') AS qtd_ativos,
    COUNT(*) FILTER (WHERE status = 'em_analise') AS qtd_em_analise,
    COUNT(*) FILTER (WHERE severidade = 'critico' AND status IN ('ativo', 'em_analise')) AS qtd_criticos,
    COUNT(*) FILTER (WHERE severidade = 'alto' AND status IN ('ativo', 'em_analise')) AS qtd_altos,
    COUNT(*) FILTER (WHERE severidade = 'medio' AND status IN ('ativo', 'em_analise')) AS qtd_medios,
    MAX(data_atualizacao) AS ultima_atualizacao
FROM app.fato_alerta_ativo
GROUP BY area_responsavel
ORDER BY qtd_criticos DESC, qtd_altos DESC, qtd_abertos DESC, area_responsavel;

CREATE OR REPLACE VIEW app.vw_alertas_resumo_tipo AS
SELECT
    tipo_alerta,
    area_responsavel,
    severidade,
    COUNT(*) AS qtd,
    AVG(score_relacionado) AS score_medio,
    MAX(data_atualizacao) AS ultima_atualizacao
FROM app.fato_alerta_ativo
WHERE status IN ('ativo', 'em_analise')
GROUP BY tipo_alerta, area_responsavel, severidade
ORDER BY qtd DESC, tipo_alerta;

CREATE OR REPLACE VIEW app.vw_alertas_historico_recente AS
SELECT
    id,
    data_referencia,
    uf,
    regiao_comercial,
    area_responsavel,
    tipo_alerta,
    severidade,
    status,
    titulo,
    score_relacionado,
    origem,
    data_criacao,
    data_atualizacao,
    data_resolucao
FROM app.fato_alerta_ativo
ORDER BY data_atualizacao DESC, id DESC;

INSERT INTO app.config_alerta_ativo (
    tipo_alerta,
    nome,
    area_responsavel,
    descricao,
    limite_alerta,
    limite_critico,
    direcao,
    ativo
)
VALUES
    ('competitividade_baixa', 'Competitividade baixa do pescado', 'Marketing', 'Pescado perde competitividade relativa contra proteínas concorrentes.', 35, 25, 'menor_pior', TRUE),
    ('pressao_custo_alta', 'Pressão de custo alta', 'Compras/Precificação', 'Grãos, farinha de peixe, dólar ou insumos pressionando custo.', 70, 85, 'maior_pior', TRUE),
    ('risco_substituicao_alto', 'Risco de substituição alto', 'Marketing/Comercial', 'Consumidor pode migrar para frango, suíno, boi ou ovos.', 65, 80, 'maior_pior', TRUE),
    ('potencial_alto_venda_baixa', 'Potencial alto e venda baixa', 'Comercial', 'Região com alto potencial populacional e baixa venda/cobertura.', 70, 85, 'maior_pior', TRUE),
    ('score_regional_baixo', 'Score regional baixo', 'Gestão Comercial', 'Região com score final baixo ou deteriorado.', 45, 35, 'menor_pior', TRUE),
    ('dados_insuficientes_potencial', 'Dados insuficientes em região promissora', 'Gestão de Dados/Comercial', 'Região promissora, mas sem vendas reais suficientes para decisão agressiva.', 70, 85, 'maior_pior', TRUE),
    ('recomendacao_correcao_mix_preco', 'Correção de mix/preço recomendada', 'Precificação/Comercial', 'Motor de recomendação indicou revisão de preço, margem, compras ou mix.', 1, 1, 'manual', TRUE)
ON CONFLICT (tipo_alerta)
DO UPDATE SET
    nome = EXCLUDED.nome,
    area_responsavel = EXCLUDED.area_responsavel,
    descricao = EXCLUDED.descricao,
    limite_alerta = EXCLUDED.limite_alerta,
    limite_critico = EXCLUDED.limite_critico,
    direcao = EXCLUDED.direcao,
    ativo = EXCLUDED.ativo;

INSERT INTO app.config_notificacao_alerta (
    area_responsavel,
    canal,
    destino,
    ativo,
    observacao
)
VALUES
    ('Comercial', 'painel', NULL, TRUE, 'Notificação visual no painel Streamlit.'),
    ('Marketing', 'painel', NULL, TRUE, 'Notificação visual no painel Streamlit.'),
    ('Marketing/Comercial', 'painel', NULL, TRUE, 'Notificação visual no painel Streamlit.'),
    ('Compras/Precificação', 'painel', NULL, TRUE, 'Notificação visual no painel Streamlit.'),
    ('Precificação/Comercial', 'painel', NULL, TRUE, 'Notificação visual no painel Streamlit.'),
    ('Gestão Comercial', 'painel', NULL, TRUE, 'Notificação visual no painel Streamlit.'),
    ('Gestão de Dados/Comercial', 'painel', NULL, TRUE, 'Notificação visual no painel Streamlit.')
ON CONFLICT (area_responsavel)
DO UPDATE SET
    canal = EXCLUDED.canal,
    destino = EXCLUDED.destino,
    ativo = EXCLUDED.ativo,
    observacao = EXCLUDED.observacao;
