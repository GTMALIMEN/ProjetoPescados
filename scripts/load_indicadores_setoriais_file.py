from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.etl.load_indicadores_setoriais import carregar_indicadores_setoriais_arquivo


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Carregar indicadores setoriais")
    parser.add_argument("--arquivo", required=True, help="Arquivo .csv/.xlsx/.xlsb")
    args = parser.parse_args()

    carregar_indicadores_setoriais_arquivo(args.arquivo)
