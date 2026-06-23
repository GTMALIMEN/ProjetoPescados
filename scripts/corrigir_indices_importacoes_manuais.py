from __future__ import annotations

from sqlalchemy import text

from src.database.connection import get_engine

TABELAS = [
    ("app.fato_ceagesp_pescados", "uq_ceagesp_hash"),
    ("app.fato_cepea_tilapia_manual", "uq_cepea_manual_chave"),
    ("app.fato_compra_manual", "uq_compra_manual_hash"),
    ("app.fato_previa_vendedores", "uq_previa_vendedores_hash"),
    ("app.fato_receita_manual_expansao", "uq_receita_manual_exp_hash"),
    ("app.fato_mercado_privado", "uq_fato_mercado_privado_hash"),
    ("app.fato_curva_mercado_categoria", "uq_fato_curva_mercado_hash"),
    ("app.dim_key_account_loja", "uq_dim_key_account_hash"),
]


def relation_exists(conn, relation_name: str) -> bool:
    return bool(conn.execute(text("SELECT to_regclass(:name) IS NOT NULL"), {"name": relation_name}).scalar())


def column_exists(conn, table_name: str, column_name: str) -> bool:
    schema, table = table_name.split(".", 1)
    return bool(conn.execute(text("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = :table
              AND column_name = :column
        )
    """), {"schema": schema, "table": table, "column": column_name}).scalar())


def clean_and_index(conn, table_name: str, index_name: str) -> None:
    if not relation_exists(conn, table_name):
        print(f"- {table_name}: tabela não existe, pulando.")
        return
    if not column_exists(conn, table_name, "hash_linha"):
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS hash_linha TEXT"))

    schema = table_name.split(".")[0]
    qualified_index = f"{schema}.{index_name}"

    conn.execute(text(f"DROP INDEX IF EXISTS {qualified_index}"))
    conn.execute(text(f"""
        DELETE FROM {table_name} a
        USING {table_name} b
        WHERE a.ctid < b.ctid
          AND a.hash_linha IS NOT NULL
          AND a.hash_linha = b.hash_linha
    """))
    conn.execute(text(f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} ON {table_name}(hash_linha)"))
    print(f"- {table_name}: índice único em hash_linha OK.")


def main() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        for table_name, index_name in TABELAS:
            clean_and_index(conn, table_name, index_name)
    print("\nConcluído. Agora o ON CONFLICT(hash_linha) está compatível com as bases manuais.")


if __name__ == "__main__":
    main()
