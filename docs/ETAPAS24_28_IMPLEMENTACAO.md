
# Etapas 24 a 28 — Implementação

## Objetivo

Completar os dados que ainda aparecem como `N/A` e preparar a base para a futura fase de Machine Learning.

---

## Etapa 24 — Censo Demográfico 2022

### Implementado

```text
scripts/run_censo_demografico_2022.py
app.fato_demografia_renda_municipio
```

### Campos preenchidos

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
renda_classe_de
fonte_demografia
fonte_renda
```

### Observação importante

A versão atual usa **proxy controlado por UF** para preencher a estrutura e tirar os `N/A`.
A fonte fica clara no banco:

```text
fonte_demografia = Proxy controlado baseado em Censo 2022 por UF; substituir por SIDRA municipal fino
fonte_renda = Proxy operacional por PIB per capita; substituir por Censo/SIDRA/POF
```

Isso evita zero falso e deixa claro que é uma estimativa inicial.

---

## Etapa 25 — PDV Proxy

### Implementado

```text
scripts/run_pdv_proxy.py
app.fato_pdv_proxy_municipio
```

### Campos preenchidos

```text
supermercados
restaurantes
peixarias
outros_pdv
fonte_pdv
```

### Fonte

```text
Proxy estimado por população/renda — não oficial
```

### Observação

A próxima evolução pode trocar esse proxy por CNPJ/CNAE Receita Federal ou OSM/Overpass.

---

## Etapa 26 — Comex Stat refinado

### Implementado

```text
scripts/run_comex_refinado.py
app.vw_comex_stat_status_atual
app.vw_fontes_reais_cargas_sucesso
app.vw_fontes_reais_cargas_erro
```

### Melhorias

```text
retry/backoff
split por ano/grupo
não consulta mês futuro no ano corrente
logs de sucesso separados dos erros
erro antigo não aparece como status atual
```

---

## Etapa 27 — Base de compra manual

### Já existia

```text
scripts/load_compra_manual_file.py
app.fato_compra_manual
```

### Novo

```text
scripts/criar_templates_etapas27_28.py
data/templates/base_compra_manual.csv
data/input/base_compra_manual.csv
app.vw_compra_manual_resumo
```

### Campos

```text
data
fornecedor
marca
produto
categoria
preco_compra
quantidade_comprada
unidade
observacao
```

---

## Etapa 28 — Prévia vendedores

### Já existia

```text
scripts/load_previa_vendedores_file.py
app.fato_previa_vendedores
```

### Novo

```text
data/templates/previa_vendedores.csv
data/input/previa_vendedores.csv
app.vw_previa_vendedores_resumo
```

### Campos

```text
data_venda
vendedor
cliente
regiao
produto
preco
quantidade_vendida
receita_total
observacao
```

---

## Como rodar tudo

```bat
scripts\rodar_etapas24_28.bat
```

## Rodar etapa por etapa

```bat
.\.venv\Scripts\python.exe scripts\apply_etapas24_28.py

.\.venv\Scripts\python.exe scripts\run_censo_demografico_2022.py --estados MG,SP,RJ,ES

.\.venv\Scripts\python.exe scripts\run_pdv_proxy.py --estados MG,SP,RJ,ES

.\.venv\Scripts\python.exe scripts\criar_templates_etapas27_28.py

.\.venv\Scripts\python.exe scripts\load_compra_manual_file.py --arquivo "data\input\base_compra_manual.csv"

.\.venv\Scripts\python.exe scripts\load_previa_vendedores_file.py --arquivo "data\input\previa_vendedores.csv"

.\.venv\Scripts\python.exe scripts\run_comex_refinado.py --ano-inicio 2020 --ano-fim 2026 --delay 12 --max-tentativas 2

.\.venv\Scripts\python.exe scripts\diagnosticar_v2_plano.py
```

---

## Critério de pronto

```text
expansao_demografia_censo = OK
expansao_renda_censo = OK
expansao_pdv = OK_PROXY_ESTIMADO
comex_stat_refinado = OK_COM_DADOS ou OK_SEM_DADOS
base_compra_manual = OK
previa_vendedores = OK
```

---

## Próximo passo depois disso

Somente depois dessas bases estarem completas, avançar para Machine Learning:

```text
Previsão de preço
Previsão de demanda
Score de oportunidade regional
Segmentação de regiões
Detecção de anomalias
```
