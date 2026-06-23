
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.services.importacoes_manuais_service import aplicar_estruturas_importacoes_manuais

if __name__ == "__main__":
    aplicar_estruturas_importacoes_manuais()
    print("✅ Estruturas das Etapas 35-40 aplicadas.")
