-- ============================================================
-- CEPEA Manual Oficial — tabela histórica e integração DW
-- ============================================================
-- Objetivo:
--   Permitir importar manualmente valores da base CEPEA nova preenchida/conferida.
--   CEPEA proxy, scraper e automático foram desativados no app.
--   A tela e os gráficos usam somente esta tabela manual auditável.
--
-- Regra de governança:
--   - CEPEA manual oficial: subcategoria = 'oficial_arquivo_manual'
--   - CEPEA proxy/antigo/scraper: não deve ser usado nem exibido no app.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS dw;

CREATE TABLE IF NOT EXISTS app.fato_cepea_tilapia_manual (
    id BIGSERIAL PRIMARY KEY,
    chave_registro TEXT,
    hash_linha TEXT,
    data_coleta TIMESTAMP DEFAULT NOW(),
    data_inicio_periodo DATE,
    data_fim_periodo DATE NOT NULL,
    periodo_original TEXT,
    produto TEXT NOT NULL DEFAULT 'Tilápia',
    regiao_cepea TEXT NOT NULL,
    uf TEXT,
    preco_ajustado NUMERIC,
    preco_rs_kg NUMERIC NOT NULL,
    variacao_semana_pct NUMERIC,
    unidade TEXT DEFAULT 'R$/kg',
    fonte TEXT DEFAULT 'CEPEA',
    tipo_fonte TEXT DEFAULT 'oficial_arquivo_manual',
    url_fonte TEXT DEFAULT 'https://www.cepea.org.br/br/indicador/tilapia.aspx',
    arquivo_origem TEXT,
    usuario_carga TEXT,
    observacao TEXT,
    criado_em TIMESTAMP DEFAULT NOW()
);

ALTER TABLE app.fato_cepea_tilapia_manual
    ADD COLUMN IF NOT EXISTS chave_registro TEXT,
    ADD COLUMN IF NOT EXISTS hash_linha TEXT,
    ADD COLUMN IF NOT EXISTS data_inicio_periodo DATE,
    ADD COLUMN IF NOT EXISTS data_fim_periodo DATE,
    ADD COLUMN IF NOT EXISTS periodo_original TEXT,
    ADD COLUMN IF NOT EXISTS produto TEXT DEFAULT 'Tilápia',
    ADD COLUMN IF NOT EXISTS regiao_cepea TEXT,
    ADD COLUMN IF NOT EXISTS uf TEXT,
    ADD COLUMN IF NOT EXISTS preco_ajustado NUMERIC,
    ADD COLUMN IF NOT EXISTS preco_rs_kg NUMERIC,
    ADD COLUMN IF NOT EXISTS variacao_semana_pct NUMERIC,
    ADD COLUMN IF NOT EXISTS unidade TEXT DEFAULT 'R$/kg',
    ADD COLUMN IF NOT EXISTS fonte TEXT DEFAULT 'CEPEA',
    ADD COLUMN IF NOT EXISTS tipo_fonte TEXT DEFAULT 'oficial_arquivo_manual',
    ADD COLUMN IF NOT EXISTS url_fonte TEXT DEFAULT 'https://www.cepea.org.br/br/indicador/tilapia.aspx',
    ADD COLUMN IF NOT EXISTS arquivo_origem TEXT,
    ADD COLUMN IF NOT EXISTS usuario_carga TEXT,
    ADD COLUMN IF NOT EXISTS observacao TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_fato_cepea_tilapia_manual_chave_registro'
    ) THEN
        ALTER TABLE app.fato_cepea_tilapia_manual
        ADD CONSTRAINT uq_fato_cepea_tilapia_manual_chave_registro UNIQUE (chave_registro);
    END IF;
EXCEPTION
    WHEN duplicate_table THEN NULL;
    WHEN duplicate_object THEN NULL;
END $$;

CREATE INDEX IF NOT EXISTS idx_cepea_manual_data_regiao
ON app.fato_cepea_tilapia_manual (data_fim_periodo DESC, regiao_cepea);

CREATE INDEX IF NOT EXISTS idx_cepea_manual_produto
ON app.fato_cepea_tilapia_manual (produto, data_fim_periodo DESC);

CREATE OR REPLACE VIEW app.vw_cepea_tilapia_manual_historico AS
SELECT
    data_fim_periodo AS data,
    data_inicio_periodo,
    data_fim_periodo,
    periodo_original,
    fonte,
    tipo_fonte AS subcategoria,
    produto,
    uf,
    regiao_cepea AS regiao,
    COALESCE(preco_ajustado, preco_rs_kg) AS valor,
    preco_ajustado,
    unidade,
    variacao_semana_pct,
    url_fonte,
    arquivo_origem,
    usuario_carga,
    observacao,
    data_coleta
FROM app.fato_cepea_tilapia_manual
ORDER BY data_fim_periodo DESC, regiao_cepea;

-- Diagnóstico simples para conferência no app/scripts.
CREATE OR REPLACE VIEW app.vw_cepea_tilapia_manual_resumo AS
SELECT
    produto,
    uf,
    regiao_cepea AS regiao,
    COUNT(*) AS qtd_registros,
    MIN(data_fim_periodo) AS primeira_data,
    MAX(data_fim_periodo) AS ultima_data,
    AVG(COALESCE(preco_ajustado, preco_rs_kg)) AS preco_medio,
    MIN(COALESCE(preco_ajustado, preco_rs_kg)) AS preco_minimo,
    MAX(COALESCE(preco_ajustado, preco_rs_kg)) AS preco_maximo,
    MAX(data_coleta) AS ultima_carga
FROM app.fato_cepea_tilapia_manual
GROUP BY produto, uf, regiao_cepea
ORDER BY produto, uf, regiao_cepea;
