
# Ajuste V2 — Aderência ao plano e dados públicos

## Problemas identificados

A tela mostrava campos como PIB, IDH, renda média, supermercados, restaurantes e peixarias com valor `0`.

Isso estava incorreto porque:

- `0` parece dado real;
- alguns campos ainda não tinham fonte carregada;
- PIB e população deveriam vir de IBGE/SIDRA;
- IDH, renda por classe e PDV precisam de fonte específica ou carga manual.

## Correção aplicada

### 1. Abas alinhadas ao plano

A interface foi reduzida para as abas do planejamento V2:

```text
📈 Radar Econômico
🗺️ Geografia IBGE
🧭 Região Comercial MG
🌎 Análise de Expansão
🥩 Proteínas e Grãos
🔌 Fontes Reais
📈 Análise Previsão de Mercado
🧪 What-if
🚨 Alertas Ativos
📄 Relatório Executivo
🩺 Saúde do Sistema
```

### 2. Campos sem fonte não aparecem como zero falso

Agora:

- população vem do IBGE/SIDRA quando carregada;
- PIB tenta vir do IBGE/SIDRA tabela 5938;
- IDH fica como pendente até fonte externa confiável;
- renda/classe econômica fica como pendente até Censo/POF;
- supermercados/restaurantes/peixarias ficam pendentes até base CNPJ, OSM, Google Places ou cadastro interno.

### 3. Novas estruturas no banco

Foi criado:

```text
app.fato_expansao_municipio
app.fato_ceagesp_pescados
app.fato_compra_manual
app.fato_previa_vendedores
app.vw_diagnostico_v2_plano
```

### 4. Novos scripts

```bat
python scripts/apply_expansao_v2_publica.py
python scripts/run_expansao_publica.py --estados MG,SP,RJ,ES
python scripts/run_ceagesp_pescados.py
python scripts/diagnosticar_v2_plano.py
```

## Ordem para aplicar

```bat
python scripts/init_db.py
python scripts/run_ibge_localidades.py
python scripts/run_ibge_populacao.py
python scripts/apply_expansao_v2_publica.py
python scripts/run_expansao_publica.py --estados MG,SP,RJ,ES
python scripts/run_ceagesp_pescados.py
python scripts/diagnosticar_v2_plano.py
streamlit run app.py
```

## Observação sobre IDH e PDV

O app não inventa IDH nem quantidade de PDV.

Essas colunas ficam como `N/A`/pendente até receber fonte confiável.
