# Hotfix definitivo — Mapas com Folium/Leaflet

Os mapas em Plotly foram trocados para Folium/Leaflet para evitar o erro do retângulo gigante.

## Rodar

```bat
pip install -r requirements.txt
scripts\limpar_cache_mapas_folium.bat
streamlit run app.py
```

## Diagnóstico esperado

Brasil:

```text
qtd_features: 27
```

MG:

```text
qtd_features: aproximadamente 853
```
