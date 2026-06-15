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
    sql_file = ROOT_DIR / "src/database/etapa14_alertas_ativos.sql"
    engine = get_engine()

    with engine.begin() as conn:
        logger.info("Aplicando Etapa 14: %s", sql_file)
        conn.execute(text(sql_file.read_text(encoding="utf-8")))

        checks = [
            "app.config_alerta_ativo",
            "app.fato_alerta_ativo",
            "app.historico_alerta_ativo",
            "app.config_notificacao_alerta",
            "app.vw_alertas_ativos_atual",
            "app.vw_alertas_resumo_area",
        ]

        for name in checks:
            exists = conn.execute(text("SELECT to_regclass(:name) IS NOT NULL"), {"name": name}).scalar()
            print(f"{name}: {exists}")

    logger.info("Etapa 14 aplicada com sucesso.")


if __name__ == "__main__":
    main()
