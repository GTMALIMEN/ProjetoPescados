
-- ============================================================
-- Etapas 35-40 — Importações Manuais + Mercado Privado + Correlação IDC
-- ============================================================

CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS dw;

CREATE TABLE IF NOT EXISTS app.importacao_manual_log (
    id BIGSERIAL PRIMARY KEY,
    tipo_base TEXT,
    nome_arquivo TEXT,
    usuario TEXT,
    qtd_linhas INTEGER,
    qtd_linhas_validas INTEGER,
    qtd_linhas_erro INTEGER,
    status TEXT,
    mensagem TEXT,
    data_importacao TIMESTAMP DEFAULT NOW(),
    periodo_inicio DATE,
    periodo_fim DATE,
    modo_importacao TEXT
);

ALTER TABLE app.importacao_manual_log
    ADD COLUMN IF NOT EXISTS tipo_base TEXT,
    ADD COLUMN IF NOT EXISTS nome_arquivo TEXT,
    ADD COLUMN IF NOT EXISTS usuario TEXT,
    ADD COLUMN IF NOT EXISTS qtd_linhas INTEGER,
    ADD COLUMN IF NOT EXISTS qtd_linhas_validas INTEGER,
    ADD COLUMN IF NOT EXISTS qtd_linhas_erro INTEGER,
    ADD COLUMN IF NOT EXISTS status TEXT,
    ADD COLUMN IF NOT EXISTS mensagem TEXT,
    ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS periodo_inicio DATE,
    ADD COLUMN IF NOT EXISTS periodo_fim DATE,
    ADD COLUMN IF NOT EXISTS modo_importacao TEXT;

CREATE TABLE IF NOT EXISTS app.fato_mercado_privado (
    id BIGSERIAL PRIMARY KEY,
    data_competencia DATE,
    mes DATE,
    uf TEXT,
    cidade TEXT,
    microrregiao TEXT,
    categoria TEXT,
    produto TEXT,
    marca TEXT,
    ean TEXT,
    canal TEXT,
    valor_mercado NUMERIC,
    volume_mercado NUMERIC,
    preco_medio NUMERIC,
    ticket_medio NUMERIC,
    qtd_lojas NUMERIC,
    fonte TEXT DEFAULT 'Mercado privado',
    tipo_base TEXT DEFAULT 'scanntech_mercado_privado',
    arquivo_origem TEXT,
    hash_linha TEXT,
    data_importacao TIMESTAMP DEFAULT NOW()
);

ALTER TABLE app.fato_mercado_privado
    ADD COLUMN IF NOT EXISTS data_competencia DATE,
    ADD COLUMN IF NOT EXISTS mes DATE,
    ADD COLUMN IF NOT EXISTS uf TEXT,
    ADD COLUMN IF NOT EXISTS cidade TEXT,
    ADD COLUMN IF NOT EXISTS microrregiao TEXT,
    ADD COLUMN IF NOT EXISTS categoria TEXT,
    ADD COLUMN IF NOT EXISTS produto TEXT,
    ADD COLUMN IF NOT EXISTS marca TEXT,
    ADD COLUMN IF NOT EXISTS ean TEXT,
    ADD COLUMN IF NOT EXISTS canal TEXT,
    ADD COLUMN IF NOT EXISTS valor_mercado NUMERIC,
    ADD COLUMN IF NOT EXISTS volume_mercado NUMERIC,
    ADD COLUMN IF NOT EXISTS preco_medio NUMERIC,
    ADD COLUMN IF NOT EXISTS ticket_medio NUMERIC,
    ADD COLUMN IF NOT EXISTS qtd_lojas NUMERIC,
    ADD COLUMN IF NOT EXISTS fonte TEXT DEFAULT 'Mercado privado',
    ADD COLUMN IF NOT EXISTS tipo_base TEXT DEFAULT 'scanntech_mercado_privado',
    ADD COLUMN IF NOT EXISTS arquivo_origem TEXT,
    ADD COLUMN IF NOT EXISTS hash_linha TEXT,
    ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_mercado_privado_geo ON app.fato_mercado_privado (uf, microrregiao);
CREATE INDEX IF NOT EXISTS idx_mercado_privado_data ON app.fato_mercado_privado (data_competencia DESC);
CREATE INDEX IF NOT EXISTS idx_mercado_privado_categoria ON app.fato_mercado_privado (categoria, produto);
CREATE INDEX IF NOT EXISTS idx_mercado_privado_hash ON app.fato_mercado_privado (hash_linha);

CREATE TABLE IF NOT EXISTS app.fato_curva_mercado_categoria (
    id BIGSERIAL PRIMARY KEY,
    data_competencia DATE,
    mes DATE,
    uf TEXT,
    cidade TEXT,
    microrregiao TEXT,
    categoria TEXT,
    produto TEXT,
    valor_mercado NUMERIC,
    volume_mercado NUMERIC,
    preco_medio NUMERIC,
    qtd_lojas NUMERIC,
    fonte TEXT DEFAULT 'Curva mercado privada',
    arquivo_origem TEXT,
    hash_linha TEXT,
    data_importacao TIMESTAMP DEFAULT NOW()
);

ALTER TABLE app.fato_curva_mercado_categoria
    ADD COLUMN IF NOT EXISTS data_competencia DATE,
    ADD COLUMN IF NOT EXISTS mes DATE,
    ADD COLUMN IF NOT EXISTS uf TEXT,
    ADD COLUMN IF NOT EXISTS cidade TEXT,
    ADD COLUMN IF NOT EXISTS microrregiao TEXT,
    ADD COLUMN IF NOT EXISTS categoria TEXT,
    ADD COLUMN IF NOT EXISTS produto TEXT,
    ADD COLUMN IF NOT EXISTS valor_mercado NUMERIC,
    ADD COLUMN IF NOT EXISTS volume_mercado NUMERIC,
    ADD COLUMN IF NOT EXISTS preco_medio NUMERIC,
    ADD COLUMN IF NOT EXISTS qtd_lojas NUMERIC,
    ADD COLUMN IF NOT EXISTS fonte TEXT DEFAULT 'Curva mercado privada',
    ADD COLUMN IF NOT EXISTS arquivo_origem TEXT,
    ADD COLUMN IF NOT EXISTS hash_linha TEXT,
    ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_curva_mercado_geo ON app.fato_curva_mercado_categoria (uf, microrregiao);
CREATE INDEX IF NOT EXISTS idx_curva_mercado_data ON app.fato_curva_mercado_categoria (data_competencia DESC);
CREATE INDEX IF NOT EXISTS idx_curva_mercado_categoria ON app.fato_curva_mercado_categoria (categoria, produto);
CREATE INDEX IF NOT EXISTS idx_curva_mercado_hash ON app.fato_curva_mercado_categoria (hash_linha);

CREATE TABLE IF NOT EXISTS app.dim_key_account_loja (
    id BIGSERIAL PRIMARY KEY,
    grupo_key_account TEXT,
    cliente TEXT,
    cnpj TEXT,
    loja TEXT,
    endereco TEXT,
    numero TEXT,
    bairro TEXT,
    cidade TEXT,
    uf TEXT,
    cep TEXT,
    latitude NUMERIC,
    longitude NUMERIC,
    canal TEXT,
    status TEXT,
    arquivo_origem TEXT,
    hash_linha TEXT,
    data_importacao TIMESTAMP DEFAULT NOW()
);

ALTER TABLE app.dim_key_account_loja
    ADD COLUMN IF NOT EXISTS grupo_key_account TEXT,
    ADD COLUMN IF NOT EXISTS cliente TEXT,
    ADD COLUMN IF NOT EXISTS cnpj TEXT,
    ADD COLUMN IF NOT EXISTS loja TEXT,
    ADD COLUMN IF NOT EXISTS endereco TEXT,
    ADD COLUMN IF NOT EXISTS numero TEXT,
    ADD COLUMN IF NOT EXISTS bairro TEXT,
    ADD COLUMN IF NOT EXISTS cidade TEXT,
    ADD COLUMN IF NOT EXISTS uf TEXT,
    ADD COLUMN IF NOT EXISTS cep TEXT,
    ADD COLUMN IF NOT EXISTS latitude NUMERIC,
    ADD COLUMN IF NOT EXISTS longitude NUMERIC,
    ADD COLUMN IF NOT EXISTS canal TEXT,
    ADD COLUMN IF NOT EXISTS status TEXT,
    ADD COLUMN IF NOT EXISTS arquivo_origem TEXT,
    ADD COLUMN IF NOT EXISTS hash_linha TEXT,
    ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_key_account_geo ON app.dim_key_account_loja (uf, cidade);
CREATE INDEX IF NOT EXISTS idx_key_account_grupo ON app.dim_key_account_loja (grupo_key_account);
CREATE INDEX IF NOT EXISTS idx_key_account_hash ON app.dim_key_account_loja (hash_linha);

-- Views de mercado privado, consolidando Scanntech/mercado privado + curva privada.
CREATE OR REPLACE VIEW app.vw_mercado_privado_union AS
SELECT
    'scanntech_mercado_privado' AS origem_base,
    data_competencia,
    mes,
    uf,
    cidade,
    microrregiao,
    categoria,
    produto,
    marca,
    ean,
    canal,
    valor_mercado,
    volume_mercado,
    preco_medio,
    ticket_medio,
    qtd_lojas,
    fonte,
    arquivo_origem,
    data_importacao
FROM app.fato_mercado_privado
UNION ALL
SELECT
    'curva_mercado_categoria' AS origem_base,
    data_competencia,
    mes,
    uf,
    cidade,
    microrregiao,
    categoria,
    produto,
    NULL::TEXT AS marca,
    NULL::TEXT AS ean,
    NULL::TEXT AS canal,
    valor_mercado,
    volume_mercado,
    preco_medio,
    NULL::NUMERIC AS ticket_medio,
    qtd_lojas,
    fonte,
    arquivo_origem,
    data_importacao
FROM app.fato_curva_mercado_categoria;

DROP VIEW IF EXISTS app.vw_mercado_privado_resumo CASCADE;

CREATE OR REPLACE VIEW app.vw_mercado_privado_resumo AS
SELECT
    origem_base,
    COALESCE(fonte, origem_base) AS fonte,
    COUNT(*) AS qtd_registros,
    COUNT(DISTINCT uf) AS qtd_ufs,
    COUNT(DISTINCT COALESCE(microrregiao, cidade)) AS qtd_regioes,
    COUNT(DISTINCT categoria) AS qtd_categorias,
    COUNT(DISTINCT produto) AS qtd_produtos,
    MIN(data_competencia) AS primeira_data,
    MAX(data_competencia) AS ultima_data,
    SUM(valor_mercado) AS valor_mercado_total,
    SUM(volume_mercado) AS volume_mercado_total,
    CASE WHEN SUM(volume_mercado) > 0 THEN SUM(valor_mercado) / SUM(volume_mercado) ELSE NULL END AS preco_medio_ponderado,
    SUM(qtd_lojas) AS qtd_lojas_total
FROM app.vw_mercado_privado_union
GROUP BY origem_base, COALESCE(fonte, origem_base);

CREATE OR REPLACE VIEW app.vw_mercado_privado_curva_mensal AS
SELECT
    mes,
    uf,
    COALESCE(microrregiao, 'Sem microrregião') AS microrregiao,
    COALESCE(categoria, 'Sem categoria') AS categoria,
    COALESCE(produto, 'Sem produto') AS produto,
    SUM(valor_mercado) AS valor_mercado,
    SUM(volume_mercado) AS volume_mercado,
    CASE WHEN SUM(volume_mercado) > 0 THEN SUM(valor_mercado) / SUM(volume_mercado) ELSE AVG(preco_medio) END AS preco_medio,
    SUM(qtd_lojas) AS qtd_lojas
FROM app.vw_mercado_privado_union
GROUP BY mes, uf, COALESCE(microrregiao, 'Sem microrregião'), COALESCE(categoria, 'Sem categoria'), COALESCE(produto, 'Sem produto');

CREATE OR REPLACE VIEW app.vw_mercado_privado_micro AS
SELECT
    uf AS estado,
    COALESCE(microrregiao, 'Sem microrregião') AS microrregiao,
    COALESCE(categoria, 'Todas') AS categoria,
    SUM(valor_mercado) AS valor_mercado,
    SUM(volume_mercado) AS volume_mercado,
    CASE WHEN SUM(volume_mercado) > 0 THEN SUM(valor_mercado) / SUM(volume_mercado) ELSE AVG(preco_medio) END AS preco_medio,
    SUM(qtd_lojas) AS qtd_lojas,
    MIN(data_competencia) AS primeira_data,
    MAX(data_competencia) AS ultima_data
FROM app.vw_mercado_privado_union
GROUP BY uf, COALESCE(microrregiao, 'Sem microrregião'), COALESCE(categoria, 'Todas');

CREATE OR REPLACE VIEW app.vw_key_account_resumo AS
SELECT
    uf AS estado,
    cidade,
    COUNT(*) AS qtd_lojas_key_account,
    COUNT(DISTINCT grupo_key_account) AS qtd_grupos_key_account,
    COUNT(DISTINCT cliente) AS qtd_clientes_key_account,
    COUNT(*) FILTER (WHERE latitude IS NOT NULL AND longitude IS NOT NULL) AS lojas_com_coordenada,
    MAX(data_importacao) AS ultima_importacao
FROM app.dim_key_account_loja
GROUP BY uf, cidade;

CREATE OR REPLACE VIEW app.vw_importacoes_manuais_recentes AS
SELECT
    id,
    tipo_base,
    nome_arquivo,
    usuario,
    qtd_linhas,
    qtd_linhas_validas,
    qtd_linhas_erro,
    status,
    mensagem,
    data_importacao,
    periodo_inicio,
    periodo_fim,
    modo_importacao
FROM app.importacao_manual_log
ORDER BY data_importacao DESC, id DESC;
