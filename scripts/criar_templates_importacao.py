from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
OUT = ROOT_DIR / 'data' / 'templates'
OUT.mkdir(parents=True, exist_ok=True)

TEMPLATES = {
    'ceagesp_manual.csv': pd.DataFrame([{
        'data_referencia': '2026-06-08', 'produto': 'Tilápia', 'classificacao': 'Inteira',
        'unidade': 'kg', 'preco_minimo': 12.50, 'preco_comum': 14.00, 'preco_maximo': 16.00,
        'fonte': 'CEAGESP manual', 'url_fonte': 'https://ceagesp.gov.br/cotacoes/'
    }]),
    'base_compra_manual.csv': pd.DataFrame([{
        'data': '2026-06-01', 'fornecedor': 'Fornecedor Exemplo', 'marca': 'Marca Exemplo',
        'produto': 'Tilápia', 'categoria': 'Pescado', 'preco_compra': 13.75,
        'quantidade_comprada': 500, 'unidade': 'kg', 'observacao': 'Linha de exemplo'
    }]),
    'previa_vendedores.csv': pd.DataFrame([{
        'vendedor': 'Vendedor Exemplo', 'produto': 'Tilápia', 'preco': 18.90,
        'data_venda': '2026-06-10', 'quantidade_vendida': 120, 'receita_total': 2268,
        'cliente': 'Cliente Exemplo', 'regiao': 'Grande BH / Central', 'observacao': 'Linha de exemplo'
    }]),
    'idh_municipal.csv': pd.DataFrame([{
        'codigo_ibge': '3106200', 'uf': 'MG', 'municipio': 'Belo Horizonte',
        'idhm': 0.810, 'ano': 2010, 'fonte': 'Atlas Brasil/IPEA/PNUD/FJP'
    }]),
}

for filename, df in TEMPLATES.items():
    path = OUT / filename
    df.to_csv(path, index=False, encoding='utf-8-sig', sep=';')
    print(f'OK: {path}')
print('\nTemplates criados em data/templates.')
