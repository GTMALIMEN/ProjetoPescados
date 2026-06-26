-- ============================================================
-- Etapa 41 — Persistência correta, bases manuais, APIs e IDC planejado
-- ============================================================

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS dw;
CREATE SCHEMA IF NOT EXISTS app;

-- Raw API: garante que todas as coletas externas tenham lugar para payload/metadados.
CREATE TABLE IF NOT EXISTS raw.api_payload (
    id BIGSERIAL PRIMARY KEY,
    run_id TEXT,
    fonte TEXT NOT NULL,
    endpoint TEXT,
    parametros JSONB,
    payload JSONB,
    status_http INTEGER,
    coletado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_raw_api_payload_fonte_data
ON raw.api_payload (fonte, coletado_em DESC);

-- Log único de importação manual por upload na interface.
CREATE TABLE IF NOT EXISTS app.importacao_manual_log (
    id BIGSERIAL PRIMARY KEY,
    tipo_importacao TEXT NOT NULL,
    arquivo TEXT,
    usuario TEXT,
    modo_importacao TEXT,
    status TEXT NOT NULL,
    registros_lidos INTEGER DEFAULT 0,
    registros_processados INTEGER DEFAULT 0,
    registros_rejeitados INTEGER DEFAULT 0,
    periodo_inicio DATE,
    periodo_fim DATE,
    detalhe TEXT,
    executado_em TIMESTAMP DEFAULT NOW()
);

ALTER TABLE app.importacao_manual_log
    ADD COLUMN IF NOT EXISTS usuario TEXT,
    ADD COLUMN IF NOT EXISTS modo_importacao TEXT,
    ADD COLUMN IF NOT EXISTS periodo_inicio DATE,
    ADD COLUMN IF NOT EXISTS periodo_fim DATE;

CREATE INDEX IF NOT EXISTS idx_importacao_manual_log_tipo_data
ON app.importacao_manual_log (tipo_importacao, executado_em DESC);

-- Mercado privado / Scanntech / Total mercado.
CREATE TABLE IF NOT EXISTS app.fato_mercado_privado (
    id BIGSERIAL PRIMARY KEY,
    data_competencia DATE NOT NULL,
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
    qtd_lojas NUMERIC,
    fonte TEXT DEFAULT 'manual_upload',
    fonte_arquivo TEXT,
    hash_linha TEXT UNIQUE,
    data_importacao TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mercado_privado_periodo_geo
ON app.fato_mercado_privado (data_competencia, uf, microrregiao);

CREATE INDEX IF NOT EXISTS idx_mercado_privado_categoria_produto
ON app.fato_mercado_privado (categoria, produto);

-- Curva de mercado produto/categoria separada quando vier em arquivo próprio.
CREATE TABLE IF NOT EXISTS app.fato_curva_mercado_categoria (
    id BIGSERIAL PRIMARY KEY,
    data_competencia DATE NOT NULL,
    uf TEXT,
    cidade TEXT,
    microrregiao TEXT,
    categoria TEXT,
    produto TEXT,
    valor NUMERIC,
    volume NUMERIC,
    preco_medio NUMERIC,
    fonte TEXT DEFAULT 'manual_upload',
    fonte_arquivo TEXT,
    hash_linha TEXT UNIQUE,
    data_importacao TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_curva_mercado_periodo_geo
ON app.fato_curva_mercado_categoria (data_competencia, uf, microrregiao);

-- Key account / lojas.
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
    fonte_arquivo TEXT,
    hash_linha TEXT UNIQUE,
    data_importacao TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_key_account_geo
ON app.dim_key_account_loja (uf, cidade);


-- Compatibilidade: cria bases manuais antigas caso a sequência de scripts não tenha rodado.
CREATE TABLE IF NOT EXISTS app.fato_ceagesp_pescados (
    id BIGSERIAL PRIMARY KEY,
    chave_registro TEXT UNIQUE,
    data_coleta TIMESTAMP DEFAULT NOW(),
    data_referencia DATE,
    categoria TEXT DEFAULT 'Pescados',
    produto TEXT,
    classificacao TEXT,
    unidade TEXT,
    preco_minimo NUMERIC,
    preco_comum NUMERIC,
    preco_maximo NUMERIC,
    fonte TEXT DEFAULT 'CEAGESP',
    url_fonte TEXT,
    hash_carga TEXT,
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.fato_compra_manual (
    id BIGSERIAL PRIMARY KEY,
    data DATE,
    mes DATE,
    fornecedor TEXT,
    marca TEXT,
    produto TEXT,
    categoria TEXT,
    preco_compra NUMERIC,
    quantidade_comprada NUMERIC,
    unidade TEXT,
    observacao TEXT,
    data_carga TIMESTAMP DEFAULT NOW(),
    fonte_arquivo TEXT,
    hash_linha TEXT
);

CREATE TABLE IF NOT EXISTS app.fato_previa_vendedores (
    id BIGSERIAL PRIMARY KEY,
    vendedor TEXT,
    produto TEXT,
    preco NUMERIC,
    data_venda DATE,
    quantidade_vendida NUMERIC,
    receita_total NUMERIC,
    cliente TEXT,
    regiao TEXT,
    observacao TEXT,
    data_carga TIMESTAMP DEFAULT NOW(),
    fonte TEXT DEFAULT 'manual',
    hash_linha TEXT
);

CREATE TABLE IF NOT EXISTS app.fato_receita_manual_expansao (
    id BIGSERIAL PRIMARY KEY,
    parceiro TEXT,
    cidade TEXT,
    estado TEXT,
    data_competencia DATE,
    mes DATE,
    grupo_produto TEXT,
    categoria_pescado TEXT,
    vlr_total_liquido NUMERIC,
    fonte_arquivo TEXT,
    hash_linha TEXT,
    data_carga TIMESTAMP DEFAULT NOW()
);

-- Garante colunas de hash/fonte nas bases manuais antigas.
ALTER TABLE app.fato_compra_manual
    ADD COLUMN IF NOT EXISTS fonte_arquivo TEXT,
    ADD COLUMN IF NOT EXISTS hash_linha TEXT,
    ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS uq_compra_manual_hash
<<<<<<< HEAD
ON app.fato_compra_manual (hash_linha);
=======
ON app.fato_compra_manual (hash_linha)
WHERE hash_linha IS NOT NULL;
>>>>>>> f755249488d880ab9c85f5f8580ef22c3a215cbf

ALTER TABLE app.fato_previa_vendedores
    ADD COLUMN IF NOT EXISTS fonte_arquivo TEXT,
    ADD COLUMN IF NOT EXISTS hash_linha TEXT,
    ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS uq_previa_vendedores_hash
<<<<<<< HEAD
ON app.fato_previa_vendedores (hash_linha);
=======
ON app.fato_previa_vendedores (hash_linha)
WHERE hash_linha IS NOT NULL;
>>>>>>> f755249488d880ab9c85f5f8580ef22c3a215cbf

ALTER TABLE app.fato_receita_manual_expansao
    ADD COLUMN IF NOT EXISTS fonte_arquivo TEXT,
    ADD COLUMN IF NOT EXISTS hash_linha TEXT,
    ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS uq_receita_manual_exp_hash
<<<<<<< HEAD
ON app.fato_receita_manual_expansao (hash_linha);
=======
ON app.fato_receita_manual_expansao (hash_linha)
WHERE hash_linha IS NOT NULL;
>>>>>>> f755249488d880ab9c85f5f8580ef22c3a215cbf

ALTER TABLE app.fato_ceagesp_pescados
    ADD COLUMN IF NOT EXISTS fonte_arquivo TEXT,
    ADD COLUMN IF NOT EXISTS hash_linha TEXT,
    ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS uq_ceagesp_hash
<<<<<<< HEAD
ON app.fato_ceagesp_pescados (hash_linha);
=======
ON app.fato_ceagesp_pescados (hash_linha)
WHERE hash_linha IS NOT NULL;
>>>>>>> f755249488d880ab9c85f5f8580ef22c3a215cbf

-- Preenche todos os campos automáticos possíveis sem mexer nas bases manuais.
-- Onde não existe fonte oficial carregada, grava proxy claramente identificado.
UPDATE app.fato_expansao_municipio
SET
    pib_per_capita = CASE
        WHEN pib_per_capita IS NULL AND populacao IS NOT NULL AND populacao > 0 AND pib IS NOT NULL THEN pib / populacao
        ELSE pib_per_capita
    END,
    renda_media = renda_media,
    fonte_renda = COALESCE(fonte_renda, 'Pendente: IBGE Censo 2022/POF oficial'),
    pct_masculina = pct_masculina,
    pct_feminina = pct_feminina,
    pct_0_14 = pct_0_14,
    pct_15_29 = pct_15_29,
    pct_30_44 = pct_30_44,
    pct_45_59 = pct_45_59,
    pct_60_plus = pct_60_plus,
    renda_classe_a = renda_classe_a,
    renda_classe_b = renda_classe_b,
    renda_classe_c = renda_classe_c,
    renda_classe_de = renda_classe_de,
    fonte_demografia = COALESCE(fonte_demografia, 'Pendente: IBGE Censo 2022 sexo/faixa etária oficial'),
    fonte_pdv = COALESCE(fonte_pdv, 'PDV proxy automático/estimado até base oficial'),
    supermercados = COALESCE(supermercados, 0),
    restaurantes = COALESCE(restaurantes, 0),
    peixarias = COALESCE(peixarias, 0),
    outros_pdv = COALESCE(outros_pdv, 0),
    status_dados = CASE
        WHEN populacao IS NOT NULL AND pib IS NOT NULL AND idh IS NOT NULL THEN 'ok_automatico_completo'
        WHEN populacao IS NOT NULL AND pib IS NOT NULL THEN 'ok_automatico_sem_idh'
        ELSE COALESCE(status_dados, 'parcial')
    END,
    data_atualizacao = NOW()
WHERE uf IN ('MG','SP','RJ','ES');

-- View central: IDC planejado com TODOS os fatores automáticos/proxy marcados.
DROP VIEW IF EXISTS app.vw_idc_completo_atual CASCADE;

CREATE OR REPLACE VIEW app.vw_idc_completo_atual AS
WITH base AS (
    SELECT
        e.codigo_ibge,
        e.uf AS estado,
        e.nome_uf,
        e.municipio,
        COALESCE(e.microrregiao, 'Sem microrregião') AS microrregiao,
        COALESCE(e.regiao_comercial, e.mesorregiao, e.microrregiao, 'Sem região') AS regiao_economica,
        e.populacao,
        e.pib,
        CASE WHEN e.pib_per_capita IS NOT NULL THEN e.pib_per_capita
             WHEN e.populacao > 0 AND e.pib IS NOT NULL THEN e.pib / e.populacao
             ELSE NULL END AS pib_per_capita,
        e.idh,
        e.renda_media AS renda_media,
        e.pct_feminina AS pct_feminina,
        e.pct_masculina AS pct_masculina,
        COALESCE(e.supermercados,0) AS supermercados,
        COALESCE(e.restaurantes,0) AS restaurantes,
        COALESCE(e.peixarias,0) AS peixarias,
        COALESCE(e.outros_pdv,0) AS outros_pdv,
        COALESCE(e.supermercados,0) + COALESCE(e.restaurantes,0) + COALESCE(e.peixarias,0) + COALESCE(e.outros_pdv,0) AS total_pdv,
        e.fonte_populacao,
        e.fonte_pib,
        e.fonte_idh,
        COALESCE(e.fonte_renda, 'Pendente: IBGE Censo 2022/POF oficial') AS fonte_renda,
        COALESCE(e.fonte_demografia, 'Pendente: IBGE Censo 2022 sexo/faixa etária oficial') AS fonte_demografia,
        COALESCE(e.fonte_pdv, 'PDV proxy automático/estimado') AS fonte_pdv,
        e.data_atualizacao
    FROM app.vw_expansao_municipio e
    WHERE e.uf IN ('MG','SP','RJ','ES')
), agg AS (
    SELECT
        estado,
        microrregiao,
        MAX(regiao_economica) AS regiao_economica,
        SUM(populacao) AS populacao,
        SUM(pib) AS pib,
        AVG(pib_per_capita) AS pib_per_capita,
        AVG(idh) AS idh,
        AVG(renda_media) AS renda_media,
        AVG(pct_feminina) AS pct_feminina,
        AVG(pct_masculina) AS pct_masculina,
        SUM(supermercados) AS supermercados,
        SUM(restaurantes) AS restaurantes,
        SUM(peixarias) AS peixarias,
        SUM(outros_pdv) AS outros_pdv,
        SUM(total_pdv) AS total_pdv,
        COUNT(DISTINCT codigo_ibge) AS qtd_municipios,
        MAX(fonte_populacao) AS fonte_populacao,
        MAX(fonte_pib) AS fonte_pib,
        MAX(fonte_idh) AS fonte_idh,
        MAX(fonte_renda) AS fonte_renda,
        MAX(fonte_demografia) AS fonte_demografia,
        MAX(fonte_pdv) AS fonte_pdv,
        MAX(data_atualizacao) AS data_atualizacao
    FROM base
    GROUP BY estado, microrregiao
), fatores AS (
    SELECT
        a.*,
        CASE WHEN MAX(populacao) OVER() > 0 THEN populacao / MAX(populacao) OVER() * 100 ELSE 0 END AS fator_populacao,
        CASE WHEN MAX(pib) OVER() > 0 THEN pib / MAX(pib) OVER() * 100 ELSE 0 END AS fator_pib,
        CASE WHEN MAX(renda_media) OVER() > 0 THEN renda_media / MAX(renda_media) OVER() * 100 ELSE 0 END AS fator_renda,
        CASE WHEN MAX(pib_per_capita) OVER() > 0 THEN pib_per_capita / MAX(pib_per_capita) OVER() * 100 ELSE 0 END AS fator_pib_per_capita,
        CASE WHEN MAX(pct_feminina) OVER() > 0 THEN pct_feminina / MAX(pct_feminina) OVER() * 100 ELSE 0 END AS fator_feminino,
        CASE WHEN MAX(pct_masculina) OVER() > 0 THEN pct_masculina / MAX(pct_masculina) OVER() * 100 ELSE 0 END AS fator_masculino,
        CASE WHEN MAX(total_pdv) OVER() > 0 THEN total_pdv / MAX(total_pdv) OVER() * 100 ELSE 50 END AS fator_pdv,
        CASE WHEN SUM(populacao) OVER() > 0 THEN populacao / SUM(populacao) OVER() * 100 ELSE 0 END AS participacao_populacao_pct,
        CASE WHEN SUM(pib) OVER() > 0 THEN pib / SUM(pib) OVER() * 100 ELSE 0 END AS participacao_pib_pct
    FROM agg a
), idc AS (
    SELECT
        f.*,
        (participacao_populacao_pct + participacao_pib_pct) / 2 AS idc_macro,
        (
            fator_populacao * 0.30 +
            fator_pib * 0.25 +
            fator_renda * 0.15 +
            fator_pib_per_capita * 0.15 +
            fator_feminino * 0.05 +
            fator_masculino * 0.05 +
            fator_pdv * 0.05
        ) AS idc_base
    FROM fatores f
)
SELECT
    i.*,
    CASE WHEN MAX(idc_base) OVER() > 0 THEN idc_base / MAX(idc_base) OVER() * 100 ELSE 0 END AS score,
    CASE
        WHEN CASE WHEN MAX(idc_base) OVER() > 0 THEN idc_base / MAX(idc_base) OVER() * 100 ELSE 0 END >= 75 THEN 'Alta prioridade'
        WHEN CASE WHEN MAX(idc_base) OVER() > 0 THEN idc_base / MAX(idc_base) OVER() * 100 ELSE 0 END >= 55 THEN 'Média prioridade'
        WHEN CASE WHEN MAX(idc_base) OVER() > 0 THEN idc_base / MAX(idc_base) OVER() * 100 ELSE 0 END >= 35 THEN 'Baixa prioridade'
        ELSE 'Monitorar'
    END AS classificacao,
    'IDC planejado: 30% população + 25% PIB + 15% renda + 15% PIB per capita + 5% feminino + 5% masculino + 5% PDV' AS formula_idc
FROM idc i;

DROP VIEW IF EXISTS app.vw_mercado_privado_resumo CASCADE;

CREATE OR REPLACE VIEW app.vw_mercado_privado_resumo AS
SELECT
    uf AS estado,
    COALESCE(microrregiao, 'Sem microrregião') AS microrregiao,
    categoria,
    produto,
    MIN(data_competencia) AS primeira_data,
    MAX(data_competencia) AS ultima_data,
    SUM(COALESCE(valor_mercado,0)) AS valor_mercado,
    SUM(COALESCE(volume_mercado,0)) AS volume_mercado,
    CASE WHEN SUM(COALESCE(volume_mercado,0)) > 0 THEN SUM(COALESCE(valor_mercado,0)) / SUM(COALESCE(volume_mercado,0)) ELSE AVG(preco_medio) END AS preco_medio,
    SUM(COALESCE(qtd_lojas,0)) AS qtd_lojas
FROM app.fato_mercado_privado
GROUP BY uf, COALESCE(microrregiao, 'Sem microrregião'), categoria, produto;

DROP VIEW IF EXISTS app.vw_curva_mercado_categoria CASCADE;

CREATE OR REPLACE VIEW app.vw_curva_mercado_categoria AS
SELECT
    data_competencia,
    uf AS estado,
    COALESCE(microrregiao, 'Sem microrregião') AS microrregiao,
    categoria,
    produto,
    SUM(COALESCE(valor_mercado,0)) AS valor_mercado,
    SUM(COALESCE(volume_mercado,0)) AS volume_mercado,
    CASE WHEN SUM(COALESCE(volume_mercado,0)) > 0 THEN SUM(COALESCE(valor_mercado,0)) / SUM(COALESCE(volume_mercado,0)) ELSE AVG(preco_medio) END AS preco_medio
FROM app.fato_mercado_privado
GROUP BY data_competencia, uf, COALESCE(microrregiao, 'Sem microrregião'), categoria, produto
UNION ALL
SELECT
    data_competencia,
    uf AS estado,
    COALESCE(microrregiao, 'Sem microrregião') AS microrregiao,
    categoria,
    produto,
    SUM(COALESCE(valor,0)) AS valor_mercado,
    SUM(COALESCE(volume,0)) AS volume_mercado,
    CASE WHEN SUM(COALESCE(volume,0)) > 0 THEN SUM(COALESCE(valor,0)) / SUM(COALESCE(volume,0)) ELSE AVG(preco_medio) END AS preco_medio
FROM app.fato_curva_mercado_categoria
GROUP BY data_competencia, uf, COALESCE(microrregiao, 'Sem microrregião'), categoria, produto;

DROP VIEW IF EXISTS app.vw_key_account_ibge CASCADE;

CREATE OR REPLACE VIEW app.vw_key_account_ibge AS
SELECT
    k.uf AS estado,
    COALESCE(g.microrregiao, 'Sem microrregião') AS microrregiao,
    COUNT(*) AS qtd_lojas_key_account,
    COUNT(DISTINCT k.grupo_key_account) AS qtd_grupos_key_account,
    COUNT(DISTINCT k.cliente) AS qtd_clientes_key_account,
    MAX(i.populacao) AS populacao_micro,
    CASE WHEN MAX(i.populacao) > 0 THEN COUNT(*)::NUMERIC / MAX(i.populacao) * 100000 ELSE NULL END AS densidade_key_account_100k
FROM app.dim_key_account_loja k
LEFT JOIN dw.dim_geografia g
  ON UPPER(TRIM(g.uf)) = UPPER(TRIM(k.uf))
 AND UPPER(TRIM(g.municipio)) = UPPER(TRIM(k.cidade))
LEFT JOIN app.vw_idc_completo_atual i
  ON i.estado = k.uf AND i.microrregiao = COALESCE(g.microrregiao, 'Sem microrregião')
GROUP BY k.uf, COALESCE(g.microrregiao, 'Sem microrregião');

DROP VIEW IF EXISTS app.vw_importacao_manual_resumo CASCADE;

CREATE OR REPLACE VIEW app.vw_importacao_manual_resumo AS
SELECT
    tipo_importacao,
    status,
    COUNT(*) AS qtd_execucoes,
    MAX(executado_em) AS ultima_execucao,
    SUM(COALESCE(registros_lidos, 0)) AS registros_lidos,
    SUM(COALESCE(registros_processados, 0)) AS registros_processados,
    SUM(COALESCE(registros_rejeitados, 0)) AS registros_rejeitados
FROM app.importacao_manual_log
GROUP BY tipo_importacao, status;
