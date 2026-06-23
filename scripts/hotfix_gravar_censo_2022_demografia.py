from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from src.database.connection import get_engine

sql = """
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.fato_demografia_renda_municipio (
    codigo_ibge TEXT PRIMARY KEY
);

ALTER TABLE app.fato_demografia_renda_municipio
    ADD COLUMN IF NOT EXISTS uf TEXT,
    ADD COLUMN IF NOT EXISTS municipio TEXT,
    ADD COLUMN IF NOT EXISTS ano INTEGER DEFAULT 2022,
    ADD COLUMN IF NOT EXISTS populacao NUMERIC,
    ADD COLUMN IF NOT EXISTS pop_masculina NUMERIC,
    ADD COLUMN IF NOT EXISTS pop_feminina NUMERIC,
    ADD COLUMN IF NOT EXISTS pop_0_14 NUMERIC,
    ADD COLUMN IF NOT EXISTS pop_15_29 NUMERIC,
    ADD COLUMN IF NOT EXISTS pop_30_44 NUMERIC,
    ADD COLUMN IF NOT EXISTS pop_45_59 NUMERIC,
    ADD COLUMN IF NOT EXISTS pop_60_plus NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_masculina NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_feminina NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_0_14 NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_15_29 NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_30_44 NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_45_59 NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_60_plus NUMERIC,
    ADD COLUMN IF NOT EXISTS renda_media NUMERIC,
    ADD COLUMN IF NOT EXISTS renda_classe_a NUMERIC,
    ADD COLUMN IF NOT EXISTS renda_classe_b NUMERIC,
    ADD COLUMN IF NOT EXISTS renda_classe_c NUMERIC,
    ADD COLUMN IF NOT EXISTS renda_classe_de NUMERIC,
    ADD COLUMN IF NOT EXISTS fonte_demografia TEXT,
    ADD COLUMN IF NOT EXISTS fonte_renda TEXT,
    ADD COLUMN IF NOT EXISTS metodo TEXT,
    ADD COLUMN IF NOT EXISTS nivel_confianca INTEGER,
    ADD COLUMN IF NOT EXISTS data_atualizacao TIMESTAMP DEFAULT NOW();

ALTER TABLE app.fato_expansao_municipio
    ADD COLUMN IF NOT EXISTS pop_masculina NUMERIC,
    ADD COLUMN IF NOT EXISTS pop_feminina NUMERIC,
    ADD COLUMN IF NOT EXISTS pop_0_14 NUMERIC,
    ADD COLUMN IF NOT EXISTS pop_15_29 NUMERIC,
    ADD COLUMN IF NOT EXISTS pop_30_44 NUMERIC,
    ADD COLUMN IF NOT EXISTS pop_45_59 NUMERIC,
    ADD COLUMN IF NOT EXISTS pop_60_plus NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_masculina NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_feminina NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_0_14 NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_15_29 NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_30_44 NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_45_59 NUMERIC,
    ADD COLUMN IF NOT EXISTS pct_60_plus NUMERIC,
    ADD COLUMN IF NOT EXISTS fonte_demografia TEXT;

DO $$
BEGIN
    IF to_regclass('app.tmp_censo_2022_demografia') IS NULL THEN
        RAISE EXCEPTION 'Tabela app.tmp_censo_2022_demografia não existe. Neste caso rode novamente scripts/run_censo_2022_demografia_oficial.py';
    END IF;
END $$;

DELETE FROM app.fato_demografia_renda_municipio d
USING app.tmp_censo_2022_demografia t
WHERE d.codigo_ibge = t.codigo_ibge::text;

INSERT INTO app.fato_demografia_renda_municipio (
    codigo_ibge,
    uf,
    municipio,
    ano,
    populacao,
    pop_masculina,
    pop_feminina,
    pop_0_14,
    pop_15_29,
    pop_30_44,
    pop_45_59,
    pop_60_plus,
    pct_masculina,
    pct_feminina,
    pct_0_14,
    pct_15_29,
    pct_30_44,
    pct_45_59,
    pct_60_plus,
    fonte_demografia,
    metodo,
    nivel_confianca,
    data_atualizacao
)
SELECT
    codigo_ibge::text,
    uf,
    municipio,
    2022,
    populacao,
    pop_masculina,
    pop_feminina,
    pop_0_14,
    pop_15_29,
    pop_30_44,
    pop_45_59,
    pop_60_plus,
    pct_masculina,
    pct_feminina,
    pct_0_14,
    pct_15_29,
    pct_30_44,
    pct_45_59,
    pct_60_plus,
    fonte_demografia,
    metodo,
    nivel_confianca,
    NOW()
FROM app.tmp_censo_2022_demografia;

UPDATE app.fato_expansao_municipio e
SET
    pct_masculina = d.pct_masculina,
    pct_feminina = d.pct_feminina,
    pct_0_14 = d.pct_0_14,
    pct_15_29 = d.pct_15_29,
    pct_30_44 = d.pct_30_44,
    pct_45_59 = d.pct_45_59,
    pct_60_plus = d.pct_60_plus,
    pop_masculina = d.pop_masculina,
    pop_feminina = d.pop_feminina,
    pop_0_14 = d.pop_0_14,
    pop_15_29 = d.pop_15_29,
    pop_30_44 = d.pop_30_44,
    pop_45_59 = d.pop_45_59,
    pop_60_plus = d.pop_60_plus,
    fonte_demografia = 'IBGE SIDRA Censo 2022 tabela 9514',
    data_atualizacao = NOW()
FROM app.fato_demografia_renda_municipio d
WHERE e.codigo_ibge::text = d.codigo_ibge
  AND e.uf IN ('MG','SP','RJ','ES');

DROP TABLE IF EXISTS app.tmp_censo_2022_demografia;
"""

with get_engine().begin() as conn:
    conn.execute(text(sql))

print("✅ Dados oficiais do Censo 2022 gravados e aplicados na base de expansão.")
