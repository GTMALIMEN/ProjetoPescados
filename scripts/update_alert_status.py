from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.services.active_alerts_service import atualizar_status_alerta


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Atualizar status de alerta ativo")
    parser.add_argument("--id", type=int, required=True)
    parser.add_argument("--status", required=True, choices=["ativo", "em_analise", "resolvido", "ignorado"])
    parser.add_argument("--comentario", default="")
    parser.add_argument("--usuario", default="")
    args = parser.parse_args()

    atualizar_status_alerta(
        id_alerta=args.id,
        status_novo=args.status,
        comentario=args.comentario,
        usuario=args.usuario,
    )

    print(f"✅ Alerta {args.id} atualizado para {args.status}")
