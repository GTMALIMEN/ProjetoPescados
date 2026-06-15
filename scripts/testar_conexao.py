from pathlib import Path
import os
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from src.database.connection import get_engine


def main():
    if os.getenv("DATABASE_URL"):
        print("DATABASE_URL detectada. Usando banco online/Supabase.")
    else:
        print("DATABASE_URL não detectada. Usando .env local.")

    engine = get_engine()
    with engine.begin() as conn:
        print("SELECT 1 =", conn.execute(text("SELECT 1")).scalar())
        print("Banco atual =", conn.execute(text("SELECT current_database()")).scalar())
        print("Usuário atual =", conn.execute(text("SELECT current_user")).scalar())
        print("Versão Postgres =", conn.execute(text("SHOW server_version")).scalar())

    print("✅ Conexão OK.")


if __name__ == "__main__":
    main()
