
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.etl.load_expansao_publica import carregar_expansao_publica


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Carregar dados públicos da Análise de Expansão V2")
    parser.add_argument("--estados", default="MG,SP,RJ,ES", help="Lista de UFs separadas por vírgula")
    parser.add_argument("--sem-pib", action="store_true", help="Não tentar carregar PIB SIDRA")
    args = parser.parse_args()

    estados = [x.strip().upper() for x in args.estados.split(",") if x.strip()]
    resumo = carregar_expansao_publica(estados=estados, carregar_pib=not args.sem_pib)

    print("\nResumo da carga pública de expansão:")
    for key, value in resumo.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
