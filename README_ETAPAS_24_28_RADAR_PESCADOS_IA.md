# README — Roadmap Etapas 24 a 28  
## Radar Pescados IA — Expansão, Fontes, Compras e Previsão

Este documento registra a sequência planejada para completar os dados que ainda aparecem como `N/A` no app e preparar a base para a fase futura de Machine Learning.

---

## Status atual antes das próximas etapas

### Já concluído

```text
✅ Estrutura principal do Streamlit com 2 abas principais
✅ Análise de Expansão
✅ Análise Previsão de Mercado
✅ População Sudeste carregada
✅ PIB Sudeste carregado
✅ IDH/IDHM Sudeste 100% carregado
✅ Regiões comerciais MG
✅ Regiões econômicas iniciais para SP/RJ/ES via mesorregião IBGE
✅ CEAGESP definido como manual/controlado
✅ Documentação de fórmulas criada
✅ Diagnóstico V2 ativo
```

### Ainda pendente

```text
⏳ Perfil demográfico por sexo e faixa etária
⏳ Renda média
⏳ Classe de renda
⏳ PDV proxy: supermercados, restaurantes, peixarias e outros
⏳ Comex Stat refinado
⏳ Base de compra manual
⏳ Prévia vendedores
⏳ Modelos de Machine Learning
```

---

# Etapa 24 — Censo Demográfico 2022

## Objetivo

Carregar informações demográficas e de renda para preencher os campos atualmente exibidos como `N/A` na aba **Análise de Expansão**.

## Campos a preencher

```text
pct_masculina
pct_feminina
pct_0_14
pct_15_29
pct_30_44
pct_45_59
pct_60_plus
renda_media
renda_classe_a
renda_classe_b
renda_classe_c
renda_classe_d
fonte_demografia
fonte_renda
```

## Fonte sugerida

```text
IBGE SIDRA — Censo Demográfico 2022
```

## Dados esperados

### Sexo

```text
População masculina
População feminina
Percentual masculino
Percentual feminino
```

### Faixa etária

```text
0 a 14 anos
15 a 29 anos
30 a 44 anos
45 a 59 anos
60 anos ou mais
```

### Renda

```text
Renda média
Distribuição por classe de renda
```

## Aplicação no app

```text
Aba principal: 🌎 Análise de Expansão
Subaba: 🌎 Análise de Expansão
Bloco: Perfil demográfico
Bloco: Simulador IDC / What-if
```

## Resultado esperado

A tabela de perfil demográfico deixa de mostrar:

```text
N/A
Pendente: Censo por sexo/faixa
```

e passa a mostrar percentuais reais por microrregião, estado e região econômica.

---

# Etapa 25 — PDV Proxy

## Objetivo

Criar uma base aproximada de pontos de venda por município/região para melhorar o cálculo de potencial comercial.

## Campos a preencher

```text
supermercados
restaurantes
peixarias
outros_pdv
fonte_pdv
```

## Estratégia inicial

Como ainda não teremos uma base oficial completa por CNPJ/CNAE, a primeira versão pode ser **proxy estimado pela internet**.

## Fontes possíveis

```text
OpenStreetMap / Overpass
Google Places, se houver chave/API
Base pública de estabelecimentos, se disponível
CNPJ/CNAE Receita Federal em etapa posterior
```

## Classificação sugerida

### Supermercados

```text
supermarket
grocery
mercado
supermercado
hortifruti
```

### Restaurantes

```text
restaurant
fast_food
lanchonete
bar
food_court
```

### Peixarias

```text
seafood
fishmonger
peixaria
pescados
fish
```

### Outros PDV

```text
açougue
mercearia
loja alimentar
distribuidor local
```

## Regra importante

O app precisa deixar claro que esse dado é estimado:

```text
fonte_pdv = "Proxy internet / estimado"
```

Depois, quando entrar a base oficial por CNPJ/CNAE:

```text
fonte_pdv = "CNPJ/CNAE Receita Federal"
```

## Aplicação no app

```text
Aba principal: 🌎 Análise de Expansão
Subaba: 🌎 Análise de Expansão
Bloco: Regiões econômicas/comerciais
Bloco: Municípios da região selecionada
Bloco: IDC / Margin Pool
Bloco: Simulador IDC
```

## Resultado esperado

As colunas deixam de aparecer como:

```text
supermercados = N/A
restaurantes = N/A
peixarias = N/A
outros_pdv = N/A
```

e passam a ter uma estimativa por município/região.

---

# Etapa 26 — Comex Stat refinado

## Objetivo

Melhorar a carga do Comex Stat, reduzir erros de API e separar melhor carga com sucesso de erro antigo.

## Problemas atuais

```text
A base Comex possui registros carregados com sucesso.
A tela ainda mostra logs antigos com ERRO_API.
O erro 429 indica excesso de requisições.
O erro 400 indica payload ou parâmetro inválido.
```

## Melhorias planejadas

```text
retry/backoff para erro 429
quebra de consultas por ano
quebra de consultas por grupo de NCM
validação de payload antes do envio
não consultar meses futuros
separar Últimas cargas com sucesso de Últimos erros
não mostrar erro antigo como status atual
```

## Aplicação no app

```text
Aba principal: 📈 Análise Previsão de Mercado
Subaba: 🔌 Fontes Reais
Bloco: Comex Stat
```

## Resultado esperado

A tela de Fontes Reais passa a mostrar algo como:

```text
Comex Stat — última carga válida
Status: Sucesso
Registros: 261
Período: 2024-01 até 2026-05

Últimos erros:
Somente histórico técnico, não status atual
```

---

# Etapa 27 — Base de compra manual

## Objetivo

Criar uma base histórica de compras reais da empresa para alimentar análise de preço, margem e previsão futura.

## Campos sugeridos

```text
data_compra
produto
marca
fornecedor
categoria
unidade
quantidade
preco_unitario
valor_total
observacao
```

## Histórico esperado

```text
A partir de 2022/mês
```

## Aplicação no app

```text
Aba principal: 📈 Análise Previsão de Mercado
Subaba: 📈 Análise Previsão de Mercado
Bloco: Base de compra
Bloco: Preço real de compra
Bloco futuro: Previsão de preço
```

## Resultado esperado

O app passa a comparar:

```text
Preço CEAGESP manual
Preço real de compra
Preço Comex/externo
Preço CEPEA/CONAB quando aplicável
```

## Observação

Essa base será uma das mais importantes para Machine Learning, porque representa o preço real que a empresa pagou.

---

# Etapa 28 — Prévia vendedores

## Objetivo

Criar uma base manual para previsão comercial e acompanhamento de intenção de venda.

## Campos sugeridos

```text
data_previa
vendedor
cliente
produto
marca
preco_previsto
quantidade_prevista
receita_prevista
status
observacao
```

## Status sugeridos

```text
Aberto
Em negociação
Convertido
Perdido
Cancelado
```

## Aplicação no app

```text
Aba principal: 📈 Análise Previsão de Mercado
Subaba: 📈 Análise Previsão de Mercado
Bloco: Prévia vendedores
Bloco futuro: Previsão de demanda
```

## Resultado esperado

O app passa a mostrar:

```text
Vendedor
Produto
Preço
Quantidade
Receita total
Data prevista
Status da oportunidade
```

---

# Após as etapas 24 a 28 — Direção para Machine Learning

A fase de Machine Learning só deve começar depois que as bases estiverem mais completas.

## 1. Previsão de preço

### Modelos possíveis

```text
Prophet
SARIMA
XGBoost
LightGBM
Random Forest
```

### Variáveis possíveis

```text
Preço real de compra
Preço CEAGESP
Comex Stat
Dólar
CEPEA
CONAB
Produto
Mês
Sazonalidade
Fornecedor
Marca
```

### Resultado esperado

```text
Preço previsto
Intervalo de confiança
Erro do modelo
Comparação preço real x previsto
```

---

## 2. Previsão de demanda

### Modelos possíveis

```text
Prophet
LightGBM
XGBoost
Random Forest
```

### Variáveis possíveis

```text
Vendas históricas
Prévia vendedores
Preço de compra
Preço CEAGESP
Região
Cliente
Produto
Mês
Sazonalidade
```

### Resultado esperado

```text
Demanda prevista
Demanda real
Erro percentual
Curva de tendência
```

---

## 3. Score de oportunidade regional

### Modelos possíveis

```text
Random Forest
XGBoost
LightGBM
Regressão logística
```

### Variáveis possíveis

```text
População
PIB
IDH
Renda média
Faixa etária
Sexo
PDV proxy
Vendas históricas
Preço
Região econômica
```

### Resultado esperado

```text
Probabilidade de oportunidade
Ranking de regiões
Explicação por variável
```

---

## 4. Segmentação de regiões

### Modelos possíveis

```text
K-Means
HDBSCAN
Hierarchical Clustering
```

### Objetivo

Agrupar regiões parecidas para estratégia comercial.

### Exemplos de clusters

```text
Alta renda + alto PIB + baixa venda
Alta população + baixo PDV
Baixa renda + alta venda atual
Regiões maduras
Regiões de expansão
```

---

## 5. Detecção de anomalias

### Modelos possíveis

```text
Isolation Forest
Local Outlier Factor
Z-score robusto
```

### Uso

```text
Preço fora da curva
Queda brusca de venda
Compra fora do padrão
Erro de cadastro
Produto com comportamento incomum
```

---

# Ordem recomendada de execução

```text
Etapa 24 — Censo Demográfico 2022
Etapa 25 — PDV Proxy
Etapa 26 — Comex Stat refinado
Etapa 27 — Base de compra manual
Etapa 28 — Prévia vendedores
Depois — Machine Learning
```

---

# Critério para considerar a fase pronta

A fase 24 a 28 pode ser considerada pronta quando o diagnóstico mostrar:

```text
expansao_demografia_censo = OK
expansao_pdv = OK ou OK_PROXY
ceagesp_pescados_manual = OK
base_compra_manual = OK
previa_vendedores = OK
comex_stat = OK sem erro atual crítico
```

---

# Observação final

A prioridade agora é completar dados confiáveis antes de treinar modelos.

Machine Learning sem:

```text
demografia
renda
PDV
compra real
prévia comercial
histórico limpo
```

gera previsão fraca.

Por isso, o melhor caminho é primeiro fechar as bases, depois avançar para Prophet, LightGBM/XGBoost, segmentação e anomalias.
