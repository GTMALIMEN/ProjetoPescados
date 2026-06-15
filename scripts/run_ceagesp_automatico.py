
from pathlib import Path
import sys
import json

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text

from src.collectors.ceagesp_collector import CeagespCollector
from src.database.connection import get_engine


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Carregar CEAGESP Pescados automaticamente, sem travar o pipeline")
    parser.add_argument("--dias-busca", type=int, default=21)
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--max-tentativas", type=int, default=12)
    args = parser.parse_args()

    collector = CeagespCollector(timeout=args.timeout, max_tentativas=args.max_tentativas)
    df, meta = collector.coletar_pescados_automatico(dias_busca=args.dias_busca)

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO raw.fonte_automatica_payload (fonte, endpoint, status, detalhe, payload_json)
            VALUES (:fonte, :endpoint, :status, :detalhe, CAST(:payload_json AS JSONB))
        """), {
            "fonte": "CEAGESP Pescados",
            "endpoint": meta.get("url"),
            "status": meta.get("status"),
            "detalhe": meta.get("observacao") or meta.get("estrategia") or "",
            "payload_json": json.dumps(meta, ensure_ascii=False, default=str),
        })

    if df.empty:
        print("⚠️ Nenhum dado CEAGESP capturado automaticamente.")
        print("Status:", meta.get("status"))
        print("Tentativas:", meta.get("tentativas"))
        print("Detalhe:", meta.get("observacao"))
        print("Forms detectados:", meta.get("forms_detectados"))
        print("Opções detectadas:", meta.get("opcoes_detectadas"))
        print("\nO pipeline continua normalmente. A CEAGESP não vai mais travar o terminal.")
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

    print(f"✅ CEAGESP Pescados automático carregado: {len(records)} registros")
    print("Estratégia:", meta.get("estrategia"))
    print("URL:", meta.get("url_usada") or meta.get("url"))


if __name__ == "__main__":
    main()
