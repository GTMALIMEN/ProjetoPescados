
from pathlib import Path
import sys
import json

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text

from src.collectors.ceagesp_playwright_collector import CeagespPlaywrightCollector
from src.database.connection import get_engine


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Carregar CEAGESP Pescados via navegador Playwright")
    parser.add_argument("--dias-busca", type=int, default=60)
    parser.add_argument("--max-datas", type=int, default=12)
    parser.add_argument("--visivel", action="store_true", help="Abre o navegador visível para depuração.")
    args = parser.parse_args()

    collector = CeagespPlaywrightCollector(headless=not args.visivel)
    df, meta = collector.coletar(dias_busca=args.dias_busca, max_datas=args.max_datas)

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO raw.fonte_automatica_payload (fonte, endpoint, status, detalhe, payload_json)
            VALUES (:fonte, :endpoint, :status, :detalhe, CAST(:payload_json AS JSONB))
        """), {
            "fonte": "CEAGESP Pescados Playwright",
            "endpoint": meta.get("url"),
            "status": meta.get("status"),
            "detalhe": meta.get("observacao") or meta.get("modo") or "",
            "payload_json": json.dumps(meta, ensure_ascii=False, default=str),
        })

    if df.empty:
        print("⚠️ Nenhum dado CEAGESP capturado via Playwright.")
        print("Status:", meta.get("status"))
        print("Detalhe:", meta.get("observacao"))
        print("Erros:", meta.get("erros"))
        if meta.get("status") == "FALTA_DEPENDENCIA":
            print("\nRode:")
            print(r"scripts\instalar_playwright_ceagesp.bat")
        return

    records = df.to_dict(orient="records")

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.fato_ceagesp_pescados (
                chave_registro, data_coleta, data_referencia, categoria, produto, classificacao, unidade,
                preco_minimo, preco_comum, preco_maximo, fonte, url_fonte, hash_carga
            )
            VALUES (
                :chave_registro, :data_coleta, :data_referencia, :categoria, :produto, :classificacao, :unidade,
                :preco_minimo, :preco_comum, :preco_maximo, :fonte, :url_fonte, :hash_carga
            )
            ON CONFLICT (chave_registro)
            DO UPDATE SET
                preco_minimo = EXCLUDED.preco_minimo,
                preco_comum = EXCLUDED.preco_comum,
                preco_maximo = EXCLUDED.preco_maximo,
                data_coleta = EXCLUDED.data_coleta,
                url_fonte = EXCLUDED.url_fonte,
                hash_carga = EXCLUDED.hash_carga;
        """), records)

    print(f"✅ CEAGESP Playwright carregado: {len(records)} registros")
    print("Data referência:", meta.get("data_referencia_br"))
    print("URL:", meta.get("url"))


if __name__ == "__main__":
    main()
