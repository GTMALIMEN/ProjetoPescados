from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import psycopg
from psycopg import sql

from src.config.settings import settings


def main():
    """
    Cria o banco configurado no .env caso ele ainda não exista.

    Este script conecta no banco administrativo padrão "postgres"
    e cria o banco DB_NAME definido no .env.
    """

    db_name = settings.db_name

    conninfo = {
        "host": settings.db_host,
        "port": settings.db_port,
        "dbname": "postgres",
        "user": settings.db_user,
        "password": settings.db_password,
    }

    print(f"Conectando no PostgreSQL em {settings.db_host}:{settings.db_port} como {settings.db_user}...")

    with psycopg.connect(**conninfo, autocommit=True) as conn:
        exists = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,),
        ).fetchone()

        if exists:
            print(f"✅ Banco já existe: {db_name}")
            return

        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
        print(f"✅ Banco criado: {db_name}")


if __name__ == "__main__":
    main()
