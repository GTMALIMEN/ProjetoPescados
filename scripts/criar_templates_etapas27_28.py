
from pathlib import Path
import csv


def _write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def main():
    root = Path(__file__).resolve().parents[1]
    tpl = root / "data" / "templates"
    inp = root / "data" / "input"
    tpl.mkdir(parents=True, exist_ok=True)
    inp.mkdir(parents=True, exist_ok=True)

    compra_rows = [
        {
            "data": "10/01/2022",
            "fornecedor": "Fornecedor Exemplo",
            "marca": "Marca Exemplo",
            "produto": "Tilápia",
            "categoria": "Pescado",
            "preco_compra": "14,50",
            "quantidade_comprada": "100",
            "unidade": "kg",
            "observacao": "Exemplo; substituir por compras reais."
        },
        {
            "data": "10/02/2022",
            "fornecedor": "Fornecedor Exemplo",
            "marca": "Marca Exemplo",
            "produto": "Salmão",
            "categoria": "Pescado",
            "preco_compra": "72,00",
            "quantidade_comprada": "80",
            "unidade": "kg",
            "observacao": "Exemplo; substituir por compras reais."
        },
    ]

    previa_rows = [
        {
            "data_venda": "10/06/2026",
            "vendedor": "Vendedor Exemplo",
            "cliente": "Cliente Exemplo",
            "regiao": "Grande BH / Central",
            "produto": "Tilápia",
            "preco": "18,90",
            "quantidade_vendida": "50",
            "receita_total": "945,00",
            "observacao": "Exemplo de prévia."
        },
        {
            "data_venda": "11/06/2026",
            "vendedor": "Vendedor Exemplo",
            "cliente": "Cliente Exemplo",
            "regiao": "Sul de MG",
            "produto": "Salmão",
            "preco": "89,90",
            "quantidade_vendida": "20",
            "receita_total": "1798,00",
            "observacao": "Exemplo de prévia."
        },
    ]

    compra_tpl = tpl / "base_compra_manual.csv"
    previa_tpl = tpl / "previa_vendedores.csv"
    _write_csv(compra_tpl, compra_rows)
    _write_csv(previa_tpl, previa_rows)

    compra_in = inp / "base_compra_manual.csv"
    previa_in = inp / "previa_vendedores.csv"

    if not compra_in.exists():
        _write_csv(compra_in, compra_rows)
    if not previa_in.exists():
        _write_csv(previa_in, previa_rows)

    print("✅ Templates criados:")
    print(f"- {compra_tpl}")
    print(f"- {previa_tpl}")
    print("\n✅ Cópias para preenchimento:")
    print(f"- {compra_in}")
    print(f"- {previa_in}")
    print("\nDepois de editar, carregue com:")
    print(r'python scripts\load_compra_manual_file.py --arquivo "data\input\base_compra_manual.csv"')
    print(r'python scripts\load_previa_vendedores_file.py --arquivo "data\input\previa_vendedores.csv"')


if __name__ == "__main__":
    main()
