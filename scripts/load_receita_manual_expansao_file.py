
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.etl.load_receita_manual_expansao import carregar_receita_manual_expansao


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Carregar receita manual da Análise de Expansão")
    parser.add_argument("--arquivo", required=True, help="CSV/XLSX com parceiro, cidade, estado, data_competencia, grupo_produto, vlr_total_liquido")
    args = parser.parse_args()

    resumo = carregar_receita_manual_expansao(args.arquivo)
    print("\nResumo da carga:")
    for k, v in resumo.items():
        print(f"- {k}: {v}")


if __name__ == "__main__":
    main()
