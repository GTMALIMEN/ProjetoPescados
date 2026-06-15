from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.etl.load_ibge import carregar_ibge_localidades


if __name__ == "__main__":
    carregar_ibge_localidades()
