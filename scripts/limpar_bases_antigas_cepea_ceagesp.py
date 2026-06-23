from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from src.database.connection import get_engine


def _exists(conn, relation: str) -> bool:
    return bool(conn.execute(text("SELECT to_regclass(:r) IS NOT NULL"), {"r": relation}).scalar())


def main() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        if _exists(conn, "dw.fato_indicador_setorial"):
            r = conn.execute(text("""
                DELETE FROM dw.fato_indicador_setorial
                WHERE fonte ILIKE '%CEPEA%'
                   OR fonte ILIKE '%CEAGESP%'
                   OR COALESCE(subcategoria, '') ILIKE '%cepea%'
                   OR COALESCE(subcategoria, '') ILIKE '%ceagesp%'
                   OR COALESCE(indicador, '') ILIKE '%cepea%'
                   OR COALESCE(indicador, '') ILIKE '%ceagesp%'
            """))
            print(f"DW antigo CEPEA/CEAGESP removido: {r.rowcount if r.rowcount is not None else 'OK'}")

        # CEPEA manual nova fica preservada. Para zerar e subir de novo, use a importação com substituir_tudo.
        # CEAGESP: remove somente registros que claramente não vieram da importação manual nova.
        if _exists(conn, "app.fato_ceagesp_pescados"):
            conn.execute(text("""
                ALTER TABLE app.fato_ceagesp_pescados
                    ADD COLUMN IF NOT EXISTS fonte_arquivo TEXT,
                    ADD COLUMN IF NOT EXISTS hash_linha TEXT;
            """))
            r = conn.execute(text("""
                DELETE FROM app.fato_ceagesp_pescados
                WHERE COALESCE(fonte, '') NOT ILIKE '%manual%'
                  AND COALESCE(fonte_arquivo, '') = ''
                  AND COALESCE(hash_linha, '') = ''
            """))
            print(f"CEAGESP automatico/antigo removido do app: {r.rowcount if r.rowcount is not None else 'OK'}")

    print("Limpeza concluida. Agora importe CEPEA/CEAGESP pelas bases manuais novas no app.")


if __name__ == "__main__":
    main()
