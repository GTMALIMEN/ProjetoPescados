
from pathlib import Path
import csv


def main():
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "data" / "templates"
    out_dir.mkdir(parents=True, exist_ok=True)

    path = out_dir / "ceagesp_manual.csv"

    rows = [
        {
            "data_referencia": "10/06/2026",
            "produto": "Tilápia",
            "classificacao": "Inteira",
            "unidade": "kg",
            "preco_minimo": "12,00",
            "preco_comum": "14,50",
            "preco_maximo": "17,00",
            "fonte": "CEAGESP Manual",
            "url_fonte": "https://ceagesp.gov.br/cotacoes/",
            "observacao": "Exemplo; substituir pelos dados reais da cotação.",
        },
        {
            "data_referencia": "10/06/2026",
            "produto": "Salmão",
            "classificacao": "Filé",
            "unidade": "kg",
            "preco_minimo": "65,00",
            "preco_comum": "72,00",
            "preco_maximo": "80,00",
            "fonte": "CEAGESP Manual",
            "url_fonte": "https://ceagesp.gov.br/cotacoes/",
            "observacao": "Exemplo; substituir pelos dados reais da cotação.",
        },
    ]

    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    input_path = root / "data" / "input" / "ceagesp_manual.csv"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    if not input_path.exists():
        input_path.write_text(path.read_text(encoding="utf-8-sig"), encoding="utf-8-sig")

    print(f"✅ Template criado: {path}")
    print(f"✅ Cópia para preenchimento: {input_path}")
    print("\nEdite o arquivo em data/input/ceagesp_manual.csv e depois rode:")
    print(r'python scripts\load_ceagesp_manual_file.py --arquivo "data\input\ceagesp_manual.csv"')


if __name__ == "__main__":
    main()
