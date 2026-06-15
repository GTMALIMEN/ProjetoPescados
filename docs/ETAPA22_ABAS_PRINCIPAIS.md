
# Etapa 22 — Abas principais do Radar Pescados IA

## Decisão

O app passa a ter **2 abas principais**, conforme a Versão 2.0 do plano:

```text
🐟 Radar Pescados IA
├── 🌎 Análise de Expansão
└── 📈 Análise Previsão de Mercado
```

## Objetivo

Separar visualmente as duas frentes estratégicas sem perder o que já foi construído.

## Estrutura implementada

### 1. 🌎 Análise de Expansão

Ordem interna:

```text
📈 Radar Econômico
🗺️ Geografia IBGE
🧭 Região Comercial MG
🌎 Análise de Expansão
🧪 What-if
```

Essa frente concentra:

```text
População
PIB
IDH/IDHM
Microrregião
Região comercial
IDC
Margin Pool
Simulador de critérios
Exportação das bases de expansão
```

### 2. 📈 Análise Previsão de Mercado

Ordem interna:

```text
🥩 Proteínas e Grãos
🔌 Fontes Reais
📈 Análise Previsão de Mercado
🚨 Alertas Ativos
📄 Relatório Executivo
🩺 Saúde do Sistema
```

Essa frente concentra:

```text
Radar econômico último ano dentro da página de previsão
Proteínas e grãos unificados
CEAGESP manual/controlado
Base de compra manual
Prévia vendedores
Índices no final da página
Exportação das bases de previsão
```

## Mantido do projeto atual

```text
✅ População Sudeste
✅ PIB Sudeste
✅ IDH/IDHM 100%
✅ CEAGESP manual/controlado
✅ Diagnóstico V2
✅ Exportações
✅ Saúde do sistema
```

## Como rodar

```bat
.\.venv\Scripts\python.exe scripts\diagnosticar_v2_plano.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Próxima etapa

Depois da Etapa 22, seguir a ordem:

```text
Etapa 23 — Análise de Expansão Completa
Etapa 24 — Simulador IDC
Etapa 25 — Previsão de Mercado Base
Etapa 26 — Prophet Preço
Etapa 27 — Prophet Demanda
Etapa 28 — Cenários Finais
```
