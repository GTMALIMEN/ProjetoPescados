from pathlib import Path
import sys
import requests
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CODIGO_TESTE = "3106200"  # Belo Horizonte
BASE_URL = "https://apisidra.ibge.gov.br/values/t/10295"

urls = [
    (
        "10295_basico",
        f"{BASE_URL}/n6/{CODIGO_TESTE}/v/all/p/2022?formato=json"
    ),
    (
        "10295_sexo_all",
        f"{BASE_URL}/n6/{CODIGO_TESTE}/v/all/p/2022/c2/all?formato=json"
    ),
    (
        "10295_sexo_raca_idade_all",
        f"{BASE_URL}/n6/{CODIGO_TESTE}/v/all/p/2022/c2/all/c86/all/c287/all?formato=json"
    ),
    (
        "10295_sexo_raca_idade_allxt",
        f"{BASE_URL}/n6/{CODIGO_TESTE}/v/all/p/2022/c2/all/c86/allxt/c287/allxt?formato=json"
    ),
]

for nome, url in urls:
    print("\n" + "=" * 80)
    print(f"Testando: {nome}")
    print(url)

    try:
        resp = requests.get(url, timeout=90)
        print("HTTP:", resp.status_code)

        if resp.status_code != 200:
            print(resp.text[:800])
            continue

        data = resp.json()

        if not data or len(data) < 2:
            print("Retorno vazio.")
            print(str(data)[:800])
            continue

        print("✅ Retornou dados")
        print("\nHEADER:")
        print(data[0])

        df = pd.DataFrame(data[1:])
        print("\nAmostra:")
        print(df.head(20).to_string(index=False))

        print("\nColunas:")
        for col in df.columns:
            print(col, "=>", data[0].get(col))

        # Mostra variáveis disponíveis
        for c in df.columns:
            nome_col = str(data[0].get(c, "")).lower()
            if "variável" in nome_col or "variavel" in nome_col:
                print("\nValores de variável encontrados:")
                print(df[c].drop_duplicates().head(50).to_string(index=False))

        break

    except Exception as e:
        print("Erro:", e)
