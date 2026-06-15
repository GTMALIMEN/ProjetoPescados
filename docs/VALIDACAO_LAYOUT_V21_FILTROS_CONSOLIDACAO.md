# Validação Layout V2.1 — Filtros, consolidação e dólar separado

## Solicitação atendida

Este pacote valida e ajusta o arquivo enviado para:

```text
1. Colocar filtro de data/período/seleção de tempo na Análise Previsão de Mercado
2. Separar a parte do dólar/câmbio
3. Juntar tabelas iguais em um só lugar
4. Consolidar Região Comercial MG dentro da Análise de Expansão
5. Manter mapa comercial/econômico simplificado dentro da Análise de Expansão
6. Manter lógica: seleciona MG mostra MG; seleciona SP mostra SP; RJ e ES idem
```

## Resultado validado no app.py

### Análise de Expansão

A antiga aba separada `🧭 Região Comercial MG` foi removida.

Agora fica tudo em:

```text
🌎 Análise de Expansão
```

Com:

```text
Estado base: MG, SP, RJ, ES
Região econômica/comercial
Mapa comercial/econômico simplificado
Resumo por estado
Regiões econômicas/comerciais
Municípios da região selecionada
Microrregião, demografia, receita e IDC
Exportação
```

Regra:

```text
MG:
    usa Região Comercial MG + mapa MG

SP/RJ/ES:
    usa mesorregião IBGE como região econômica inicial
    exibe mapa simplificado em treemap
```

### Análise Previsão de Mercado

A antiga aba separada `🥩 Proteínas e Grãos` foi removida.

Agora fica consolidado dentro de:

```text
📈 Análise Previsão de Mercado
```

Com:

```text
Filtro de período
Dólar / Câmbio
Radar econômico — demais indicadores
Proteínas e grãos consolidados
CEAGESP
Base de compra
Prévia vendedores
Índices
Exportação
```

## Filtros de tempo implementados

```text
Últimos 3 meses
Últimos 6 meses
Últimos 12 meses
Últimos 24 meses
Ano atual
Tudo
Personalizado
```

Aplicados visualmente em:

```text
Dólar/Câmbio
Radar econômico
Proteínas e grãos
CEAGESP
Base de compra
Prévia vendedores
```

## Limpeza de tabelas duplicadas

Foram adicionadas funções visuais:

```text
_date_range_from_period()
_filter_df_by_period()
_drop_duplicate_columns()
dataframe_periodo()
```

Essas funções filtram por período e removem colunas duplicadas geradas por merges visuais.

## Como rodar

```bat
cd /d "C:\Users\Marcos Aredes\OneDrive - BH Trade\Área de Trabalho\Pescados"

.\.venv\Scripts\activate.bat

.\.venv\Scripts\python.exe scripts\validar_layout_v21.py

.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Observação

Este ajuste é visual/organizacional. Não altera fórmulas do banco e não apaga dados.
