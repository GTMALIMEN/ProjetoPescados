from pathlib import Path
import sys
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.database.connection import get_engine

SQL = """
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.catalogo_fonte_dados (
    id BIGSERIAL PRIMARY KEY,
    nome_fonte TEXT NOT NULL,
    tipo_fonte TEXT NOT NULL,
    origem TEXT NOT NULL,
    oficial BOOLEAN DEFAULT FALSE,
    url_base TEXT,
    tabela_api TEXT,
    variavel_api TEXT,
    descricao TEXT,
    periodicidade TEXT,
    status TEXT DEFAULT 'ATIVA',
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_catalogo_fonte_nome
ON app.catalogo_fonte_dados (nome_fonte);

CREATE TABLE IF NOT EXISTS app.auditoria_fonte_dados (
    id BIGSERIAL PRIMARY KEY,
    nome_fonte TEXT NOT NULL,
    tabela_destino TEXT,
    status TEXT NOT NULL,
    registros INTEGER DEFAULT 0,
    registros_distintos INTEGER DEFAULT 0,
    duplicatas INTEGER DEFAULT 0,
    nulos_criticos INTEGER DEFAULT 0,
    data_min DATE,
    data_max DATE,
    detalhe TEXT,
    executado_em TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.validacao_dados_resultado (
    id BIGSERIAL PRIMARY KEY,
    grupo_validacao TEXT NOT NULL,
    tabela TEXT NOT NULL,
    regra TEXT NOT NULL,
    status TEXT NOT NULL,
    qtd_problemas INTEGER DEFAULT 0,
    detalhe TEXT,
    executado_em TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.validacao_dados_rejeicoes (
    id BIGSERIAL PRIMARY KEY,
    grupo_validacao TEXT NOT NULL,
    tabela TEXT NOT NULL,
    regra TEXT NOT NULL,
    chave TEXT,
    coluna TEXT,
    valor TEXT,
    motivo TEXT,
    criado_em TIMESTAMP DEFAULT NOW()
);

INSERT INTO app.catalogo_fonte_dados (
    nome_fonte,
    tipo_fonte,
    origem,
    oficial,
    url_base,
    tabela_api,
    variavel_api,
    descricao,
    periodicidade
)
VALUES
(
    'IBGE SIDRA - População e Demografia',
    'API',
    'IBGE/SIDRA',
    TRUE,
    'https://apisidra.ibge.gov.br/',
    '9514',
    'Sexo, idade e população',
    'Censo 2022 - estrutura demográfica municipal',
    'Censo'
),
(
    'IBGE SIDRA - Renda',
    'API',
    'IBGE/SIDRA',
    TRUE,
    'https://apisidra.ibge.gov.br/',
    '10295',
    'Rendimento nominal médio/mediano domiciliar per capita',
    'Censo 2022 - renda municipal',
    'Censo'
),
(
    'IBGE - PIB dos Municípios',
    'API/arquivo oficial',
    'IBGE',
    TRUE,
    'https://www.ibge.gov.br/',
    NULL,
    'PIB municipal',
    'Produto Interno Bruto dos Municípios',
    'Anual'
),
(
    'Banco Central SGS',
    'API',
    'Banco Central do Brasil',
    TRUE,
    'https://api.bcb.gov.br/',
    NULL,
    'Dólar, Selic, IPCA e demais séries',
    'Séries temporais macroeconômicas',
    'Diária/Mensal'
),
(
    'CEAGESP Pescados',
    'Web scraping/API indireta',
    'CEAGESP',
    TRUE,
    NULL,
    NULL,
    'Cotações de pescados',
    'Referência de preço de mercado',
    'Diária/Semanal'
),
(
    'Scanntech / Mercado Privado',
    'Manual',
    'Base privada',
    FALSE,
    NULL,
    NULL,
    'Sell-out / mercado privado',
    'Base privada importada manualmente',
    'Mensal'
),
(
    'Bases internas manuais',
    'Manual',
    'GTM / Usuário',
    FALSE,
    NULL,
    NULL,
    'Receita, compras, prévias e key accounts',
    'Dados internos importados manualmente',
    'Sob demanda'
)
ON CONFLICT (nome_fonte) DO UPDATE SET
    tipo_fonte = EXCLUDED.tipo_fonte,
    origem = EXCLUDED.origem,
    oficial = EXCLUDED.oficial,
    url_base = EXCLUDED.url_base,
    tabela_api = EXCLUDED.tabela_api,
    variavel_api = EXCLUDED.variavel_api,
    descricao = EXCLUDED.descricao,
    periodicidade = EXCLUDED.periodicidade,
    status = 'ATIVA';
"""

with get_engine().begin() as conn:
    conn.execute(text(SQL))

print("✅ Estrutura de auditoria e catálogo de fontes criada/atualizada.")
