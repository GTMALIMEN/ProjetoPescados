# Arquitetura — Radar Pescados IA

## Visão Geral

O sistema segue uma arquitetura em camadas:

```text
Fonte de dados
    ↓
Raw
    ↓
Staging
    ↓
Data Warehouse
    ↓
Camada Analítica
    ↓
Aplicação Streamlit
```

## Camada de fontes

Fontes utilizadas:

- Banco Central
- IBGE
- Comex Stat
- CONAB
- CEPEA
- Arquivo interno de vendas

## Camada Raw

Armazena payloads ou registros brutos importantes para auditoria.

Exemplos:

- `raw.api_payload`
- `raw.comexstat_payload`

## Camada Staging

Recebe dados temporários ou normalizados antes de entrar no DW.

Exemplos:

- `staging.bcb_series`
- `staging.ibge_municipios`
- `staging.ibge_sidra_municipal`
- `staging.indicador_setorial`
- `staging.vendas_internas`

## Camada DW

Camada analítica principal.

Exemplos:

- `dw.fato_serie_historica`
- `dw.fato_indicador_municipal`
- `dw.fato_indicador_setorial`
- `dw.fato_vendas`
- `dw.dim_geografia`
- `dw.dim_cliente`
- `dw.dim_produto`
- `dw.dim_vendedor`
- `dw.dim_canal`

## Camada App

Camada de decisão, scores, alertas e relatórios.

Exemplos:

- `app.fato_potencial_regional`
- `app.fato_score_regional`
- `app.fato_recomendacao`
- `app.fato_alerta_ativo`
- `app.fato_relatorio_executivo`
- `app.pipeline_execucao`

## Fluxo de decisão

```text
Vendas + IBGE + BCB + Setorial
        ↓
Potencial regional
        ↓
Índices setoriais
        ↓
Score regional
        ↓
Recomendação
        ↓
Alerta ativo
        ↓
Relatório executivo
```

## Motor de decisão

O motor considera:

- oportunidade regional;
- risco regional;
- potencial populacional/comercial;
- competitividade do pescado;
- pressão de custo;
- risco de substituição;
- confiança dos dados.

## Escala de cenário

O score final é convertido para uma escala de 1 a 10.

```text
1 = cenário muito ruim
10 = cenário muito favorável
```

## Observabilidade

A observabilidade é feita por:

- `app.etl_run`
- `app.etl_controle_carga`
- `app.pipeline_execucao`
- `app.pipeline_etapa_execucao`
- `app.vw_saude_sistema`
- `app.vw_pipeline_saude`
