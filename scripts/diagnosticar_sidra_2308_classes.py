import requests
import json

AGREGADO = "2308"

url = f"https://servicodados.ibge.gov.br/api/v3/agregados/{AGREGADO}/metadados"

resp = requests.get(url, timeout=60)
print("HTTP:", resp.status_code)

meta = resp.json()
if isinstance(meta, list):
    meta = meta[0]

print("\nAGREGADO:", AGREGADO)
print("NOME:", meta.get("nome"))

print("\nVARIÁVEIS:")
for v in meta.get("variaveis", []):
    print(v.get("id"), "|", v.get("nome"))

print("\nCLASSIFICAÇÕES E CATEGORIAS:")
for c in meta.get("classificacoes", []):
    print("\nCLASSIFICAÇÃO:", c.get("id"), "|", c.get("nome"))
    for cat in c.get("categorias", []):
        print("  ", cat.get("id"), "|", cat.get("nome"))

print("\nNÍVEIS TERRITORIAIS:")
print(json.dumps(meta.get("nivelTerritorial", meta.get("niveisTerritoriais", {})), ensure_ascii=False, indent=2))

print("\nPERÍODOS:")
print(json.dumps(meta.get("periodicidade", meta.get("periodos", {})), ensure_ascii=False, indent=2))
