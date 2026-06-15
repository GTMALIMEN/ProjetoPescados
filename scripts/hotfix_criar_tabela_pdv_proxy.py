from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from src.database.connection import get_engine

sql = """
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.fato_pdv_proxy_municipio (
    codigo_ibge TEXT PRIMARY KEY,
    uf TEXT,
    municipio TEXT,
    supermercados INTEGER DEFAULT 0,
    restaurantes INTEGER DEFAULT 0,
    peixarias INTEGER DEFAULT 0,
    outros_pdv INTEGER DEFAULT 0,
    fonte_pdv TEXT,
    metodo TEXT,
    nivel_confianca NUMERIC,
    payload_json JSONB,
    data_atualizacao TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pdv_proxy_uf
ON app.fato_pdv_proxy_municipio (uf);

CREATE INDEX IF NOT EXISTS idx_pdv_proxy_municipio
ON app.fato_pdv_proxy_municipio (municipio);

CREATE OR REPLACE VIEW app.vw_pdv_proxy_municipio AS
SELECT
    codigo_ibge,
    uf,
    municipio,
    supermercados,
    restaurantes,
    peixarias,
    outros_pdv,
    COALESCE(supermercados, 0)
      + COALESCE(restaurantes, 0)
      + COALESCE(peixarias, 0)
      + COALESCE(outros_pdv, 0) AS total_pdv,
    fonte_pdv,
    metodo,
    nivel_confianca,
    payload_json,
    data_atualizacao
FROM app.fato_pdv_proxy_municipio;
"""

with get_engine().begin() as conn:
    conn.execute(text(sql))

print("✅ Tabela app.fato_pdv_proxy_municipio criada/validada.")
