from pathlib import Path
import sys
import requests
import json
from pprint import pprint

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TERMOS_OBRIGATORIOS = [
    "rendimento",
]

TERMOS_DESEJADOS = [
    "classe",
    "domicílio",
    "domicilio",
    "responsável",
    "responsavel",
    "renda",
]

def contem(texto, termos):
    t = str(texto or "").lower()
    return all(x.lower() in t for x in termos)

def contem_algum(texto, termos):
    t = str(texto or "").lower()
    return any(x.lower() in t for x in termos)

def main():
    print("Buscando agregados IBGE relacionados a rendimento/classes...")

    urls = [
        "https://servicodados.ibge.gov.br/api/v3/agregados?busca=rendimento",
        "https://servicodados.ibge.gov.br/api/v3/agregados?busca=classe%20rendimento",
        "https://servicodados.ibge.gov.br/api/v3/agregados?busca=rendimento%20domiciliar",
        "https://servicodados.ibge.gov.br/api/v3/agregados?busca=responsavel%20domicilio%20rendimento",
    ]

    candidatos = {}

    for url in urls:
        try:
            resp = requests.get(url, timeout=60)
            print(f"HTTP {resp.status_code} | {url}")

            if resp.status_code != 200:
                print(resp.text[:500])
                continue

            data = resp.json()

            def andar(obj):
                if isinstance(obj, list):
                    for x in obj:
                        andar(x)

                elif isinstance(obj, dict):
                    agg_id = obj.get("id") or obj.get("agregado")
                    nome = obj.get("nome") or obj.get("descricao") or ""

                    if agg_id and contem_algum(nome, TERMOS_DESEJADOS):
                        candidatos[str(agg_id)] = nome

                    for v in obj.values():
                        andar(v)

            andar(data)

        except Exception as e:
            print(f"Falha na busca: {e}")

    print("\nCandidatos encontrados:")
    for agg_id, nome in sorted(candidatos.items()):
        print(f"{agg_id} | {nome}")

    print("\nAnalisando metadados dos candidatos...")

    bons = []

    for agg_id, nome in sorted(candidatos.items()):
        try:
            url = f"https://servicodados.ibge.gov.br/api/v3/agregados/{agg_id}/metadados"
            resp = requests.get(url, timeout=60)

            if resp.status_code != 200:
                continue

            meta = resp.json()
            meta_txt = json.dumps(meta, ensure_ascii=False).lower()

            score = 0
            for termo in ["classe", "rendimento", "domicílio", "domicilio", "responsável", "responsavel", "salário", "salario"]:
                if termo in meta_txt:
                    score += 1

            if score >= 3:
                bons.append((score, agg_id, nome, meta))

        except Exception as e:
            print(f"Falha metadados {agg_id}: {e}")

    print("\n==============================")
    print("MELHORES CANDIDATOS")
    print("==============================")

    for score, agg_id, nome, meta in sorted(bons, reverse=True):
        print(f"\nAGREGADO {agg_id} | score={score}")
        print(nome)

        variaveis = meta.get("variaveis") or []
        classificacoes = meta.get("classificacoes") or []

        print("Variáveis:")
        for v in variaveis[:20]:
            print(" -", v.get("id"), "|", v.get("nome"))

        print("Classificações:")
        for c in classificacoes[:20]:
            print(" -", c.get("id"), "|", c.get("nome"))

    if not bons:
        raise RuntimeError(
            "Nenhum agregado oficial com classe de rendimento foi identificado automaticamente. "
            "Precisamos escolher manualmente a tabela oficial do SIDRA/IBGE."
        )

    print("\n✅ Diagnóstico concluído.")
    print("Me mande o bloco MELHORES CANDIDATOS para eu fechar a carga automática correta.")

if __name__ == "__main__":
    main()
