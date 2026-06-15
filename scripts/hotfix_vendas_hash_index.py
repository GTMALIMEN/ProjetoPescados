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
ALTER TABLE dw.fato_vendas
    ADD COLUMN IF NOT EXISTS chave_venda_hash TEXT;

DROP INDEX IF EXISTS dw.uq_fato_vendas_hash_text;
DROP INDEX IF EXISTS uq_fato_vendas_hash_text;

CREATE UNIQUE INDEX IF NOT EXISTS uq_fato_vendas_hash_text
ON dw.fato_vendas (chave_venda_hash);
"""

def main():
    engine = get_engine()
    with engine.begin() as conn:
        logger.info("Aplicando hotfix do índice único de dw.fato_vendas.chave_venda_hash...")
        conn.execute(text(SQL))
    logger.info("Hotfix aplicado com sucesso.")

if __name__ == "__main__":
    main()
