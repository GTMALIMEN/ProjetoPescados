from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from src.database.connection import get_engine

sql = """
-- Corrige percentuais de faixa etária para fecharem 100%
-- Usa como denominador a soma das faixas carregadas do SIDRA 9514.

WITH base AS (
    SELECT
        codigo_ibge,
        COALESCE(pop_0_14, 0)
      + COALESCE(pop_15_29, 0)
      + COALESCE(pop_30_44, 0)
      + COALESCE(pop_45_59, 0)
      + COALESCE(pop_60_plus, 0) AS total_faixas
    FROM app.fato_demografia_renda_municipio
)
UPDATE app.fato_demografia_renda_municipio d
SET
    pct_0_14 = CASE WHEN b.total_faixas > 0 THEN d.pop_0_14 / b.total_faixas * 100 ELSE NULL END,
    pct_15_29 = CASE WHEN b.total_faixas > 0 THEN d.pop_15_29 / b.total_faixas * 100 ELSE NULL END,
    pct_30_44 = CASE WHEN b.total_faixas > 0 THEN d.pop_30_44 / b.total_faixas * 100 ELSE NULL END,
    pct_45_59 = CASE WHEN b.total_faixas > 0 THEN d.pop_45_59 / b.total_faixas * 100 ELSE NULL END,
    pct_60_plus = CASE WHEN b.total_faixas > 0 THEN d.pop_60_plus / b.total_faixas * 100 ELSE NULL END,
    fonte_demografia = 'IBGE SIDRA Censo 2022 tabela 9514',
    metodo = COALESCE(d.metodo, 'sidra_api_9514') || '_faixas_normalizadas',
    data_atualizacao = NOW()
FROM base b
WHERE d.codigo_ibge = b.codigo_ibge
  AND b.total_faixas > 0;

UPDATE app.fato_expansao_municipio e
SET
    pct_0_14 = d.pct_0_14,
    pct_15_29 = d.pct_15_29,
    pct_30_44 = d.pct_30_44,
    pct_45_59 = d.pct_45_59,
    pct_60_plus = d.pct_60_plus,
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
"""

with get_engine().begin() as conn:
    conn.execute(text(sql))

print("✅ Percentuais de faixa etária corrigidos para fechar 100%.")
