from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.etl.load_vendas import carregar_vendas_arquivo


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Carregar arquivo de vendas internas")
    parser.add_argument("--arquivo", required=True, help="Caminho do arquivo .csv, .xlsx, .xls ou .xlsb")
    parser.add_argument("--sheet", required=False, help="Nome ou índice da aba para Excel")
    args = parser.parse_args()

    carregar_vendas_arquivo(args.arquivo, sheet_name=args.sheet)
