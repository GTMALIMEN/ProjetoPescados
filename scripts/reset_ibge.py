from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from src.database.connection import get_engine
from src.utils.logs import get_logger

logger = get_logger(__name__)

SQL = """
DELETE FROM staging.ibge_municipios;
DELETE FROM staging.ibge_ufs;
DELETE FROM dw.dim_geografia;
DELETE FROM app.dim_regiao_comercial;
"""

def main():
    engine = get_engine()
    with engine.begin() as conn:
        logger.info("Limpando apenas dados IBGE/geografia...")
        conn.execute(text(SQL))
    logger.info("Dados IBGE/geografia removidos. Agora rode: python scripts\\run_ibge_localidades.py")

if __name__ == "__main__":
    main()
