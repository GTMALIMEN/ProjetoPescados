from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.etl.load_importadores_manuais import carregar_compra_manual


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Carregar base de compra manual')
    parser.add_argument('--arquivo', required=True, help='Caminho do arquivo .xlsx/.csv')
    args = parser.parse_args()
    resumo = carregar_compra_manual(args.arquivo)
    print('\nResumo da carga:')
    for k, v in resumo.items():
        print(f'- {k}: {v}')


if __name__ == '__main__':
    main()
