from pathlib import Path
import os
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from src.database.connection import get_engine


def main():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        print("DATABASE_URL detectada no ambiente.")
    else:
        print("DATABASE_URL não detectada; usando fallback local do .env.")

    engine = get_engine()
    with engine.begin() as conn:
        print("SELECT 1 =", conn.execute(text("SELECT 1")).scalar())
        print("Banco atual =", conn.execute(text("SELECT current_database()")).scalar())
        print("Usuário atual =", conn.execute(text("SELECT current_user")).scalar())
        print("Versão Postgres =", conn.execute(text("SHOW server_version")).scalar())

    print("✅ Conexão OK.")


if __name__ == "__main__":
    main()
