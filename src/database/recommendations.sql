-- ============================================================
-- Radar Pescados IA — Etapa 6
-- Recomendações Comerciais
-- ============================================================

CREATE TABLE IF NOT EXISTS app.config_roi_acao (
    id SERIAL PRIMARY KEY,
    tipo_recomendacao TEXT NOT NULL,
    custo_mensal_estimado NUMERIC,
    ganho_multiplo_estimado NUMERIC,
    observacao TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT NOW(),
    UNIQUE (tipo_recomendacao)
);

CREATE TABLE IF NOT EXISTS app.fato_recomendacao (
    id BIGSERIAL PRIMARY KEY,
    id_score BIGINT REFERENCES app.fato_score_regional(id),
    data_referencia DATE NOT NULL,
    pais TEXT NOT NULL DEFAULT 'Brasil',
    uf TEXT NOT NULL DEFAULT '',
    regiao_comercial TEXT NOT NULL DEFAULT '',
    municipio TEXT NOT NULL DEFAULT '',
    produto TEXT NOT NULL DEFAULT '',
    proteina TEXT NOT NULL DEFAULT '',
    cenario_1_10 INT CHECK (cenario_1_10 BETWEEN 1 AND 10),
    tipo_recomendacao TEXT,
    acao_sugerida TEXT,
    justificativa TEXT,
    confianca NUMERIC CHECK (confianca BETWEEN 0 AND 100),
    impacto_estimado NUMERIC,
    roi_estimado NUMERIC,
    score_vendedor NUMERIC CHECK (score_vendedor BETWEEN 0 AND 100),
    score_promotor NUMERIC CHECK (score_promotor BETWEEN 0 AND 100),
    score_campanha NUMERIC CHECK (score_campanha BETWEEN 0 AND 100),
    status TEXT DEFAULT 'pendente',
    principais_fatores JSONB,
    data_criacao TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_fato_recomendacao_natural UNIQUE (
        data_referencia, pais, uf, regiao_comercial, municipio, produto, proteina, tipo_recomendacao
    )
);

CREATE INDEX IF NOT EXISTS idx_recomendacao_data
ON app.fato_recomendacao (data_referencia);

CREATE INDEX IF NOT EXISTS idx_recomendacao_uf_tipo
ON app.fato_recomendacao (uf, tipo_recomendacao, data_referencia);

CREATE INDEX IF NOT EXISTS idx_recomendacao_status
ON app.fato_recomendacao (status);

CREATE INDEX IF NOT EXISTS idx_recomendacao_score
ON app.fato_recomendacao (id_score);

CREATE TABLE IF NOT EXISTS app.feedback_recomendacao (
    id BIGSERIAL PRIMARY KEY,
    id_recomendacao BIGINT REFERENCES app.fato_recomendacao(id),
    usuario_login TEXT,
    feedback TEXT CHECK (feedback IN ('positivo', 'negativo', 'neutro')),
    executada BOOLEAN,
    resultado_observado TEXT,
    observacao TEXT,
    data_feedback TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_recomendacao
ON app.feedback_recomendacao (id_recomendacao, data_feedback);

DROP MATERIALIZED VIEW IF EXISTS app.mv_recomendacao_atual;

CREATE MATERIALIZED VIEW app.mv_recomendacao_atual AS
WITH ranked AS (
    SELECT
        r.*,
        ROW_NUMBER() OVER (
            PARTITION BY r.uf, r.regiao_comercial, r.municipio, r.produto, r.proteina
            ORDER BY r.data_criacao DESC, r.data_referencia DESC, r.id DESC
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
    status,
    principais_fatores,
    data_criacao
FROM ranked
WHERE rn = 1;

CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_recomendacao_atual
ON app.mv_recomendacao_atual (uf, regiao_comercial, municipio, produto, proteina);

INSERT INTO app.config_roi_acao (
    tipo_recomendacao, custo_mensal_estimado, ganho_multiplo_estimado, observacao, ativo
)
VALUES
    ('adicionar_vendedor', 6000, 4.00, 'Custo estimado mensal de vendedor + potencial de incremento bruto', TRUE),
    ('adicionar_promotor', 4000, 3.50, 'Custo estimado mensal de promotor + execução em loja', TRUE),
    ('campanha_marketing', 2500, 3.00, 'Campanha comercial/marketing regional', TRUE),
    ('monitorar', 0, 0.00, 'Sem custo direto; acompanhar indicadores', TRUE),
    ('corrigir_mix_preco', 0, 0.00, 'Ação corretiva de mix/preço; custo depende do caso', TRUE),
    ('aguardar_dados_reais', 0, 0.00, 'Base insuficiente; aguardar carga real de vendas', TRUE)
ON CONFLICT (tipo_recomendacao)
DO UPDATE SET
    custo_mensal_estimado = EXCLUDED.custo_mensal_estimado,
    ganho_multiplo_estimado = EXCLUDED.ganho_multiplo_estimado,
    observacao = EXCLUDED.observacao,
    ativo = TRUE;
