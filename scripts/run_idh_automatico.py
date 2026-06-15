
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.etl.load_idh_automatico import carregar_idh_automatico


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Carregar IDH/IDHM automaticamente")
    parser.add_argument("--url", action="append", help="URL direta para ZIP/CSV/XLSX/HTML com IDHM. Pode repetir.")
    args = parser.parse_args()

    resumo = carregar_idh_automatico(extra_urls=args.url)

    print("\nResumo IDH/IDHM automático:")
    print(f"- status: {resumo.get('status')}")
    print(f"- qtd: {resumo.get('qtd')}")
    if resumo.get("municipios_atualizados") is not None:
        print(f"- municipios_atualizados: {resumo.get('municipios_atualizados')}")

    meta = resumo.get("metadata", {})
    print(f"- metodo: {meta.get('metodo')}")
    print(f"- url_usada: {meta.get('url_usada')}")
    if resumo.get("status") != "OK":
        print(f"- observacao: {meta.get('observacao')}")
        print("\nSe continuar FALHA, rode com uma URL direta de download:")
        print('python scripts\\run_idh_automatico.py --url "URL_DO_ARQUIVO_CSV_XLSX_ZIP"')


if __name__ == "__main__":
    main()
