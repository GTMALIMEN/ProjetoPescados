
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(dotenv_path=Path(".env"))

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL nao encontrada no .env ou secrets.")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

if DATABASE_URL.startswith("postgresql+psycopg2://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)

engine = create_engine(DATABASE_URL)

sql = """
UPDATE app.fato_receita_manual_expansao
SET categoria_pescado =
    CASE
        WHEN normalizado LIKE '%TILAPIA%' THEN 'TILAPIA'
        WHEN normalizado LIKE '%SALMAO%' THEN 'SALMAO'
        WHEN normalizado LIKE '%CAMARAO%' THEN 'CAMARAO'
        WHEN normalizado LIKE '%PIRAMUTABA%' THEN 'PIRAMUTABA'
        WHEN normalizado LIKE '%POLACA%' THEN 'POLACA'
        WHEN normalizado LIKE '%MERLUZA%' THEN 'MERLUZA'
        WHEN normalizado LIKE '%PANGA%' OR normalizado LIKE '%PANGASIUS%' THEN 'PANGA'
        WHEN normalizado LIKE '%PEIXES PARA%' THEN 'OUTROS PEIXES'
        ELSE UPPER(categoria_pescado)
    END
FROM (
    SELECT
        hash_linha,
        UPPER(
            TRANSLATE(
                COALESCE(grupo_produto, '') || ' ' || COALESCE(categoria_pescado, ''),
                '??????????????????????????????????????????????',
                'AAAAAEEEEIIIIOOOOOUUUUCaaaaaeeeeiiiiooooouuuuc'
            )
        ) AS normalizado
    FROM app.fato_receita_manual_expansao
) x
WHERE app.fato_receita_manual_expansao.hash_linha = x.hash_linha;
"""

with engine.begin() as conn:
    result = conn.execute(text(sql))
    print(f"Linhas revisadas: {result.rowcount}")
