from pathlib import Path
import sys
import json

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.services.executive_report_service import gerar_relatorio_executivo


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gerar relatório executivo automático")
    parser.add_argument("--uf", default="MG")
    parser.add_argument("--usuario", default="")
    parser.add_argument("--nao-salvar-banco", action="store_true")
    args = parser.parse_args()

    rel = gerar_relatorio_executivo(
        uf=args.uf,
        salvar_banco=not args.nao_salvar_banco,
        usuario=args.usuario or None,
    )

    print("\n✅ Relatório executivo gerado")
    print(f"ID: {rel['id']}")
    print(f"Excel: {rel['excel_path']}")
    print(f"HTML: {rel['html_path']}")
    print("\nMensagem WhatsApp:\n")
    print(rel["whatsapp"])
    print("\nIndicadores:")
    print(json.dumps(rel["indicadores"], ensure_ascii=False, indent=2))
