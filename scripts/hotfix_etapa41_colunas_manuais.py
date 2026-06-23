from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from src.database.connection import get_engine

sql = """
CREATE SCHEMA IF NOT EXISTS app;

-- Remove views dependentes antes de ajustar tabelas
DROP VIEW IF EXISTS app.vw_key_account_ibge CASCADE;
DROP VIEW IF EXISTS app.vw_curva_mercado_categoria CASCADE;
DROP VIEW IF EXISTS app.vw_mercado_privado_resumo CASCADE;
DROP VIEW IF EXISTS app.vw_importacao_manual_resumo CASCADE;
DROP VIEW IF EXISTS app.vw_idc_completo_atual CASCADE;

-- Garante estrutura da curva de mercado
CREATE TABLE IF NOT EXISTS app.fato_curva_mercado_categoria (
    id BIGSERIAL PRIMARY KEY
);

ALTER TABLE app.fato_curva_mercado_categoria
    ADD COLUMN IF NOT EXISTS data_competencia DATE,
    ADD COLUMN IF NOT EXISTS uf TEXT,
    ADD COLUMN IF NOT EXISTS cidade TEXT,
    ADD COLUMN IF NOT EXISTS microrregiao TEXT,
    ADD COLUMN IF NOT EXISTS categoria TEXT,
    ADD COLUMN IF NOT EXISTS produto TEXT,
    ADD COLUMN IF NOT EXISTS valor NUMERIC,
    ADD COLUMN IF NOT EXISTS volume NUMERIC,
    ADD COLUMN IF NOT EXISTS preco_medio NUMERIC,
    ADD COLUMN IF NOT EXISTS fonte TEXT DEFAULT 'manual_upload',
    ADD COLUMN IF NOT EXISTS fonte_arquivo TEXT,
    ADD COLUMN IF NOT EXISTS hash_linha TEXT,
    ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS uq_curva_mercado_hash
ON app.fato_curva_mercado_categoria (hash_linha)
WHERE hash_linha IS NOT NULL;

-- Garante estrutura do mercado privado / Scanntech
CREATE TABLE IF NOT EXISTS app.fato_mercado_privado (
    id BIGSERIAL PRIMARY KEY
);

ALTER TABLE app.fato_mercado_privado
    ADD COLUMN IF NOT EXISTS data_competencia DATE,
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
    ADD COLUMN IF NOT EXISTS qtd_lojas NUMERIC,
    ADD COLUMN IF NOT EXISTS fonte TEXT DEFAULT 'manual_upload',
    ADD COLUMN IF NOT EXISTS fonte_arquivo TEXT,
    ADD COLUMN IF NOT EXISTS hash_linha TEXT,
    ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS uq_mercado_privado_hash
ON app.fato_mercado_privado (hash_linha)
WHERE hash_linha IS NOT NULL;

-- Garante estrutura Key Account
CREATE TABLE IF NOT EXISTS app.dim_key_account_loja (
    id BIGSERIAL PRIMARY KEY
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
    ADD COLUMN IF NOT EXISTS fonte_arquivo TEXT,
    ADD COLUMN IF NOT EXISTS hash_linha TEXT,
    ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS uq_key_account_hash
ON app.dim_key_account_loja (hash_linha)
WHERE hash_linha IS NOT NULL;
"""

with get_engine().begin() as conn:
    conn.execute(text(sql))

print("✅ Hotfix aplicado: tabelas manuais corrigidas e views antigas removidas.")
