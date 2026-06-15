from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.etl.load_fontes_reais import carregar_arquivo_fonte_real


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Carregar arquivo CONAB baixado")
    parser.add_argument("--arquivo", required=True)
    parser.add_argument("--categoria", default="graos_racao")
    parser.add_argument("--produto-default", default="CONAB")
    parser.add_argument("--uf-default", default="MG")
    args = parser.parse_args()

    carregar_arquivo_fonte_real(
        arquivo=args.arquivo,
        fonte="CONAB",
        categoria_default=args.categoria,
        produto_default=args.produto_default,
        uf_default=args.uf_default,
    )
