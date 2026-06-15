from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from src.database.connection import get_engine
from src.utils.logs import get_logger

logger = get_logger(__name__)


def main():
    sql_file = ROOT_DIR / "src/database/etapa13_whatif.sql"
    engine = get_engine()

    with engine.begin() as conn:
        logger.info("Aplicando Etapa 13: %s", sql_file)
        conn.execute(text(sql_file.read_text(encoding="utf-8")))

        checks = [
            "app.fato_simulacao_whatif",
            "app.vw_whatif_ultimas_simulacoes",
            "app.vw_whatif_resumo_regiao",
        ]

        for name in checks:
            exists = conn.execute(text("SELECT to_regclass(:name) IS NOT NULL"), {"name": name}).scalar()
            print(f"{name}: {exists}")

    logger.info("Etapa 13 aplicada com sucesso.")


if __name__ == "__main__":
    main()
