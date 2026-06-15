
# Etapa 21 — Mapas Geográficos Reais

Esta etapa substitui os mapas simplificados por mapas geográficos reais usando malhas oficiais do IBGE.

## O que entrou

- Mapa do Brasil por UF.
- Mapa real de Minas Gerais por município.
- Cores por região comercial.
- Mapa de potencial regional em MG.
- Clique no mapa de MG para selecionar região comercial.
- Cache local dos GeoJSONs em `data/geojson/`.

## Fonte das malhas

As malhas são baixadas da API oficial de malhas do IBGE:

- Brasil por UF;
- Minas Gerais por município.

## Arquivos criados

```text
src/services/mapas_service.py
scripts/baixar_malhas_ibge.py
scripts/atualizar_mapas_ibge.bat
docs/ETAPA21_MAPAS_GEOGRAFICOS.md
```

## Rodar

```bat
cd /d "C:\Users\ducar\OneDrive\Área de Trabalho\Nova pasta"
.venv\Scripts\activate

python scripts\baixar_malhas_ibge.py
python scripts\apply_regioes_mg.py
streamlit run app.py
```

Ou:

```bat
scripts\atualizar_mapas_ibge.bat
```

## Abas alteradas

### Geografia IBGE

Agora mostra um mapa real do Brasil por UF.

Métricas disponíveis:

- municípios;
- faturamento;
- volume KG;
- clientes;
- faturamento por município.

### Região Comercial MG

Agora mostra um mapa real de Minas Gerais por município, colorido por região comercial.

Ao clicar no mapa, a região comercial é selecionada automaticamente.

### Potencial Regional

Agora mostra um mapa real de MG com:

- score de potencial;
- população regional;
- faturamento regional;
- volume regional;
- clientes;
- cenário;
- confiança.

## Observações

Na primeira execução, o app precisa de internet para baixar as malhas do IBGE. Depois disso, usa o cache local.
