
from pathlib import Path
import sys
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path: sys.path.insert(0, str(ROOT_DIR))
from src.services.mapas_service import carregar_geojson_brasil_ufs, carregar_geojson_mg_municipios, diagnostico_geojson

def main():
    import argparse
    p=argparse.ArgumentParser(description='Baixar/cachear malhas GeoJSON para Folium')
    p.add_argument('--force', action='store_true')
    args=p.parse_args()
    print('Baixando Brasil por UF...')
    br=carregar_geojson_brasil_ufs(force=args.force); print(diagnostico_geojson(br))
    print('\nBaixando MG por município...')
    mg=carregar_geojson_mg_municipios(force=args.force); print(diagnostico_geojson(mg))
    if len(mg.get('features', [])) < 800:
        print('\nATENÇÃO: MG deveria ter perto de 853 municípios. Rode novamente se a internet/API falhar.')
if __name__ == '__main__': main()
