from pathlib import Path
import csv


COLUNAS = [
    "data_inicio_periodo",
    "data_fim_periodo",
    "periodo_original",
    "produto",
    "regiao_cepea",
    "uf",
    "preco_ajustado",
    "preco_rs_kg",
    "variacao_semana_pct",
    "unidade",
    "url_fonte",
    "observacao",
]


def main():
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "data" / "templates"
    out_dir.mkdir(parents=True, exist_ok=True)

    path = out_dir / "cepea_manual.csv"

    rows = [
        {
            "data_inicio_periodo": "15/06/2026",
            "data_fim_periodo": "19/06/2026",
            "periodo_original": "15 - 19/06/2026",
            "produto": "Tilápia",
            "regiao_cepea": "Triângulo Mineiro/Alto Paranaíba",
            "uf": "MG",
            "preco_ajustado": "10,00",
            "preco_rs_kg": "10,00",
            "variacao_semana_pct": "0,00",
            "unidade": "R$/kg",
            "url_fonte": "https://www.cepea.org.br/br/indicador/tilapia.aspx",
            "observacao": "Exemplo; substituir pelos dados reais copiados do CEPEA.",
        },
        {
            "data_inicio_periodo": "15/06/2026",
            "data_fim_periodo": "19/06/2026",
            "periodo_original": "15 - 19/06/2026",
            "produto": "Tilápia",
            "regiao_cepea": "Morada Nova de Minas",
            "uf": "MG",
            "preco_ajustado": "9,50",
            "preco_rs_kg": "9,50",
            "variacao_semana_pct": "0,00",
            "unidade": "R$/kg",
            "url_fonte": "https://www.cepea.org.br/br/indicador/tilapia.aspx",
            "observacao": "Exemplo; substituir pelos dados reais copiados do CEPEA.",
        },
    ]

    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    input_path = root / "data" / "input" / "cepea_manual.csv"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    if not input_path.exists():
        input_path.write_text(path.read_text(encoding="utf-8-sig"), encoding="utf-8-sig")

    print(f"✅ Template criado: {path}")
    print(f"✅ Cópia para preenchimento: {input_path}")
    print("\nEdite o arquivo em data/input/cepea_manual.csv e depois rode:")
    print(r'python scripts\load_cepea_manual_file.py --arquivo "data\input\cepea_manual.csv"')


if __name__ == "__main__":
    main()
