
# Hotfix — Mapas reais aparecendo como retângulo

## Problema

Os mapas reais estavam aparecendo como:

- retângulo grande colorido;
- MG minúsculo ou deslocado;
- mapa de potencial preenchendo toda a área.

## Causas prováveis

1. Cache antigo de GeoJSON baixado com formato/zoom ruim.
2. Malha retornando feature extra, como o polígono do estado inteiro.
3. Plotly usando `fitbounds` de forma inadequada no tema escuro.
4. Falta de filtro dos polígonos pelos códigos IBGE do banco.
5. Possível inversão de coordenadas em alguma resposta/cache.

## Correções

- URLs revisadas para malha IBGE.
- MG usa código `31` em vez de sigla.
- Qualidade alterada para `intermediaria`.
- GeoJSON agora é normalizado.
- Features são filtradas por `codarea`.
- MG aceita apenas municípios com código IBGE de 7 dígitos iniciando em `31`.
- Brasil aceita apenas UFs com código de 2 dígitos.
- Zoom geográfico foi travado:
  - Brasil: longitude/latitude do Brasil.
  - MG: longitude/latitude de Minas Gerais.
- Adicionado diagnóstico de mapas.

## Rodar

```bat
scripts\limpar_cache_mapas.bat
```

ou:

```bat
python scripts\baixar_malhas_ibge.py --force
python scripts\diagnosticar_mapas.py
streamlit run app.py
```

## Diagnóstico esperado

Para MG, o diagnóstico deve mostrar algo próximo de:

```text
qtd_features: 853
bounds: longitude entre -52 e -39, latitude entre -23 e -13
```

Se `qtd_features` vier muito menor que 853, o arquivo GeoJSON baixado não é a malha municipal correta.
