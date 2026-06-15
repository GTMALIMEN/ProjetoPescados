# Hotfix — Voltar para mapas simples em blocos

## Decisão

A tentativa de usar mapa geográfico real com Plotly/Folium gerou instabilidade visual e erros de renderização.

Foi decidido voltar para uma visualização simples, estável e bem feita em blocos/treemap.

## O que foi alterado

- Mapa real do Brasil removido da interface.
- Mapa real de MG removido da interface.
- Mapa real de potencial removido da interface.
- Visualizações substituídas por treemaps do Plotly.
- Não depende de GeoJSON.
- Não depende de internet.
- Não precisa baixar malha do IBGE.

## Telas afetadas

### Geografia IBGE

Agora mostra:

- mapa simplificado do Brasil por UF;
- métrica selecionável;
- resumo por UF;
- tabela de municípios.

### Região Comercial MG

Agora mostra:

- barras de municípios por região;
- mapa comercial simplificado em blocos;
- seletor manual de região;
- tabela de municípios da região.

### Potencial Regional

Agora mostra:

- mapa simplificado por região;
- gráficos de potencial;
- tabela analítica.

## Como rodar

```bat
streamlit run app.py
```

Não é necessário rodar:

```bat
python scripts/baixar_malhas_ibge.py
```

## Motivo

A visualização simples é melhor para este MVP:

- mais estável;
- mais rápida;
- menos dependências;
- mais fácil de apresentar;
- evita bugs visuais.
