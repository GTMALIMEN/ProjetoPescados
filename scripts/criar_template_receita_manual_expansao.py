
from pathlib import Path
import csv


def main():
    root = Path(__file__).resolve().parents[1]
    tpl = root / "data" / "templates"
    inp = root / "data" / "input"
    tpl.mkdir(parents=True, exist_ok=True)
    inp.mkdir(parents=True, exist_ok=True)

    rows = [
        {
            "parceiro": "Cliente Exemplo 1",
            "cidade": "Belo Horizonte",
            "estado": "MG",
            "data_competencia": "01/06/2026",
            "grupo_produto": "Tilápia",
            "vlr_total_liquido": "1800,00",
            "Volume": "100",
            "Produto": "Tilápia",
            "TOP": "1100 - VENDA DE MERCADORIA",
        },
        {
            "parceiro": "Cliente Exemplo 2",
            "cidade": "Belo Horizonte",
            "estado": "MG",
            "data_competencia": "01/06/2026",
            "grupo_produto": "Salmão",
            "vlr_total_liquido": "4500,50",
            "Volume": "150",
            "Produto": "Salmão",
            "TOP": "1100 - VENDA DE MERCADORIA",
        },
    ]

    tpl_path = tpl / "receita_manual_expansao.csv"
    input_path = inp / "receita_manual_expansao.csv"

    for path in [tpl_path, input_path]:
        if path == input_path and path.exists():
            continue
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
            writer.writeheader()
            writer.writerows(rows)

    print(f"✅ Template criado: {tpl_path}")
    print(f"✅ Cópia para preenchimento: {input_path}")
    print("\nDepois de preencher, rode:")
    print(r'python scripts\load_receita_manual_expansao_file.py --arquivo "data\input\receita_manual_expansao.csv"')


if __name__ == "__main__":
    main()
