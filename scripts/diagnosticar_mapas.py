
from pathlib import Path
import sys
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path: sys.path.insert(0, str(ROOT_DIR))
from src.services.mapas_service import carregar_geojson_brasil_ufs, carregar_geojson_mg_municipios, dados_mapa_brasil_ufs, dados_mapa_mg_regioes, diagnostico_geojson

def main():
    print('Diagnóstico Folium/Leaflet dos mapas\n')
    br=carregar_geojson_brasil_ufs(force=False); mg=carregar_geojson_mg_municipios(force=False)
    print('GeoJSON Brasil UF:'); print(diagnostico_geojson(br))
    print('\nGeoJSON MG municípios:'); print(diagnostico_geojson(mg))
    df_br=dados_mapa_brasil_ufs(); df_mg=dados_mapa_mg_regioes()
    print('\nDados Brasil por UF:'); print(f'Linhas: {len(df_br)}')
    if not df_br.empty: print(df_br[['uf','codigo_uf','qtd_municipios']].to_string(index=False))
    print('\nDados MG municípios:'); print(f'Linhas: {len(df_mg)}')
    if not df_mg.empty:
        print(df_mg[['codigo_ibge','municipio','regiao_comercial']].head(30).to_string(index=False))
        print('\nRegiões:'); print(df_mg['regiao_comercial'].value_counts().to_string())
if __name__ == '__main__': main()
