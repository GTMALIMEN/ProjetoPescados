

## Modo manual controlado CEPEA/CEAGESP

CEPEA e CEAGESP não usam mais proxy, scraper, Playwright ou coleta automática. Use somente a aba **Importações Manuais** com os modelos novos e o modo **Limpar base antiga e carregar somente este arquivo**.

# Radar Pescados IA — README Técnico FINAL

## 1. Resumo Executivo

O **Radar Pescados IA** é um sistema de inteligência de mercado para empresas de pescados, proteínas, grãos, ração, importação, economia e regiões comerciais.

O objetivo é transformar dados internos e externos em decisões comerciais acionáveis, usando:

- Engenharia de Dados;
- Ciência de Dados;
- Estatística aplicada;
- Probabilidade;
- Machine Learning;
- Economia aplicada;
- Inteligência Artificial;
- Lógica de decisão comercial;
- Mapas e análise regional;
- Recomendações prescritivas;
- Governança de dados;
- Data Quality;
- Auditoria;
- Backtesting;
- Simulação de cenários.

O sistema não será apenas um dashboard. Ele deve funcionar como um **copiloto analítico**, capaz de responder:

- Qual é o cenário da região de 1 a 10?
- Qual proteína está mais competitiva?
- Vale colocar vendedor?
- Vale colocar promotor?
- Vale fazer campanha?
- Qual produto tem maior potencial?
- Qual produto está sensível ao dólar, inflação, grãos ou concorrência?
- Qual é a probabilidade de queda, expansão ou oportunidade?
- Qual o impacto financeiro esperado da ação recomendada?
- O que aconteceria se o dólar, preço ou concorrência mudasse?

Todas as previsões e recomendações são **estimativas probabilísticas**, não certezas absolutas.

---

## 2. Status da Versão Final

Esta versão FINAL consolida as melhorias das versões anteriores e corrige os últimos pontos técnicos antes da implementação.

### Principais decisões consolidadas na versão final

- Correção da materialized view `app.mv_vendas_mensal_geo`;
- Correção da materialized view `app.mv_score_regional_atual`;
- Definição de `REFRESH MATERIALIZED VIEW CONCURRENTLY`;
- Melhoria da chave natural da `dw.fato_vendas`;
- Definição de tabelas `staging`;
- Contadores de linhas `raw`, `staging`, `dw` e rejeitados;
- Fluxo de reprocessamento documentado;
- Governança de versões de pesos;
- FK entre recomendação e score;
- CPF/CNPJ tratado como hash;
- Regra correta para dimensão vendedor histórica;
- Índices extras para Streamlit e ML;
- Scores de vendedor, promotor e campanha salvos;
- ROI parametrizado;
- Regra oficial de consumo de dados pelo Streamlit;
- Separação entre itens obrigatórios de MVP e roadmap pós-MVP.

---

## 3. Decisões 100% Fechadas

| Item | Decisão |
|---|---|
| Nome do projeto | Radar Pescados IA |
| Tipo | Sistema de inteligência de mercado e decisão |
| Interface | Streamlit |
| Banco principal | PostgreSQL |
| Primeiro caso real | MG |
| Visão geográfica | Brasil → UF → Região IBGE → Região Comercial → Município |
| Histórico | Desde 2000 como padrão desejado, ou desde a primeira data disponível |
| Dados internos | Vendas internas como base comercial real |
| Dados externos | BCB, IBGE, CONAB, CEPEA, Comex Stat, FRED/FMI |
| Modelo de banco | Schemas raw, staging, dw, ml e app |
| Tipo de análise | Estatística + Probabilidade + ML + Economia aplicada |
| Score principal | Cenário 1 a 10 |
| Recomendações | Vendedor, promotor, campanha, monitorar ou corrigir |
| Recomendação | Sempre com justificativa, confiança, ROI e principais fatores |
| Separação de dados | Real, estimado, previsto e recomendado |
| Versão atual | FINAL |
| Objetivo da versão final | Fechamento técnico antes do início da implementação |

---

## 4. Stack Técnica

| Camada | Ferramenta |
|---|---|
| App | Streamlit |
| Banco principal | PostgreSQL |
| Séries temporais futura | TimescaleDB, se necessário |
| Tratamento | Pandas / Polars |
| Gráficos | Plotly |
| Mapas | GeoPandas + Folium / Plotly Mapbox |
| Machine Learning | Scikit-learn |
| Séries temporais | Statsmodels / Prophet opcional |
| Orquestração futura | Prefect ou Dagster |
| Data Quality futura | Great Expectations |
| Cache inicial | st.cache_data |
| Cache futuro | Redis / DuckDB |
| Deploy futuro | Docker |
| Ambiente | .env |
| Logs | logging estruturado |
| CI/CD futuro | GitHub Actions |
| Segredos futuro | Secret Manager / Vault |

---

## 5. Estrutura do Projeto

```text
radar_pescados_ia/
│
├── app.py
├── requirements.txt
├── .env
├── README.md
│
├── src/
│   ├── config/
│   │   └── settings.py
│   │
│   ├── database/
│   │   ├── connection.py
│   │   ├── create_schemas.sql
│   │   ├── models.sql
│   │   ├── staging.sql
│   │   ├── indexes.sql
│   │   ├── materialized_views.sql
│   │   └── seeds.sql
│   │
│   ├── collectors/
│   │   ├── bcb_collector.py
│   │   ├── ibge_collector.py
│   │   ├── conab_collector.py
│   │   ├── [removido] CEPEA agora é manual
│   │   ├── comex_collector.py
│   │   └── fred_collector.py
│   │
│   ├── etl/
│   │   ├── transform_series.py
│   │   ├── transform_vendas.py
│   │   ├── load_postgres.py
│   │   ├── reprocessamento.py
│   │   └── upsert.py
│   │
│   ├── services/
│   │   ├── indicadores_service.py
│   │   ├── scores_service.py
│   │   ├── recomendacao_service.py
│   │   ├── previsao_service.py
│   │   ├── roi_service.py
│   │   └── alertas_service.py
│   │
│   ├── ml/
│   │   ├── features.py
│   │   ├── train_models.py
│   │   ├── predict.py
│   │   ├── evaluate.py
│   │   ├── drift.py
│   │   └── backtesting.py
│   │
│   ├── pages/
│   │   ├── visao_geral.py
│   │   ├── mapa_mercado.py
│   │   ├── radar_economico.py
│   │   ├── radar_proteinas.py
│   │   ├── radar_graos.py
│   │   ├── comercio_exterior.py
│   │   ├── oportunidade_regiao.py
│   │   ├── ia_previsao.py
│   │   ├── recomendacoes.py
│   │   ├── saude_etl.py
│   │   └── sandbox_what_if.py
│   │
│   └── utils/
│       ├── datas.py
│       ├── normalizacao.py
│       ├── logs.py
│       ├── validacoes.py
│       ├── data_quality.py
│       └── retry.py
│
└── tests/
    ├── test_collectors.py
    ├── test_scores.py
    ├── test_recomendacoes.py
    └── test_sql_validations.py
```

---

## 6. Arquitetura de Dados

Fluxo padrão:

```text
API / Arquivo
    ↓
raw
    ↓
staging
    ↓
dw
    ↓
ml / app
    ↓
Streamlit
```

| Schema | Função |
|---|---|
| raw | dado bruto exatamente como veio da API/arquivo |
| staging | dado limpo e padronizado |
| dw | modelo analítico final |
| ml | bases de treino, features, modelos, previsões e backtests |
| app | tabelas, views e materialized views para o Streamlit |

Regra principal:

> Nenhum dado externo entra direto no dashboard. Toda fonte passa por raw, staging e dw antes de ser usada no app.

---

## 7. Criação dos Schemas

```sql
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS dw;
CREATE SCHEMA IF NOT EXISTS ml;
CREATE SCHEMA IF NOT EXISTS app;
```

---

## 8. Execução ETL

Toda execução de coletor deve gerar um `run_id`.

```sql
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
```

---

## 9. Tabela RAW Padrão

```sql
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
```

Regras:

- `raw` recebe append;
- nada é apagado da `raw` durante o MVP;
- cada coleta recebe um `run_id`;
- payload bruto parcial pode ser preservado para auditoria;
- dados de `raw` nunca são consumidos diretamente pelo app.

---

## 10. Controle de Carga ETL

Na versão final, `etl_controle_carga` fica conectado ao `etl_run` e registra contadores por camada.

```sql
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
```

Uso:

- saber qual fonte foi carregada;
- qual execução gerou erro;
- qual payload gerou problema;
- quantas linhas entraram em cada camada;
- quantas linhas foram rejeitadas;
- qual série precisa atualizar;
- tempo de execução.

---

## 11. Data Quality por Execução

```sql
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
```

Validações mínimas:

- coluna obrigatória existe;
- data válida;
- valor numérico válido;
- valor não negativo quando aplicável;
- quantidade mínima de linhas;
- duplicidade por chave natural;
- variação anormal;
- schema esperado;
- soma de pesos igual a 1.00;
- validação do JSONB `principais_fatores`;
- validação da feature store;
- cenário entre 1 e 10;
- contagem entre raw, staging e dw.

---

## 12. Fluxo de Reprocessamento

Regra oficial:

```text
1. Nunca apagar a raw.
2. Se a carga falhar, registrar erro em etl_run e etl_controle_carga.
3. Corrigir o problema de transformação, schema ou validação.
4. Criar novo run_id.
5. Reprocessar da raw para staging.
6. Fazer upsert no DW.
7. Registrar nova execução.
8. Nunca sobrescrever o erro antigo.
9. O histórico de falhas deve permanecer auditável.
```

---

## 13. Catálogo de Fontes

A versão final adiciona um catálogo central das fontes para organizar coletores, endpoints e periodicidade.

```sql
CREATE TABLE IF NOT EXISTS app.catalogo_fonte (
    id SERIAL PRIMARY KEY,
    fonte TEXT NOT NULL,
    indicador TEXT NOT NULL,
    codigo_serie TEXT,
    endpoint TEXT,
    periodicidade TEXT,
    data_inicio_padrao DATE,
    ativo BOOLEAN DEFAULT TRUE,
    prioridade INT,
    observacao TEXT
);
```

Como `codigo_serie` pode ser nulo, usar índice com `COALESCE`.

```sql
CREATE UNIQUE INDEX IF NOT EXISTS uq_catalogo_fonte
ON app.catalogo_fonte (
    fonte,
    indicador,
    COALESCE(codigo_serie, '')
);
```

Regra:

> O catálogo define o que pode ser coletado. O coletor executa a coleta. O ETL registra a execução.

---

## 14. Padrão de Staging

Na versão final, o padrão escolhido é **tabela staging por fonte**.

### Exemplo BCB

```sql
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
```

### Exemplos futuros

```text
staging.ibge_localidades
staging.vendas_tratadas
staging.comex_importacao
staging.cepea_precos
staging.conab_precos
staging.fred_commodities
```

Regra:

> Cada coletor tem sua tabela staging própria, mantendo estrutura limpa e fácil de debugar.

---

## 15. Tabela Central de Séries Históricas

Não usar `UNIQUE` simples com colunas que podem ser `NULL`, pois pode permitir duplicatas silenciosas.  
A solução adotada é uma chave natural hash com `COALESCE`.

Na versão final, o hash oficial é apenas `chave_natural_hash`.

```sql
CREATE TABLE IF NOT EXISTS dw.fato_serie_historica (
    id BIGSERIAL PRIMARY KEY,
    data DATE NOT NULL,
    fonte TEXT NOT NULL,
    codigo_serie TEXT,
    indicador TEXT NOT NULL,
    categoria TEXT,
    subcategoria TEXT,
    pais TEXT DEFAULT 'Brasil',
    uf TEXT,
    municipio TEXT,
    regiao_ibge TEXT,
    regiao_comercial TEXT,
    valor NUMERIC,
    unidade TEXT,
    periodicidade TEXT,
    data_inicio_fonte DATE,
    data_fim_fonte DATE,
    data_coleta TIMESTAMP DEFAULT NOW(),
    chave_natural_hash TEXT GENERATED ALWAYS AS (
        md5(
            concat_ws('|',
                data::TEXT,
                COALESCE(fonte, ''),
                COALESCE(codigo_serie, ''),
                COALESCE(indicador, ''),
                COALESCE(pais, ''),
                COALESCE(uf, ''),
                COALESCE(municipio, ''),
                COALESCE(regiao_ibge, ''),
                COALESCE(regiao_comercial, '')
            )
        )
    ) STORED
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fato_serie_historica_hash
ON dw.fato_serie_historica (chave_natural_hash);
```

---

## 16. Estratégia de Atualização Incremental

| Camada | Estratégia |
|---|---|
| raw | append com `run_id` |
| staging | recria somente o lote processado |
| dw | upsert por chave natural |
| app | refresh de views/tabelas agregadas |
| ml | versionado por data/modelo |

Regra:

> Nada de `truncate + reload` como padrão.

---

## 17. Modelo Dimensional de Vendas

A venda interna usa modelo estrela.

### 17.1 Dimensão Cliente

Na versão final, CPF/CNPJ não é armazenado em texto livre no DW analítico.  
O campo deve ser armazenado como hash seguro.

```sql
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

ALTER TABLE dw.dim_cliente
ADD CONSTRAINT uq_dim_cliente_codigo UNIQUE (codigo_cliente);

CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_cliente_cpf_cnpj_hash
ON dw.dim_cliente (cpf_cnpj_hash)
WHERE cpf_cnpj_hash IS NOT NULL;
```

Regra LGPD:

> O DW analítico não guarda CPF/CNPJ puro. Se o dado original for indispensável, deve ficar em tabela separada, restrita e protegida.

### 17.2 Dimensão Produto

```sql
CREATE TABLE IF NOT EXISTS dw.dim_produto (
    id_produto SERIAL PRIMARY KEY,
    codigo_produto TEXT,
    produto TEXT,
    grupo_produto TEXT,
    proteina TEXT,
    categoria TEXT,
    origem TEXT
);

ALTER TABLE dw.dim_produto
ADD CONSTRAINT uq_dim_produto_codigo UNIQUE (codigo_produto);
```

### 17.3 Dimensão Vendedor com Histórico Simples

```sql
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
WHERE registro_atual = TRUE;
```

Regra importante:

> O ETL de vendas deve buscar o `id_vendedor` válido na data da venda. A view deve fazer JOIN direto pelo `id_vendedor`, sem filtrar `registro_atual`.

Lookup correto:

```sql
SELECT id_vendedor
FROM dw.dim_vendedor
WHERE codigo_vendedor = :codigo
  AND data_inicio <= :data_venda
  AND (data_fim IS NULL OR data_fim >= :data_venda);
```

### 17.4 Dimensão Canal

```sql
CREATE TABLE IF NOT EXISTS dw.dim_canal (
    id_canal SERIAL PRIMARY KEY,
    canal TEXT UNIQUE
);
```

### 17.5 Fato Vendas

Na versão final, a `fato_vendas` deve usar identificadores reais da origem para evitar duplicidades.

> Para bases Sankhya ou similares, priorizar: número único, nota, pedido, item, sequência, código do produto, código do parceiro e data.

```sql
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
    data_carga TIMESTAMP DEFAULT NOW(),
    chave_venda_hash TEXT GENERATED ALWAYS AS (
        md5(
            concat_ws('|',
                COALESCE(codigo_origem, ''),
                COALESCE(numero_documento, ''),
                COALESCE(numero_item, ''),
                COALESCE(numero_pedido, ''),
                data::TEXT,
                COALESCE(id_cliente::TEXT, ''),
                COALESCE(id_produto::TEXT, ''),
                COALESCE(id_vendedor::TEXT, ''),
                COALESCE(codigo_ibge, '')
            )
        )
    ) STORED
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fato_vendas_hash
ON dw.fato_vendas (chave_venda_hash);
```

Regra:

> Evitar usar valores numéricos como `valor_venda`, `volume_kg` e `quantidade` na chave hash, pois diferenças de precisão podem gerar hashes diferentes para a mesma venda.

---

## 18. View Analítica de Vendas

A view não usa `SELECT *`.  
As colunas são listadas explicitamente.

```sql
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
```

---

## 19. Geografia e Regiões

```text
Brasil
 → UF
   → Região IBGE
     → Região Comercial
       → Município
         → Bairro/setor censitário, futuro
```

### Dimensão Geográfica

```sql
CREATE TABLE IF NOT EXISTS dw.dim_geografia (
    id_geografia SERIAL PRIMARY KEY,
    codigo_ibge TEXT UNIQUE,
    pais TEXT DEFAULT 'Brasil',
    uf TEXT,
    nome_uf TEXT,
    municipio TEXT,
    regiao_intermediaria TEXT,
    regiao_imediata TEXT,
    regiao_metropolitana TEXT,
    regiao_comercial TEXT,
    latitude NUMERIC,
    longitude NUMERIC
);
```

### Região Comercial

```sql
CREATE TABLE IF NOT EXISTS app.dim_regiao_comercial (
    id SERIAL PRIMARY KEY,
    uf TEXT NOT NULL,
    regiao_comercial TEXT NOT NULL,
    municipio TEXT NOT NULL,
    codigo_ibge TEXT,
    prioridade INT,
    ativo BOOLEAN DEFAULT TRUE,
    UNIQUE (uf, regiao_comercial, municipio)
);
```

---

## 20. Tabela de NCM de Pescados

```sql
CREATE TABLE IF NOT EXISTS app.dim_ncm_pescados (
    id SERIAL PRIMARY KEY,
    ncm TEXT NOT NULL UNIQUE,
    descricao TEXT,
    produto_grupo TEXT,
    proteina TEXT,
    origem TEXT DEFAULT 'importado',
    ativo BOOLEAN DEFAULT TRUE
);
```

Uso:

- salmão;
- bacalhau;
- camarão;
- merluza;
- pescados congelados;
- outros.

---

## 21. Índices Obrigatórios

```sql
CREATE INDEX IF NOT EXISTS idx_serie_data
ON dw.fato_serie_historica (data);

CREATE INDEX IF NOT EXISTS idx_serie_fonte_indicador_data
ON dw.fato_serie_historica (fonte, indicador, data);

CREATE INDEX IF NOT EXISTS idx_serie_geo
ON dw.fato_serie_historica (pais, uf, municipio, regiao_comercial);

CREATE INDEX IF NOT EXISTS idx_vendas_data
ON dw.fato_vendas (data);

CREATE INDEX IF NOT EXISTS idx_vendas_geo
ON dw.fato_vendas (uf, municipio, regiao_comercial);

CREATE INDEX IF NOT EXISTS idx_vendas_produto
ON dw.fato_vendas (id_produto);

CREATE INDEX IF NOT EXISTS idx_vendas_cliente
ON dw.fato_vendas (id_cliente);

CREATE INDEX IF NOT EXISTS idx_vendas_vendedor
ON dw.fato_vendas (id_vendedor);

CREATE INDEX IF NOT EXISTS idx_score_regional_uf_produto
ON app.fato_score_regional (uf, produto, data_referencia);

CREATE INDEX IF NOT EXISTS idx_recomendacao_uf_tipo
ON app.fato_recomendacao (uf, tipo_recomendacao, data_referencia);

CREATE INDEX IF NOT EXISTS idx_feedback_recomendacao
ON app.feedback_recomendacao (id_recomendacao, data_feedback);

CREATE INDEX IF NOT EXISTS idx_feature_store_data_geo
ON ml.feature_store_regional (data_referencia, uf, regiao_comercial, municipio, produto, proteina);

CREATE INDEX IF NOT EXISTS idx_feature_store_nome_versao
ON ml.feature_store_regional (nome_feature, versao_feature);
```

---

## 22. Materialized Views para o Streamlit

### 22.1 Vendas Mensais por Geografia

A versão final corrige o `GROUP BY`.  
Essa MV não agrupa por cliente nem vendedor, para servir como base de cards, mapas e visão regional.

```sql
CREATE MATERIALIZED VIEW IF NOT EXISTS app.mv_vendas_mensal_geo AS
SELECT
    DATE_TRUNC('month', data)::DATE AS mes,
    uf,
    regiao_comercial,
    municipio,
    id_produto,
    SUM(valor_venda) AS valor_venda,
    SUM(volume_kg) AS volume_kg,
    SUM(quantidade) AS quantidade,
    COUNT(DISTINCT id_cliente) AS qtd_clientes,
    CASE
        WHEN SUM(volume_kg) = 0 OR SUM(volume_kg) IS NULL THEN NULL
        ELSE SUM(valor_venda) / SUM(volume_kg)
    END AS preco_medio_kg
FROM dw.fato_vendas
GROUP BY
    DATE_TRUNC('month', data)::DATE,
    uf,
    regiao_comercial,
    municipio,
    id_produto;

CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_vendas_mensal_geo
ON app.mv_vendas_mensal_geo (mes, uf, regiao_comercial, municipio, id_produto);
```

Se for necessário analisar por vendedor ou cliente:

```text
app.mv_vendas_mensal_vendedor
app.mv_vendas_mensal_cliente
```

### 22.2 Score Regional Atual

A versão final corrige o `SELECT *` e busca a última referência por combinação de região/produto/proteína.

```sql
CREATE MATERIALIZED VIEW IF NOT EXISTS app.mv_score_regional_atual AS
WITH ultima_referencia AS (
    SELECT
        uf,
        regiao_comercial,
        municipio,
        produto,
        proteina,
        MAX(data_referencia) AS ultima_data
    FROM app.fato_score_regional
    GROUP BY uf, regiao_comercial, municipio, produto, proteina
)
SELECT
    s.data_referencia,
    s.pais,
    s.uf,
    s.regiao_ibge,
    s.regiao_comercial,
    s.municipio,
    s.produto,
    s.proteina,
    s.score_oportunidade,
    s.score_risco,
    s.score_pressao_custo,
    s.score_competitividade,
    s.score_sensibilidade_dolar,
    s.score_final,
    s.cenario_1_10,
    s.confianca,
    s.data_calculo
FROM app.fato_score_regional s
INNER JOIN ultima_referencia ur
    ON s.uf               IS NOT DISTINCT FROM ur.uf
   AND s.regiao_comercial IS NOT DISTINCT FROM ur.regiao_comercial
   AND s.municipio        IS NOT DISTINCT FROM ur.municipio
   AND s.produto          IS NOT DISTINCT FROM ur.produto
   AND s.proteina         IS NOT DISTINCT FROM ur.proteina
   AND s.data_referencia  = ur.ultima_data;
```

Para índice único com `NULL`, usar hash:

```sql
CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_score_regional_atual
ON app.mv_score_regional_atual (
    COALESCE(uf, ''),
    COALESCE(regiao_comercial, ''),
    COALESCE(municipio, ''),
    COALESCE(produto, ''),
    COALESCE(proteina, '')
);
```

### 22.3 Refresh de Materialized Views

Primeira carga:

```sql
REFRESH MATERIALIZED VIEW app.mv_vendas_mensal_geo;
REFRESH MATERIALIZED VIEW app.mv_score_regional_atual;
```

Cargas seguintes em ambiente compartilhado/produção:

```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY app.mv_vendas_mensal_geo;
REFRESH MATERIALIZED VIEW CONCURRENTLY app.mv_score_regional_atual;
```

Regra:

> `REFRESH CONCURRENTLY` exige índice único e a MV já precisa estar populada.

---

## 23. Regra de Consumo de Dados no Streamlit

O Streamlit não deve consultar tabelas fato diretamente, exceto em páginas técnicas/admin.

### Regra oficial

```text
Dados transacionais:
- Nunca acessar fato diretamente em página comum.
- Usar views analíticas ou materialized views.

Scores:
- Visão atual usa app.mv_score_regional_atual.
- Histórico pode consultar app.fato_score_regional com filtros.

Recomendações:
- Usar app.fato_recomendacao.
- Futuramente criar app.mv_recomendacao_atual.

Previsões:
- Usar ml.fato_previsao com filtro de modelo em produção.

Dados econômicos:
- Usar indicadores_service.py.
- Evitar SQL direto nas páginas.
```

---

## 24. Governança de Pesos dos Scores

Na versão final, a validação de soma dos pesos não será feita linha a linha por trigger simples, pois isso pode falhar durante inserção parcial.

Será usada uma tabela de versão.

```sql
CREATE TABLE IF NOT EXISTS app.config_score_versao (
    id SERIAL PRIMARY KEY,
    nome_score TEXT NOT NULL,
    versao TEXT NOT NULL,
    status TEXT CHECK (status IN ('rascunho', 'validada', 'ativa', 'arquivada')),
    data_criacao TIMESTAMP DEFAULT NOW(),
    data_ativacao TIMESTAMP,
    UNIQUE (nome_score, versao)
);
```

Pesos:

```sql
CREATE TABLE IF NOT EXISTS app.config_pesos_score (
    id SERIAL PRIMARY KEY,
    nome_score TEXT NOT NULL,
    variavel TEXT NOT NULL,
    peso NUMERIC NOT NULL CHECK (peso >= 0),
    versao TEXT DEFAULT 'v1',
    data_inicio_vigencia DATE DEFAULT CURRENT_DATE,
    data_fim_vigencia DATE,
    motivo_alteracao TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT NOW(),
    UNIQUE (nome_score, variavel, versao)
);
```

Regra:

```text
Uma versão de score só pode virar ativa quando SUM(peso) = 1.00.
```

---

## 25. Fontes de Dados

| Fonte | Dados | Uso |
|---|---|---|
| Banco Central | dólar, Selic, IPCA, juros | cenário econômico e câmbio |
| IBGE/SIDRA/Censo | população, renda, POF, Censo, IPCA | potencial regional e consumo estimado |
| CONAB | milho, soja, grãos, preços agropecuários | pressão de custo e ração |
| CEPEA | boi, frango, suíno, ovos, tilápia, soja, milho | competitividade entre proteínas |
| Comex Stat / MDIC | importação/exportação por NCM | pescados importados e preço médio |
| FRED/FMI | fish meal, commodities globais | insumos globais e visão internacional |

---

## 26. Indicadores Estatísticos

### 26.1 Variação Mensal

```text
var_mensal = (valor_mes_atual - valor_mes_anterior) / valor_mes_anterior
```

### 26.2 Variação Trimestral

```text
var_tri = (media_ultimos_3_meses - media_3_meses_anteriores) / media_3_meses_anteriores
```

### 26.3 Média Móvel

```text
media_movel_3m = média dos últimos 3 meses
media_movel_6m = média dos últimos 6 meses
media_movel_12m = média dos últimos 12 meses
```

### 26.4 Volatilidade

```text
volatilidade = desvio_padrao(variações_mensais)
```

### 26.5 Z-score

```text
z = (valor_atual - média_histórica) / desvio_padrão_histórico
```

| Z-score | Interpretação |
|---:|---|
| menor que -2 | queda anormal |
| -2 a 2 | comportamento normal |
| maior que 2 | alta anormal |

### 26.6 Correlação com Defasagem

```text
corr_lag_0 = correlação indicador atual x venda atual
corr_lag_1 = correlação indicador mês anterior x venda atual
corr_lag_2 = correlação indicador 2 meses antes x venda atual
corr_lag_3 = correlação indicador 3 meses antes x venda atual
```

### 26.7 Elasticidade-Preço Própria

```text
elasticidade = variação_percentual_volume / variação_percentual_preço
```

### 26.8 Elasticidade-Preço Cruzada

```text
elasticidade_cruzada =
% variação volume pescado / % variação preço proteína concorrente
```

---

## 27. Normalização

Todos os scores trabalham de 0 a 100.

```text
valor_norm = ((valor_atual - p5) / (p95 - p5)) * 100
```

Depois:

```text
se valor_norm < 0, vira 0
se valor_norm > 100, vira 100
```

---

## 28. Indicadores Estratégicos

### 28.1 Pressão de Custo

```text
pressao_custo =
0.20 * dolar_norm +
0.15 * milho_norm +
0.15 * soja_norm +
0.15 * farelo_norm +
0.20 * fish_meal_norm +
0.10 * ipca_alimentos_norm +
0.05 * importacao_norm
```

### 28.2 Competitividade entre Proteínas

```text
competitividade_pescado =
0.40 * preco_relativo_pescado_vs_concorrentes_norm +
0.25 * variacao_preco_pescado_norm +
0.20 * variacao_preco_concorrentes_norm +
0.15 * volume_pescado_norm
```

### 28.3 Sensibilidade ao Dólar

```text
sensibilidade_dolar =
0.30 * corr_dolar_preco_norm +
0.30 * impacto_dolar_volume_norm +
0.20 * participacao_importada_norm +
0.10 * volatilidade_preco_norm +
0.10 * lag_impacto_norm
```

### 28.4 Oportunidade Regional

```text
oportunidade_regional =
0.15 * populacao_norm +
0.15 * renda_norm +
0.15 * crescimento_vendas_norm +
0.10 * clientes_ativos_norm +
0.10 * ticket_medio_norm +
0.10 * mix_premium_norm +
0.10 * potencial_consumo_norm +
0.10 * baixa_cobertura_norm +
0.05 * logistica_norm
```

### 28.5 Risco de Queda

```text
risco_queda =
0.20 * queda_volume_norm +
0.15 * queda_frequencia_norm +
0.15 * queda_clientes_norm +
0.10 * inflacao_norm +
0.10 * dolar_norm +
0.10 * concorrencia_norm +
0.10 * sazonalidade_negativa_norm +
0.05 * reducao_mix_norm +
0.05 * queda_ticket_norm
```

---

## 29. Regras de Bloqueio Crítico

A média ponderada não pode mascarar risco extremo.

```text
Se sensibilidade_dolar >= 85 e produto_importado = sim:
    limitar cenario_maximo = 6

Se risco_queda >= 90:
    recomendação obrigatória = ação corretiva

Se pressão_custo >= 90:
    bloquear expansão agressiva

Se dados_insuficientes = true:
    reduzir confiança do modelo

Se anomalia crítica detectada:
    marcar recomendação como revisão necessária
```

Roadmap pós-MVP:

```text
Se custo de ração > X e preço do boi < Y:
    bloquear expansão agressiva de tilápia

Se preço de frango cair fortemente e tilápia subir:
    acionar risco de substituição
```

---

## 30. Cenário 1 a 10

```text
risco_invertido = 100 - risco_queda
```

```text
score_final =
0.30 * oportunidade_regional +
0.20 * desempenho_vendas +
0.15 * competitividade_proteina +
0.15 * ambiente_economico +
0.10 * cobertura_comercial +
0.10 * risco_invertido
```

Cálculo seguro:

```sql
cenario_1_10 = LEAST(10, GREATEST(1, CEIL(score_final / 10.0)))
```

| Nota | Situação | Ação |
|---:|---|---|
| 1 | crítico extremo | ação urgente |
| 2 | muito ruim | plano corretivo |
| 3 | ruim | revisar preço/mix |
| 4 | atenção | acompanhar semanalmente |
| 5 | neutro | manter |
| 6 | levemente positivo | testar campanha |
| 7 | bom | explorar oportunidade |
| 8 | muito bom | expandir comercialmente |
| 9 | excelente | prioridade alta |
| 10 | ideal | máxima prioridade |

---

## 31. Tabela de Scores Regionais

```sql
CREATE TABLE IF NOT EXISTS app.fato_score_regional (
    id BIGSERIAL PRIMARY KEY,
    data_referencia DATE NOT NULL,
    pais TEXT DEFAULT 'Brasil',
    uf TEXT,
    regiao_ibge TEXT,
    regiao_comercial TEXT,
    municipio TEXT,
    produto TEXT,
    proteina TEXT,
    score_oportunidade NUMERIC CHECK (score_oportunidade BETWEEN 0 AND 100),
    score_risco NUMERIC CHECK (score_risco BETWEEN 0 AND 100),
    score_pressao_custo NUMERIC CHECK (score_pressao_custo BETWEEN 0 AND 100),
    score_competitividade NUMERIC CHECK (score_competitividade BETWEEN 0 AND 100),
    score_sensibilidade_dolar NUMERIC CHECK (score_sensibilidade_dolar BETWEEN 0 AND 100),
    score_final NUMERIC CHECK (score_final BETWEEN 0 AND 100),
    cenario_1_10 INT CHECK (cenario_1_10 BETWEEN 1 AND 10),
    confianca NUMERIC CHECK (confianca BETWEEN 0 AND 100),
    data_calculo TIMESTAMP DEFAULT NOW(),
    chave_score_hash TEXT GENERATED ALWAYS AS (
        md5(
            concat_ws('|',
                data_referencia::TEXT,
                COALESCE(pais, ''),
                COALESCE(uf, ''),
                COALESCE(regiao_ibge, ''),
                COALESCE(regiao_comercial, ''),
                COALESCE(municipio, ''),
                COALESCE(produto, ''),
                COALESCE(proteina, '')
            )
        )
    ) STORED
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fato_score_regional_hash
ON app.fato_score_regional (chave_score_hash);
```

---

## 32. Tabela de Recomendações

Na versão final, a recomendação referencia o score que a originou e salva os scores concorrentes.

```sql
CREATE TABLE IF NOT EXISTS app.fato_recomendacao (
    id BIGSERIAL PRIMARY KEY,
    id_score BIGINT REFERENCES app.fato_score_regional(id),
    data_referencia DATE NOT NULL,
    pais TEXT DEFAULT 'Brasil',
    uf TEXT,
    regiao_comercial TEXT,
    municipio TEXT,
    produto TEXT,
    proteina TEXT,
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
    chave_recomendacao_hash TEXT GENERATED ALWAYS AS (
        md5(
            concat_ws('|',
                data_referencia::TEXT,
                COALESCE(pais, ''),
                COALESCE(uf, ''),
                COALESCE(regiao_comercial, ''),
                COALESCE(municipio, ''),
                COALESCE(produto, ''),
                COALESCE(proteina, ''),
                COALESCE(tipo_recomendacao, '')
            )
        )
    ) STORED
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fato_recomendacao_hash
ON app.fato_recomendacao (chave_recomendacao_hash);
```

---

## 33. Contrato JSONB `principais_fatores`

```json
[
  {
    "fator": "dolar",
    "descricao": "Alta do dólar pressionando produto importado",
    "peso": 0.30,
    "direcao": "negativa",
    "impacto": -12.5,
    "unidade": "%",
    "confianca": 78
  }
]
```

Campos obrigatórios:

| Campo | Obrigatório |
|---|---|
| fator | sim |
| descricao | sim |
| peso | sim |
| direcao | sim |
| impacto | sim |
| unidade | não |
| confianca | sim |

---

## 34. Decisão Vendedor, Promotor ou Campanha

### Score de vendedor

```text
score_vendedor =
0.35 * oportunidade_regional +
0.25 * baixa_cobertura_clientes +
0.20 * potencial_consumo +
0.10 * crescimento_regional +
0.10 * margem_media
```

### Score de promotor

```text
score_promotor =
0.30 * clientes_ativos +
0.25 * redes_ativas +
0.20 * baixa_execucao_loja +
0.15 * mix_premium +
0.10 * oportunidade_campanha
```

### Score de campanha

```text
score_campanha =
0.30 * risco_substituicao +
0.25 * queda_volume +
0.20 * competitividade_preco +
0.15 * sazonalidade +
0.10 * margem_disponivel
```

---

## 35. ROI da Recomendação

ROI esperado:

```text
ROI esperado =
(ganho_incremental_estimado - custo_da_acao) / custo_da_acao
```

Custos não ficam fixos no código. Usar tabela de configuração:

```sql
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
```

---

## 36. Versionamento de Modelos ML

```sql
CREATE TABLE IF NOT EXISTS ml.modelo_registro (
    id_modelo SERIAL PRIMARY KEY,
    nome_modelo TEXT NOT NULL,
    versao TEXT NOT NULL,
    objetivo TEXT,
    algoritmo TEXT,
    features JSONB,
    metricas JSONB,
    artefato_uri TEXT,
    status TEXT CHECK (status IN ('treino', 'teste', 'producao', 'arquivado')),
    data_treino TIMESTAMP DEFAULT NOW(),
    ativo BOOLEAN DEFAULT FALSE,
    UNIQUE (nome_modelo, versao)
);
```

Garantir apenas um modelo em produção por objetivo:

```sql
CREATE UNIQUE INDEX IF NOT EXISTS uq_modelo_producao_por_objetivo
ON ml.modelo_registro (objetivo)
WHERE status = 'producao';
```

Métricas obrigatórias sugeridas:

| Tipo de modelo | Métricas |
|---|---|
| Regressão | MAE, RMSE, MAPE |
| Classificação | AUC, F1, Precision, Recall |
| Séries temporais | MAE, RMSE, MAPE |
| Clustering | Silhouette Score |

---

## 37. Tabela de Previsões

```sql
CREATE TABLE IF NOT EXISTS ml.fato_previsao (
    id BIGSERIAL PRIMARY KEY,
    id_modelo INT NOT NULL REFERENCES ml.modelo_registro(id_modelo),
    data_referencia DATE NOT NULL,
    data_prevista DATE NOT NULL,
    alvo TEXT,
    pais TEXT DEFAULT 'Brasil',
    uf TEXT,
    regiao_comercial TEXT,
    municipio TEXT,
    produto TEXT,
    proteina TEXT,
    valor_previsto NUMERIC,
    intervalo_minimo NUMERIC,
    intervalo_maximo NUMERIC,
    probabilidade NUMERIC CHECK (probabilidade BETWEEN 0 AND 100),
    confianca_modelo NUMERIC CHECK (confianca_modelo BETWEEN 0 AND 100),
    principais_fatores JSONB,
    data_calculo TIMESTAMP DEFAULT NOW(),
    chave_previsao_hash TEXT GENERATED ALWAYS AS (
        md5(
            concat_ws('|',
                data_referencia::TEXT,
                data_prevista::TEXT,
                COALESCE(id_modelo::TEXT, ''),
                COALESCE(alvo, ''),
                COALESCE(pais, ''),
                COALESCE(uf, ''),
                COALESCE(regiao_comercial, ''),
                COALESCE(municipio, ''),
                COALESCE(produto, ''),
                COALESCE(proteina, '')
            )
        )
    ) STORED
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fato_previsao_hash
ON ml.fato_previsao (chave_previsao_hash);
```

---

## 38. Feature Store Regional

```sql
CREATE TABLE IF NOT EXISTS ml.feature_store_regional (
    id BIGSERIAL PRIMARY KEY,
    data_referencia DATE NOT NULL,
    pais TEXT DEFAULT 'Brasil',
    uf TEXT,
    regiao_comercial TEXT,
    municipio TEXT,
    produto TEXT,
    proteina TEXT,
    nome_feature TEXT NOT NULL,
    valor_feature NUMERIC,
    unidade TEXT,
    janela TEXT,
    fonte_origem TEXT,
    versao_feature TEXT DEFAULT 'v1',
    data_calculo TIMESTAMP DEFAULT NOW(),
    chave_feature_hash TEXT GENERATED ALWAYS AS (
        md5(
            concat_ws('|',
                data_referencia::TEXT,
                COALESCE(pais, ''),
                COALESCE(uf, ''),
                COALESCE(regiao_comercial, ''),
                COALESCE(municipio, ''),
                COALESCE(produto, ''),
                COALESCE(proteina, ''),
                COALESCE(nome_feature, ''),
                COALESCE(versao_feature, '')
            )
        )
    ) STORED
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_feature_store_regional_hash
ON ml.feature_store_regional (chave_feature_hash);
```

---

## 39. Tratamento de Dados Faltantes nos Scores

| Situação | Regra |
|---|---|
| dado faltante pouco relevante | redistribuir peso entre variáveis disponíveis |
| dado faltante relevante | reduzir confiança |
| dado crítico ausente | bloquear score ou marcar como insuficiente |
| muitos dados faltantes | não gerar recomendação automática |

Regra inicial:

```text
Se mais de 30% das variáveis do score estiverem ausentes:
    não calcular score final
    marcar confiança baixa
    gerar alerta de dado insuficiente
```

---

## 40. Backtesting dos Scores

```sql
CREATE TABLE IF NOT EXISTS ml.backtest_score (
    id BIGSERIAL PRIMARY KEY,
    id_modelo INT REFERENCES ml.modelo_registro(id_modelo),
    data_teste DATE,
    data_alvo DATE,
    tipo_score TEXT,
    tipo_modelo TEXT CHECK (tipo_modelo IN ('regressao', 'classificacao', 'serie_temporal')),
    metrica_erro TEXT,
    versao_score TEXT,
    versao_pesos TEXT,
    uf TEXT,
    regiao_comercial TEXT,
    produto TEXT,
    score_calculado NUMERIC,
    resultado_real NUMERIC,
    erro NUMERIC,
    avaliacao TEXT,
    data_calculo TIMESTAMP DEFAULT NOW(),
    chave_backtest_hash TEXT GENERATED ALWAYS AS (
        md5(
            concat_ws('|',
                COALESCE(data_teste::TEXT, ''),
                COALESCE(data_alvo::TEXT, ''),
                COALESCE(tipo_score, ''),
                COALESCE(uf, ''),
                COALESCE(regiao_comercial, ''),
                COALESCE(produto, ''),
                COALESCE(versao_score, ''),
                COALESCE(versao_pesos, '')
            )
        )
    ) STORED
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_backtest_score_hash
ON ml.backtest_score (chave_backtest_hash);
```

---

## 41. Particionamento e Retenção

O MVP começa com PostgreSQL puro.  
Tabelas prioritárias para particionamento futuro:

```text
dw.fato_serie_historica
dw.fato_vendas
```

Estratégia futura:

```sql
CREATE TABLE dw.fato_serie_historica (
    ...
    data DATE NOT NULL
) PARTITION BY RANGE (data);
```

Partições sugeridas:

```text
2000-2005
2006-2010
2011-2015
2016-2020
2021-2025
2026+
```

Retenção inicial:

| Camada | Retenção |
|---|---|
| raw | manter tudo no MVP |
| staging | pode ser recriada |
| dw | manter histórico completo |
| ml | manter previsões, features e modelos versionados |
| app | pode ser recalculada |

---

## 42. VACUUM e ANALYZE

Com cargas incrementais e upserts, o PostgreSQL pode acumular dead tuples.

Após cargas históricas ou cargas grandes:

```sql
VACUUM ANALYZE dw.fato_serie_historica;
VACUUM ANALYZE dw.fato_vendas;
VACUUM ANALYZE app.fato_score_regional;
```

Regra:

> Autovacuum é mantido, mas cargas grandes podem exigir `VACUUM ANALYZE` manual ou agendado.

---

## 43. Segurança e Acesso

### Fase local

Sem login obrigatório.

### MVP compartilhado

Login obrigatório.

### Perfis futuros

| Perfil | Acesso |
|---|---|
| admin | tudo |
| gestor | dashboards e recomendações |
| comercial | regiões, clientes e recomendações |
| marketing | proteínas, campanhas e recomendações |
| leitura | apenas visualização |

Segurança futura:

- criptografia em trânsito;
- auditoria de acesso;
- controle por usuário;
- cuidado com LGPD;
- anonimização/pseudonimização de CPF/CNPJ quando necessário;
- Row-Level Security em cenário multiempresa ou multi-região;
- Secret Manager antes de produção.

---

## 44. Telas do App

### Tela 1 — Visão Geral

- cenário geral;
- faturamento;
- volume;
- ticket médio calculado;
- preço médio por kg;
- dólar;
- IPCA alimentos;
- pressão de custo;
- risco de queda;
- oportunidade regional;
- recomendações críticas.

### Tela 2 — Mapa de Mercado

Filtros:

- Brasil;
- UF;
- região IBGE;
- região comercial;
- município;
- produto;
- proteína;
- canal;
- período.

Camadas:

- vendas;
- população;
- renda;
- oportunidade;
- risco;
- cenário;
- recomendação.

### Tela 3 — Radar Econômico

- dólar x venda de importados;
- IPCA alimentos x volume;
- Selic x comportamento;
- inflação x preço médio kg;
- renda x mix premium.

### Tela 4 — Radar de Proteínas

Comparação dinâmica:

```text
Peixe/produto base: Tilápia
Comparar com: Frango
```

Saídas:

- variação do peixe;
- variação da proteína comparada;
- diferença percentual;
- elasticidade cruzada;
- risco de substituição;
- oportunidade de campanha;
- sugestão de ação.

### Tela 5 — Radar de Grãos e Ração

- milho;
- soja;
- farelo;
- fish meal;
- pressão de custo;
- variação mensal/trimestral.

### Tela 6 — Comércio Exterior

- salmão;
- bacalhau;
- camarão;
- merluza;
- origem;
- preço médio importado;
- dólar x importação.

### Tela 7 — Oportunidade por Região

- população;
- renda;
- vendas;
- clientes;
- preço médio kg;
- potencial;
- produto recomendado;
- vendedor/promotor recomendado.

### Tela 8 — IA / Previsão

- previsão;
- probabilidade;
- intervalo mínimo;
- intervalo máximo;
- cenário pessimista;
- cenário base;
- cenário otimista;
- confiança do modelo.

### Tela 9 — Central de Recomendações

- região;
- nota;
- ação;
- justificativa;
- confiança;
- ROI estimado;
- principais fatores;
- feedback.

### Tela 10 — Saúde do ETL

- últimas execuções;
- cargas com erro;
- tempo de execução;
- linhas raw/staging/dw;
- rejeições;
- status de Data Quality.

### Tela 11 — Sandbox What-if

Simulações:

- dólar sobe 5%;
- preço do salmão sobe 8%;
- frango cai 6%;
- milho sobe 10%;
- volume projetado muda quanto?
- cenário muda de 8 para 5?

---

## 45. Alertas Ativos

Canais futuros:

- e-mail;
- webhook;
- Slack/Teams;
- WhatsApp futuro.

Gatilhos:

```text
score_risco >= 80
pressao_custo >= 85
sensibilidade_dolar >= 85
cenario_1_10 <= 3
queda_volume anormal
cliente estratégico em risco
falha crítica no ETL
data quality com erro
```

---

## 46. Feedback das Recomendações

```sql
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
```

Uso:

- medir acurácia das recomendações;
- saber se o gestor executou a ação;
- comparar recomendação x resultado real;
- calibrar pesos e modelos no futuro.

---

## 47. Separação Formal: Cenário, Recomendação e Confiança

| Conceito | Função |
|---|---|
| Cenário | mede a condição da região/produto |
| Recomendação | decide a ação sugerida |
| Confiança | mede o quanto o sistema acredita na recomendação |
| ROI | estima retorno financeiro da ação |

Exemplo:

| Região | Cenário | Recomendação | Confiança | ROI |
|---|---:|---|---:|---:|
| Grande BH | 8 | Promotor | 71% | 275% |
| Norte MG | 6 | Vendedor | 64% | 180% |
| Sul MG | 4 | Corrigir mix | 69% | N/A |

Regra:

> Uma região pode ter cenário bom e, mesmo assim, não recomendar vendedor se já tiver cobertura suficiente.

---

## 48. MVP 1 — Radar Regional Econômico

### Entrega 1 — Fundação

Critérios de aceite:

- estrutura de pastas criada;
- PostgreSQL conectado;
- schemas criados;
- tabelas principais criadas;
- staging padrão definido;
- índices aplicados;
- constraints aplicadas;
- tela inicial Streamlit funcionando;
- `.env` funcionando;
- regra de consumo de dados documentada.

### Entrega 2 — BCB

Critérios de aceite:

- coletor BCB criado;
- histórico carregado desde 2000 ou desde a primeira data disponível;
- dados salvos em `raw`;
- dados tratados em `staging.bcb_series`;
- dados finais em `dw.fato_serie_historica`;
- upsert funcionando;
- controle de carga funcionando com contadores;
- reprocessamento documentado;
- gráfico de dólar, Selic e IPCA funcionando.

### Entrega 3 — IBGE Localidades

Critérios de aceite:

- coletor IBGE Localidades criado;
- UFs carregadas;
- municípios carregados;
- códigos IBGE salvos;
- mapa Brasil/UF funcionando;
- cadastro de região comercial funcionando.

### Entrega 4 — Vendas Internas

Critérios de aceite:

- carga de vendas internas funcionando;
- dimensões populadas;
- CPF/CNPJ sem texto puro no DW;
- fato vendas com FKs;
- fato vendas com hash por documento real;
- lookup de vendedor por data funcionando;
- view analítica sem `SELECT *`;
- materialized view mensal funcionando;
- vendas cruzando com UF/município;
- preço médio kg calculado em view;
- ticket médio calculado em view.

### Entrega 5 — Scores Iniciais

Critérios de aceite:

- normalização 0 a 100 funcionando;
- config de pesos funcionando;
- versão de score ativada apenas com soma 1.00;
- score de oportunidade calculado;
- score de risco calculado;
- cenário 1 a 10 calculado com `GREATEST` e `LEAST`;
- chave única dos scores funcionando;
- upsert de score funcionando.

### Entrega 6 — Recomendações

Critérios de aceite:

- recomendação vendedor/promotor/campanha/monitorar funcionando;
- recomendação referenciando score de origem;
- chave única das recomendações funcionando;
- scores vendedor/promotor/campanha salvos;
- JSONB `principais_fatores` validado;
- ROI estimado calculado via tabela de configuração;
- tela de central de recomendações criada;
- feedback básico criado.

---

## 49. Roadmap com Pré-requisitos

| Versão | Entrega | Pré-requisito |
|---|---|---|
| v1.0 | BCB + IBGE + vendas internas | banco, ETL e Streamlit estáveis |
| v1.1 | CONAB + CEPEA | séries históricas funcionando |
| v1.2 | Comex + FRED/FMI | estrutura de indicadores externos validada |
| v1.3 | ajustes finais de implementação | integridade, hashes, materialized views e auditoria |
| FINAL | fechamento técnico final | MVs corrigidas, staging, DQ, reprocessamento e governança |
| v1.5 | scores avançados | pesos, normalização e dados internos validados |
| v2.0 | ML inicial | histórico suficiente e feature store |
| v2.1 | alertas ativos | recomendações funcionando |
| v2.2 | feedback loop | histórico de feedback acumulado |
| v3.0 | sandbox what-if | scores e elasticidades validados |
| v3.1 | lógica fuzzy/AHP | regras e pesos amadurecidos |
| v4.0 | visão global | fontes internacionais estabilizadas |

---

## 50. Roadmap Estratégico Pós-MVP

Itens importantes, mas que não devem travar o início:

| Área | Melhoria | Quando |
|---|---|---|
| Orquestração | Prefect ou Dagster | depois do primeiro coletor funcionando |
| Segurança | Secret Manager | antes de produção |
| Segurança | Row-Level Security | antes de multiusuário real |
| Performance | TimescaleDB | quando volume exigir |
| Performance | GIN em JSONB | quando houver consulta frequente em JSONB |
| MLOps | Registro de artefatos | quando houver primeiro modelo real |
| MLOps | Monitoramento de drift | depois do primeiro modelo em produção |
| ML | SHAP/LIME | quando houver modelo supervisionado útil |
| Deploy | CI/CD | depois que houver testes |
| Observabilidade | Grafana | se Streamlit não bastar para saúde do ETL |
| Produto | Sandbox What-if | depois dos scores confiáveis |
| Produto | Alertas ativos | depois das recomendações funcionando |

---

## 51. Prioridade Técnica Antes de Implementar

| Prioridade | Ajuste | Quando |
|---:|---|---|
| 1 | `etl_run`, `raw.api_payload` e `etl_controle_carga` conectados | antes do primeiro coletor |
| 2 | staging padrão definido | antes do primeiro coletor |
| 3 | `UNIQUE` com hash na `fato_serie_historica` | antes da primeira carga |
| 4 | `catalogo_fonte` com UNIQUE via COALESCE | Entrega 1 |
| 5 | MVs corrigidas | antes do dashboard |
| 6 | `REFRESH CONCURRENTLY` planejado | antes de uso compartilhado |
| 7 | `fato_vendas` com hash baseado em documento real | antes de carregar vendas |
| 8 | CPF/CNPJ como hash | antes de carregar clientes |
| 9 | lookup histórico de vendedor | antes de carregar vendas |
| 10 | view de vendas sem `SELECT *` | antes da primeira tela comercial |
| 11 | regra de consumo do Streamlit | antes da Entrega 1 |
| 12 | governança de pesos por versão | antes dos scores |
| 13 | `id_score` em recomendações | antes da central de recomendações |
| 14 | scores vendedor/promotor/campanha salvos | Entrega 6 |
| 15 | ROI parametrizado | Entrega 6 |
| 16 | backtesting | antes de confiar em scores para decisão real |
| 17 | autenticação | antes de compartilhar |
| 18 | particionamento | planejar agora, executar se volume exigir |

---

## 52. Ordem Real de Implementação

```text
1. Criar estrutura do projeto
2. Criar schemas no PostgreSQL
3. Criar app.etl_run
4. Criar raw.api_payload
5. Criar app.etl_controle_carga com run_id e contadores
6. Criar app.data_quality_resultado
7. Criar app.catalogo_fonte
8. Criar staging.bcb_series
9. Criar dw.fato_serie_historica com hash
10. Criar índices e constraints
11. Criar coletor BCB
12. Criar upsert de séries históricas
13. Criar primeira tela Streamlit
14. Criar coletor IBGE Localidades
15. Criar dim_geografia e regiões comerciais
16. Criar dimensões de vendas
17. Criar dw.fato_vendas com hash baseado em documento real
18. Criar app.vw_vendas_analitica sem SELECT *
19. Criar materialized views corrigidas
20. Criar config_score_versao
21. Criar config_pesos_score
22. Criar normalização 0 a 100
23. Criar app.fato_score_regional com hash
24. Criar cenário 1 a 10
25. Criar app.config_roi_acao
26. Criar app.fato_recomendacao com hash e id_score
27. Criar feedback de recomendação
28. Criar ROI da recomendação
29. Evoluir para CONAB/CEPEA
30. Evoluir para Comex/FRED
31. Evoluir para feature store
32. Evoluir para ML e backtesting
```

---

## 53. Checklist Final Antes de Codar

```text
[ ] mv_vendas_mensal_geo com GROUP BY correto
[ ] mv_score_regional_atual sem SELECT * e com filtro por CTE
[ ] Índices únicos nas MVs para REFRESH CONCURRENTLY
[ ] UNIQUE em catalogo_fonte com COALESCE
[ ] Padrão de tabela staging definido
[ ] Campos qtd_raw/staging/dw/rejeitados em etl_controle_carga
[ ] Fluxo de reprocessamento documentado
[ ] Governança de pesos por versão
[ ] UNIQUE INDEX de modelo em produção por objetivo
[ ] UNIQUE em backtest_score
[ ] FK id_modelo em backtest_score
[ ] FK id_score em fato_recomendacao
[ ] Decisão sobre documento real em fato_vendas
[ ] Índices de consulta em feature_store_regional
[ ] Lookup de id_vendedor por data no ETL
[ ] CPF/CNPJ como hash em dim_cliente
[ ] Regra de consumo de dados pelo Streamlit documentada
[ ] Tabela config_roi_acao criada
[ ] Scores vendedor/promotor/campanha salvos
```

---

## 54. Conclusão

A versão FINAL fecha os pontos técnicos que ainda poderiam gerar retrabalho na v1.3:

- materialized views corrigidas;
- refresh concorrente planejado;
- staging definido;
- ETL com contadores por camada;
- fluxo de reprocessamento auditável;
- governança de pesos por versão;
- venda com hash baseado em documento real;
- CPF/CNPJ protegido por hash;
- histórico simples de vendedor corretamente usado no ETL;
- recomendações rastreáveis até o score de origem;
- scores concorrentes salvos;
- ROI parametrizado;
- consumo de dados pelo Streamlit padronizado;
- roadmap pós-MVP separado do escopo inicial.

Com isso, o projeto está pronto para sair do planejamento e começar pela implementação da fundação:

> **Etapa 1 — Fundação + Banco + Coletor BCB.**
