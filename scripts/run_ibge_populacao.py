from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.etl.load_ibge_indicadores import carregar_populacao_estimada


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Carregar população estimada do IBGE/SIDRA")
    parser.add_argument("--periodo", required=False, help="Ano SIDRA. Ex.: 2025. Se omitir, usa último período disponível.")
    args = parser.parse_args()

    carregar_populacao_estimada(periodo=args.periodo)
