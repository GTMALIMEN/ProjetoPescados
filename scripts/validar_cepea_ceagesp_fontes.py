from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from sqlalchemy import text
from src.database.connection import get_engine


def _exists(conn, relation: str) -> bool:
    return bool(conn.execute(text("SELECT to_regclass(:r) IS NOT NULL"), {"r": relation}).scalar())


def main() -> None:
    engine = get_engine()
    erros = []
    alertas = []

    with engine.begin() as conn:
        if _exists(conn, "app.fato_cepea_tilapia_manual"):
            cepea = pd.read_sql(text("""
                SELECT COUNT(*) AS total,
                       COUNT(*) FILTER (WHERE preco_ajustado IS NULL OR preco_ajustado <= 0) AS preco_invalido,
                       COUNT(*) FILTER (WHERE data_fim_periodo IS NULL) AS data_invalida
                FROM app.fato_cepea_tilapia_manual
            """), conn).iloc[0]
            if int(cepea["total"] or 0) == 0:
                alertas.append("CEPEA Manual sem registros. Importe a base nova em Importações Manuais.")
            if int(cepea["preco_invalido"] or 0) > 0:
                erros.append("CEPEA Manual possui preço_ajustado inválido.")
            if int(cepea["data_invalida"] or 0) > 0:
                erros.append("CEPEA Manual possui data_fim_periodo inválida.")
        else:
            alertas.append("Tabela app.fato_cepea_tilapia_manual não existe.")

        if _exists(conn, "app.fato_ceagesp_pescados"):
            conn.execute(text("""
                ALTER TABLE app.fato_ceagesp_pescados
                    ADD COLUMN IF NOT EXISTS fonte_arquivo TEXT,
                    ADD COLUMN IF NOT EXISTS hash_linha TEXT;
            """))
            ceagesp = pd.read_sql(text("""
                SELECT COUNT(*) AS total,
                       COUNT(*) FILTER (WHERE preco_comum IS NULL OR preco_comum <= 0) AS preco_invalido,
                       COUNT(*) FILTER (WHERE data_referencia IS NULL) AS data_invalida,
                       COUNT(*) FILTER (
                         WHERE COALESCE(fonte, '') NOT ILIKE '%manual%'
                           AND COALESCE(fonte_arquivo, '') = ''
                           AND COALESCE(hash_linha, '') = ''
                       ) AS antigos
                FROM app.fato_ceagesp_pescados
            """), conn).iloc[0]
            if int(ceagesp["total"] or 0) == 0:
                alertas.append("CEAGESP Manual sem registros. Importe a base nova em Importações Manuais.")
            if int(ceagesp["preco_invalido"] or 0) > 0:
                erros.append("CEAGESP Manual possui preço_comum inválido.")
            if int(ceagesp["data_invalida"] or 0) > 0:
                erros.append("CEAGESP Manual possui data_referencia inválida.")
            if int(ceagesp["antigos"] or 0) > 0:
                erros.append("CEAGESP possui registros antigos/automáticos. Rode scripts/limpar_bases_antigas_cepea_ceagesp.py e reimporte a base manual.")
        else:
            alertas.append("Tabela app.fato_ceagesp_pescados não existe.")

        if _exists(conn, "dw.fato_indicador_setorial"):
            legado = pd.read_sql(text("""
                SELECT fonte, subcategoria, COUNT(*) AS qtd
                FROM dw.fato_indicador_setorial
                WHERE (fonte ILIKE '%CEPEA%' OR fonte ILIKE '%CEAGESP%')
                  AND COALESCE(subcategoria, '') <> 'oficial_arquivo_manual'
                GROUP BY fonte, subcategoria
                ORDER BY qtd DESC
            """), conn)
            if not legado.empty:
                erros.append("DW ainda contém CEPEA/CEAGESP antigo, proxy ou automático.")
                print(legado.to_string(index=False))

    print("\n=== VALIDAÇÃO CEPEA/CEAGESP MANUAL ===")
    if erros:
        print("ERROS:")
        for e in erros:
            print(" -", e)
    if alertas:
        print("ALERTAS:")
        for a in alertas:
            print(" -", a)
    if not erros:
        print("OK: nenhuma base CEPEA/CEAGESP antiga foi autorizada pelo validador.")
    raise SystemExit(1 if erros else 0)


if __name__ == "__main__":
    main()
