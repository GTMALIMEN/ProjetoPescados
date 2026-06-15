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
DROP SCHEMA IF EXISTS app CASCADE;
DROP SCHEMA IF EXISTS raw CASCADE;
DROP SCHEMA IF EXISTS staging CASCADE;
DROP SCHEMA IF EXISTS dw CASCADE;
DROP SCHEMA IF EXISTS ml CASCADE;
"""

def main():
    engine = get_engine()
    with engine.begin() as conn:
        logger.info("Limpando schemas do projeto...")
        conn.execute(text(SQL))
    logger.info("Schemas removidos. Agora rode: python scripts\\init_db.py")

if __name__ == "__main__":
    main()
