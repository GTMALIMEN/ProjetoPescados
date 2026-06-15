# Hotfix — Análise Expansão + Receita Manual + IDC + CEPEA

## Ajustes na Análise de Expansão

### 1. IDC em gráficos

Os gráficos de expansão passam a incluir IDC em texto/tooltip quando a coluna existir:

```text
Mapa comercial/econômico simplificado
Score por estado
Score por região econômica/comercial
Top 20 microrregiões
IDC / Margin Pool
```

### 2. 4 casas decimais

As tabelas exibidas no app passam a arredondar números para 4 casas decimais.

### 3. Score por região

A classificação segue o mesmo padrão do Top 20 de microrregiões:

```text
Alta prioridade
Média prioridade
Baixa prioridade
Monitorar
```

### 4. IDC estratégico

O campo principal `idc_base` passa a ser o IDC estratégico com todos os fatores:

```text
30% População
25% PIB
15% Renda / POF
15% PIB per capita
5% Gênero masculino
5% Gênero feminino
5% Pontos de venda
```

A fórmula antiga fica preservada como:

```text
idc_macro = (Participação População % + Participação PIB %) / 2
```

### 5. Receita por categoria

A base manual da Análise de Expansão deve ter:

```text
parceiro
cidade
estado
data_competencia
grupo_produto
vlr_total_liquido
```

O app calcula:

```text
receita por categoria
receita total dos últimos 12 meses
receita média 12m
última venda por região
status_receita
```

Status:

```text
Última venda: dd/mm/aaaa
Sem venda nos últimos 12 meses
```

## Melhorias na Análise Previsão de Mercado

### CEPEA

Foi adicionada leitura de CEPEA a partir de:

```text
dw.fato_indicador_setorial
```

### Comparação CEPEA x CEAGESP

Foi adicionada uma aba de comparação:

```text
Comparação CEPEA x CEAGESP
```

Com seleção de fontes:

```text
CEPEA
CEAGESP
```

## Como rodar

```bat
scripts\rodar_hotfix_expansao_receita_cepea.bat
```

Ou manualmente:

```bat
.\.venv\Scripts\python.exe scripts\apply_hotfix_expansao_receita_cepea.py
.\.venv\Scripts\python.exe scripts\criar_template_receita_manual_expansao.py
.\.venv\Scripts\python.exe scripts\load_receita_manual_expansao_file.py --arquivo "data\input\receita_manual_expansao.csv"
.\.venv\Scripts\python.exe -m streamlit run app.py
```
