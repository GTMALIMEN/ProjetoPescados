# Hotfix Layout V2.1 — Filtros, consolidação de abas e dólar separado

## Objetivo

Ajustar o app para reduzir duplicidade visual e deixar a navegação mais parecida com o plano operacional.

## Alterações

### 1. Filtro de período na Análise Previsão de Mercado

Foi adicionado filtro visual:

```text
Últimos 3 meses
Últimos 6 meses
Últimos 12 meses
Últimos 24 meses
Ano atual
Tudo
Personalizado
```

Aplicado em:

```text
Radar econômico
Dólar / Câmbio
Proteínas e grãos
CEAGESP
Base de compra
Prévia vendedores
```

### 2. Dólar separado

A Análise Previsão de Mercado agora possui bloco próprio:

```text
Dólar / Câmbio
```

O app procura automaticamente indicadores com nomes contendo:

```text
dólar
dolar
usd
cambio
câmbio
ptax
```

### 3. Região Comercial MG consolidada na Análise de Expansão

A antiga subaba:

```text
🧭 Região Comercial MG
```

foi removida como aba separada.

A lógica agora fica dentro de:

```text
🌎 Análise de Expansão
```

Regra:

```text
MG: Região Comercial MG + mapa MG
SP/RJ/ES: mesorregião IBGE como região econômica inicial
```

### 4. Mapa comercial/econômico simplificado

Dentro da Análise de Expansão existe o bloco:

```text
Mapa comercial/econômico simplificado
```

Para MG:

```text
usa mapa de regiões comerciais MG
```

Para SP/RJ/ES:

```text
usa treemap por região econômica/mesorregião
```

### 5. Proteínas e Grãos consolidado

A antiga subaba separada:

```text
🥩 Proteínas e Grãos
```

foi consolidada dentro da própria:

```text
📈 Análise Previsão de Mercado
```

Isso evita tabela duplicada.

### 6. Tabelas duplicadas

Foram adicionados helpers visuais para:

```text
filtrar por período
remover colunas duplicadas de merges visuais
exibir tabelas já limpas
```

Funções adicionadas ao app:

```text
_date_range_from_period()
_filter_df_by_period()
_drop_duplicate_columns()
dataframe_periodo()
```

## Como rodar

```bat
cd /d "C:\Users\Marcos Aredes\OneDrive - BH Trade\Área de Trabalho\Pescados"

.\.venv\Scripts\activate.bat

.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Observação

Esse hotfix é visual/organizacional. Ele não altera as fórmulas do banco nem os dados carregados.
