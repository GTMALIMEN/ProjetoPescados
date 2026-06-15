# Hotfix — Métricas dos mapas simples

## Problema

Ao trocar a métrica do mapa simplificado do Brasil para:

- Faturamento
- Volume KG
- Clientes
- Faturamento por município

o app podia mostrar erro.

## Causa

O `treemap` do Plotly usa a coluna `values` para definir o tamanho dos blocos.  
Quando a métrica escolhida estava toda zerada, por exemplo faturamento sem vendas reais, o gráfico podia quebrar.

## Correção

A área dos blocos agora usa uma base estável:

```text
qtd_municipios
```

A métrica selecionada entra como cor/indicador.

Assim, mesmo se faturamento, volume ou clientes estiverem zerados, o gráfico continua carregando.

## Telas corrigidas

- Geografia IBGE
- Região Comercial MG
- Potencial Regional

## Como rodar

```bat
streamlit run app.py
```
