from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from src.database.connection import get_engine
from src.utils.logs import get_logger

logger = get_logger(__name__)
SQL_PATH = ROOT_DIR / "src" / "database" / "auditoria.sql"


def main():
    engine = get_engine()
    with engine.begin() as conn:
        logger.info("Aplicando correção de auditoria/saúde atual: %s", SQL_PATH)
        conn.execute(text(SQL_PATH.read_text(encoding="utf-8")))
    logger.info("Correção de auditoria/saúde aplicada com sucesso.")


if __name__ == "__main__":
    main()
