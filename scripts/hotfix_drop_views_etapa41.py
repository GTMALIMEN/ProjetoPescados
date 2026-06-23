from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from src.database.connection import get_engine

sql = """
DROP VIEW IF EXISTS app.vw_key_account_ibge CASCADE;
DROP VIEW IF EXISTS app.vw_curva_mercado_categoria CASCADE;
DROP VIEW IF EXISTS app.vw_mercado_privado_resumo CASCADE;
DROP VIEW IF EXISTS app.vw_importacao_manual_resumo CASCADE;
DROP VIEW IF EXISTS app.vw_idc_completo_atual CASCADE;
"""

with get_engine().begin() as conn:
    conn.execute(text(sql))

print("✅ Views antigas da Etapa 41 removidas com sucesso.")
