-- ============================================================
-- Radar Pescados IA — Modelos iniciais
-- Etapa 1: Fundação + BCB
-- Correção: removidas colunas GENERATED ALWAYS AS para compatibilidade.
-- O PostgreSQL exige expressão imutável para coluna gerada, e casts como data::TEXT
-- podem falhar. Para a etapa 1, usamos chaves naturais com colunas NOT NULL DEFAULT ''.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ------------------------------------------------------------
-- ETL run
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.etl_run (
    run_id UUID PRIMARY KEY,
    fonte TEXT NOT NULL,
    tipo_execucao TEXT,
    ambiente TEXT DEFAULT 'local'
        CHECK (ambiente IN ('local', 'dev', 'producao')),
    status TEXT CHECK (
        status IN (
            'INICIADO',
            'SUCESSO',
            'ERRO_API',
            'ERRO_SCHEMA',
            'ERRO_VALIDACAO',
            'SEM_DADOS',
            'PARCIAL',
            'CANCELADO'
        )
    ),
    iniciado_em TIMESTAMP DEFAULT NOW(),
    finalizado_em TIMESTAMP,
    mensagem TEXT
);

-- ------------------------------------------------------------
-- RAW padrão
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.api_payload (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES app.etl_run(run_id),
    fonte TEXT NOT NULL,
    endpoint TEXT,
    parametros JSONB,
    payload JSONB,
    status_http INT,
    data_referencia_inicio DATE,
    data_referencia_fim DATE,
    coletado_em TIMESTAMP DEFAULT NOW()
);

-- ------------------------------------------------------------
-- Controle de carga
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.etl_controle_carga (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES app.etl_run(run_id),
    fonte TEXT NOT NULL,
    indicador TEXT NOT NULL,
    codigo_serie TEXT,
    data_inicio_solicitada DATE,
    data_inicio_disponivel DATE,
    data_fim_disponivel DATE,
    ultima_data_coletada DATE,
    status TEXT CHECK (
        status IN (
            'SUCESSO',
            'ERRO_API',
            'ERRO_SCHEMA',
            'ERRO_VALIDACAO',
            'SEM_DADOS',
            'PARCIAL'
        )
    ),
    mensagem TEXT,
    qtd_registros INT,
    qtd_raw INT,
    qtd_staging INT,
    qtd_dw INT,
    qtd_rejeitados INT,
    tempo_execucao_segundos NUMERIC,
    data_execucao TIMESTAMP DEFAULT NOW()
);

-- ------------------------------------------------------------
-- Data Quality
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.data_quality_resultado (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID REFERENCES app.etl_run(run_id),
    fonte TEXT,
    tabela TEXT,
    regra TEXT,
    status TEXT CHECK (status IN ('OK', 'AVISO', 'ERRO')),
    qtd_linhas_afetadas INT,
    detalhe TEXT,
    data_validacao TIMESTAMP DEFAULT NOW()
);

-- ------------------------------------------------------------
-- Catálogo de fontes
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.catalogo_fonte (
    id SERIAL PRIMARY KEY,
    fonte TEXT NOT NULL,
    indicador TEXT NOT NULL,
    codigo_serie TEXT DEFAULT '',
    endpoint TEXT,
    periodicidade TEXT,
    data_inicio_padrao DATE,
    ativo BOOLEAN DEFAULT TRUE,
    prioridade INT,
    observacao TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_catalogo_fonte
ON app.catalogo_fonte (
    fonte,
    indicador,
    COALESCE(codigo_serie, '')
);

-- ------------------------------------------------------------
-- Staging BCB
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.bcb_series (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID REFERENCES app.etl_run(run_id),
    data DATE,
    codigo_serie TEXT,
    indicador TEXT,
    valor NUMERIC,
    unidade TEXT,
    processado_em TIMESTAMP DEFAULT NOW()
);

-- ------------------------------------------------------------
-- Fato série histórica
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.fato_serie_historica (
    id BIGSERIAL PRIMARY KEY,
    data DATE NOT NULL,
    fonte TEXT NOT NULL,
    codigo_serie TEXT NOT NULL DEFAULT '',
    indicador TEXT NOT NULL,
    categoria TEXT,
    subcategoria TEXT,
    pais TEXT NOT NULL DEFAULT 'Brasil',
    uf TEXT NOT NULL DEFAULT '',
    municipio TEXT NOT NULL DEFAULT '',
    regiao_ibge TEXT NOT NULL DEFAULT '',
    regiao_comercial TEXT NOT NULL DEFAULT '',
    valor NUMERIC,
    unidade TEXT,
    periodicidade TEXT,
    data_inicio_fonte DATE,
    data_fim_fonte DATE,
    data_coleta TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_fato_serie_historica_natural UNIQUE (
        data,
        fonte,
        codigo_serie,
        indicador,
        pais,
        uf,
        municipio,
        regiao_ibge,
        regiao_comercial
    )
);

-- ------------------------------------------------------------
-- Dimensões e fatos futuras, ainda sem uso na Etapa 1
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_cliente (
    id_cliente SERIAL PRIMARY KEY,
    codigo_cliente TEXT,
    cliente TEXT,
    grupo_cliente TEXT,
    perfil_cliente TEXT,
    cpf_cnpj_hash TEXT,
    uf TEXT,
    municipio TEXT,
    codigo_ibge TEXT,
    data_atualizacao TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_cliente_codigo
ON dw.dim_cliente (codigo_cliente)
WHERE codigo_cliente IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_cliente_cpf_cnpj_hash
ON dw.dim_cliente (cpf_cnpj_hash)
WHERE cpf_cnpj_hash IS NOT NULL;

CREATE TABLE IF NOT EXISTS dw.dim_produto (
    id_produto SERIAL PRIMARY KEY,
    codigo_produto TEXT,
    produto TEXT,
    grupo_produto TEXT,
    proteina TEXT,
    categoria TEXT,
    origem TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_produto_codigo
ON dw.dim_produto (codigo_produto)
WHERE codigo_produto IS NOT NULL;

CREATE TABLE IF NOT EXISTS dw.dim_vendedor (
    id_vendedor SERIAL PRIMARY KEY,
    codigo_vendedor TEXT,
    vendedor TEXT,
    equipe TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    data_inicio DATE DEFAULT CURRENT_DATE,
    data_fim DATE,
    registro_atual BOOLEAN DEFAULT TRUE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_vendedor_codigo_atual
ON dw.dim_vendedor (codigo_vendedor)
WHERE registro_atual = TRUE AND codigo_vendedor IS NOT NULL;

CREATE TABLE IF NOT EXISTS dw.dim_canal (
    id_canal SERIAL PRIMARY KEY,
    canal TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS dw.fato_vendas (
    id_venda BIGSERIAL PRIMARY KEY,
    codigo_origem TEXT,
    numero_documento TEXT,
    numero_item TEXT,
    numero_pedido TEXT,
    data DATE NOT NULL,
    id_cliente INT REFERENCES dw.dim_cliente(id_cliente),
    id_produto INT REFERENCES dw.dim_produto(id_produto),
    id_vendedor INT REFERENCES dw.dim_vendedor(id_vendedor),
    id_canal INT REFERENCES dw.dim_canal(id_canal),
    codigo_ibge TEXT,
    uf TEXT,
    municipio TEXT,
    regiao_comercial TEXT,
    valor_venda NUMERIC,
    volume_kg NUMERIC,
    quantidade NUMERIC,
    data_carga TIMESTAMP DEFAULT NOW()
);

-- Índice não único provisório. A chave única de vendas será fechada quando
-- a base interna real for carregada e confirmarmos os campos de documento/item.
CREATE INDEX IF NOT EXISTS idx_fato_vendas_documento
ON dw.fato_vendas (codigo_origem, numero_documento, numero_item, numero_pedido, data);

CREATE OR REPLACE VIEW app.vw_vendas_analitica AS
SELECT
    fv.id_venda,
    fv.codigo_origem,
    fv.numero_documento,
    fv.numero_item,
    fv.numero_pedido,
    fv.data,
    fv.uf,
    fv.municipio,
    fv.codigo_ibge,
    fv.regiao_comercial,
    dc.id_cliente,
    dc.codigo_cliente,
    dc.cliente,
    dc.grupo_cliente,
    dc.perfil_cliente,
    dp.id_produto,
    dp.codigo_produto,
    dp.produto,
    dp.grupo_produto,
    dp.proteina,
    dp.categoria,
    dp.origem,
    dv.id_vendedor,
    dv.codigo_vendedor,
    dv.vendedor,
    dv.equipe,
    dcan.id_canal,
    dcan.canal,
    fv.valor_venda,
    fv.volume_kg,
    fv.quantidade,
    CASE
        WHEN fv.quantidade IS NULL OR fv.quantidade = 0 THEN NULL
        ELSE fv.valor_venda / fv.quantidade
    END AS ticket_medio_quantidade,
    CASE
        WHEN fv.volume_kg IS NULL OR fv.volume_kg = 0 THEN NULL
        ELSE fv.valor_venda / fv.volume_kg
    END AS preco_medio_kg,
    fv.data_carga
FROM dw.fato_vendas fv
LEFT JOIN dw.dim_cliente dc ON fv.id_cliente = dc.id_cliente
LEFT JOIN dw.dim_produto dp ON fv.id_produto = dp.id_produto
LEFT JOIN dw.dim_vendedor dv ON fv.id_vendedor = dv.id_vendedor
LEFT JOIN dw.dim_canal dcan ON fv.id_canal = dcan.id_canal;
