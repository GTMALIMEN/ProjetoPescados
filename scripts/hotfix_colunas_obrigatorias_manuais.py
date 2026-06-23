from pathlib import Path
import sys
import pandas as pd
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.database.connection import get_engine

sql = """
CREATE SCHEMA IF NOT EXISTS app;

-- COMPRA MANUAL
ALTER TABLE app.fato_compra_manual
    ADD COLUMN IF NOT EXISTS data_competencia DATE,
    ADD COLUMN IF NOT EXISTS quantidade NUMERIC,
    ADD COLUMN IF NOT EXISTS valor_total NUMERIC,
    ADD COLUMN IF NOT EXISTS cidade TEXT,
    ADD COLUMN IF NOT EXISTS uf TEXT,
    ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW();

UPDATE app.fato_compra_manual
SET data_competencia = COALESCE(data_competencia, data, mes)
WHERE data_competencia IS NULL;

UPDATE app.fato_compra_manual
SET quantidade = COALESCE(quantidade, quantidade_comprada)
WHERE quantidade IS NULL
  AND EXISTS (
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = 'app'
        AND table_name = 'fato_compra_manual'
        AND column_name = 'quantidade_comprada'
  );

UPDATE app.fato_compra_manual
SET valor_total = COALESCE(valor_total, quantidade * preco_compra)
WHERE valor_total IS NULL
  AND quantidade IS NOT NULL
  AND preco_compra IS NOT NULL;


-- CEAGESP
ALTER TABLE app.fato_ceagesp_pescados
    ADD COLUMN IF NOT EXISTS data_cotacao DATE,
    ADD COLUMN IF NOT EXISTS preco_min NUMERIC,
    ADD COLUMN IF NOT EXISTS preco_max NUMERIC,
    ADD COLUMN IF NOT EXISTS fonte_arquivo TEXT,
    ADD COLUMN IF NOT EXISTS hash_linha TEXT,
    ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW();

UPDATE app.fato_ceagesp_pescados
SET data_cotacao = COALESCE(data_cotacao, data_referencia, data_coleta::date)
WHERE data_cotacao IS NULL;

UPDATE app.fato_ceagesp_pescados
SET preco_min = COALESCE(preco_min, preco_minimo)
WHERE preco_min IS NULL
  AND EXISTS (
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = 'app'
        AND table_name = 'fato_ceagesp_pescados'
        AND column_name = 'preco_minimo'
  );

UPDATE app.fato_ceagesp_pescados
SET preco_max = COALESCE(preco_max, preco_maximo)
WHERE preco_max IS NULL
  AND EXISTS (
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = 'app'
        AND table_name = 'fato_ceagesp_pescados'
        AND column_name = 'preco_maximo'
  );


-- PRÉVIA VENDEDORES
ALTER TABLE app.fato_previa_vendedores
    ADD COLUMN IF NOT EXISTS quantidade NUMERIC,
    ADD COLUMN IF NOT EXISTS receita NUMERIC,
    ADD COLUMN IF NOT EXISTS cidade TEXT,
    ADD COLUMN IF NOT EXISTS uf TEXT,
    ADD COLUMN IF NOT EXISTS categoria TEXT,
    ADD COLUMN IF NOT EXISTS status TEXT,
    ADD COLUMN IF NOT EXISTS fonte_arquivo TEXT,
    ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP DEFAULT NOW();

UPDATE app.fato_previa_vendedores
SET quantidade = COALESCE(quantidade, quantidade_vendida)
WHERE quantidade IS NULL
  AND EXISTS (
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = 'app'
        AND table_name = 'fato_previa_vendedores'
        AND column_name = 'quantidade_vendida'
  );

UPDATE app.fato_previa_vendedores
SET receita = COALESCE(receita, receita_total)
WHERE receita IS NULL
  AND EXISTS (
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = 'app'
        AND table_name = 'fato_previa_vendedores'
        AND column_name = 'receita_total'
  );

UPDATE app.fato_previa_vendedores
SET receita = quantidade * preco
WHERE receita IS NULL
  AND quantidade IS NOT NULL
  AND preco IS NOT NULL;
"""

with get_engine().begin() as conn:
    conn.execute(text(sql))

print("✅ Colunas obrigatórias faltantes criadas e compatibilizadas.")
