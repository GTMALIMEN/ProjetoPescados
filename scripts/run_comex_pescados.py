from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.etl.load_fontes_reais import carregar_comex_pescados


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Carregar Comex Stat pescados")
    parser.add_argument("--ano-inicio", type=int, required=True)
    parser.add_argument("--ano-fim", type=int, required=True)
    parser.add_argument("--config", default="config/comex_pescados_ncm.json")
    parser.add_argument("--delay", type=int, default=12, help="Delay em segundos entre grupos/NCMs")
    args = parser.parse_args()

    carregar_comex_pescados(
        args.ano_inicio,
        args.ano_fim,
        args.config,
        delay_entre_grupos=args.delay,
    )
