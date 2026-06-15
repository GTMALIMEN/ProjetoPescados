# Documentação — Como funciona o APP Radar Pescados IA

## 1. Objetivo do APP

O **Radar Pescados IA** é um aplicativo em Streamlit para apoiar decisões comerciais, expansão regional e previsão de mercado no setor de pescados.

Ele une dados públicos, dados internos e bases manuais para responder perguntas como:

```text
Onde existe maior oportunidade comercial?
Quais regiões têm maior potencial de expansão?
Como está a competitividade dos pescados frente a outras proteínas?
Quais fontes externas estão carregadas?
Quais preços reais de compra e preços de mercado estão disponíveis?
Quais vendedores/produtos têm previsão de venda?
Quais dados ainda estão pendentes?
```

---

## 2. Estrutura visual principal

O app foi organizado em **duas abas principais**.

```text
🐟 Radar Pescados IA
├── 🌎 Análise de Expansão
└── 📈 Análise Previsão de Mercado
```

Essa separação evita misturar análise geográfica/comercial com análise de mercado/preço/previsão.

---

# 3. Aba principal — 🌎 Análise de Expansão

## 3.1 Objetivo

A aba **Análise de Expansão** concentra a visão regional, geográfica e comercial.

Ela responde:

```text
Quais estados/regiões têm maior potencial?
Quais microrregiões concentram população, PIB e IDH?
Onde a empresa vende menos do que deveria pelo potencial?
Onde existe oportunidade de expansão?
Como a região muda quando altero os critérios do IDC?
```

## 3.2 Subabas internas

```text
📈 Radar Econômico
🗺️ Geografia IBGE
🧭 Região Comercial MG
🌎 Análise de Expansão
🧪 What-if / Simulador IDC
```

---

## 3.3 📈 Radar Econômico

### Função

Exibe indicadores econômicos gerais usados como contexto de mercado.

### Dados usados

```text
Banco Central
Indicadores macroeconômicos
Séries temporais carregadas no banco
```

### Uso

Serve para contextualizar a expansão e o cenário econômico.

---

## 3.4 🗺️ Geografia IBGE

### Função

Mostra a estrutura geográfica carregada:

```text
UFs
municípios
microrregiões
mesorregiões
mapas simplificados
```

### Dados usados

```text
IBGE Localidades
Malhas simplificadas quando disponíveis
```

### Uso

Serve como base territorial para cruzar população, PIB, IDH, vendas e regiões econômicas.

---

## 3.5 🧭 Região Comercial MG

### Função

Classifica municípios de Minas Gerais em regiões comerciais.

### Regra atual

MG possui regra comercial própria.

Exemplos:

```text
Grande BH / Central
Sul de MG
Zona da Mata
Triângulo / Alto Paranaíba
Vale do Aço / Rio Doce
Norte de MG
Jequitinhonha / Mucuri
```

### Uso

Essa classificação é usada diretamente na Análise de Expansão para MG.

---

## 3.6 🌎 Análise de Expansão

### Função

É a principal tela de expansão.

O usuário seleciona:

```text
Estado base: MG, SP, RJ ou ES
Região econômica/comercial
```

Depois o app mostra:

```text
Resumo por estado
Regiões econômicas/comerciais
Municípios da região selecionada
Microrregiões
Perfil demográfico
Receita por categoria
IDC / Margin Pool
Exportação de bases
```

### Regra de região econômica

```text
MG:
usa Região Comercial MG

SP, RJ e ES:
usam mesorregião IBGE como região econômica inicial

Se mesorregião estiver vazia:
usa microrregião

Se tudo estiver vazio:
"Sem região econômica"
```

### Dados usados

```text
População
PIB
IDH/IDHM
Demografia por sexo/faixa etária
Renda média
Classe de renda
PDV proxy
Receita por categoria
Vendas internas, quando carregadas
```

---

## 3.7 🧪 What-if / Simulador IDC

### Função

Permite alterar pesos dos critérios de expansão.

Exemplo de pesos:

```text
Peso população
Peso PIB
Peso masculino
Peso feminino
Peso faixa etária
Peso renda
Peso PDV
```

### Resultado esperado

O app calcula:

```text
Novo IDC
Novo score
Nova classificação
Comparação entre IDC atual e IDC simulado
```

---

# 4. Aba principal — 📈 Análise Previsão de Mercado

## 4.1 Objetivo

A aba **Análise Previsão de Mercado** concentra mercado, preços, compras, fontes externas, alertas e futuras previsões.

Ela responde:

```text
Como estão proteínas e grãos?
Quais fontes externas estão carregadas?
Qual é o histórico CEAGESP?
Qual é o preço real de compra?
Qual a prévia dos vendedores?
Quais alertas estão ativos?
Quais dados estão prontos para Machine Learning?
```

## 4.2 Subabas internas

```text
🥩 Proteínas e Grãos
🔌 Fontes Reais
📈 Análise Previsão de Mercado
🚨 Alertas Ativos
📄 Relatório Executivo
🩺 Saúde do Sistema
```

---

## 4.3 🥩 Proteínas e Grãos

### Função

Mostra comparação entre proteínas e insumos.

Exemplos:

```text
Tilápia
Frango
Boi
Suíno
Milho
Soja
```

### Uso

Ajuda a entender competitividade, substituição de proteínas e pressão de custo.

---

## 4.4 🔌 Fontes Reais

### Função

Mostra o status das fontes externas.

### Fontes previstas

```text
Comex Stat
CEPEA
CONAB
CEAGESP manual
Banco Central
IBGE
```

### Melhorias aplicadas

A tela separa:

```text
Últimas cargas com sucesso
Últimos erros
Histórico completo
Status atual Comex
```

Isso evita interpretar erro antigo como erro atual.

---

## 4.5 📈 Análise Previsão de Mercado

### Função

Centraliza bases e análises de mercado.

Blocos esperados:

```text
Radar econômico último ano
Proteínas e grãos juntos
CEAGESP manual/histórico
Base de compra manual
Prévia vendedores
Importações de pescados
Futuras previsões de preço
Futuras previsões de demanda
Cenários
Exportação das bases
```

---

## 4.6 🚨 Alertas Ativos

### Função

Mostra alertas gerados por regras de negócio.

Exemplos:

```text
Pescado perdendo competitividade
Pressão de custo de ração
Risco de substituição por outra proteína
Falha de carga em fonte importante
```

---

## 4.7 📄 Relatório Executivo

### Função

Consolida os principais resultados em texto executivo.

Uso esperado:

```text
enviar por WhatsApp
apresentar para liderança
usar como resumo semanal/mensal
```

---

## 4.8 🩺 Saúde do Sistema

### Função

Mostra se o pipeline está saudável.

Indicadores:

```text
últimas execuções
etapas com erro
fontes pendentes
quantidade de registros
diagnóstico V2
```

---

# 5. Fontes de dados

## 5.1 Fontes públicas

```text
IBGE Localidades
IBGE SIDRA
PNUD/IDHM via Jina Reader e fallback IBGE
Banco Central
Comex Stat
CEPEA
CONAB
CEAGESP, atualmente manual/controlado
```

## 5.2 Fontes internas/manuais

```text
Base de compra manual
Prévia vendedores
Vendas internas
Região Comercial MG
CEAGESP manual
```

---

# 6. Diagnóstico V2

O diagnóstico V2 é a tabela de controle que mostra o que está OK e o que ainda falta.

Itens principais:

```text
expansao_populacao
expansao_pib
expansao_idh_atlas_brasil
expansao_demografia_censo
expansao_renda_censo
expansao_pdv
comex_stat_refinado
ceagesp_pescados_manual
base_compra_manual
previa_vendedores
```

## Status possíveis

```text
OK
OK_PROXY_ESTIMADO
OK_COM_DADOS
OK_SEM_DADOS
PARCIAL
PENDENTE
PENDENTE_IMPORTACAO
PENDENTE_BASE_PDV
PENDENTE_CENSO_DEMOGRAFIA
PENDENTE_RENDA
```

---

# 7. Como rodar o APP

## Rodar tudo até a Etapa 23

```bat
cd /d "C:\Users\ducar\OneDrive\Área de Trabalho\Pescados"

scripts\rodar_tudo_etapa23.bat
```

## Rodar Etapas 24 a 28

```bat
cd /d "C:\Users\ducar\OneDrive\Área de Trabalho\Pescados"

scripts\rodar_etapas24_28.bat
```

## Abrir app depois de tudo pronto

```bat
cd /d "C:\Users\ducar\OneDrive\Área de Trabalho\Pescados"

.\.venv\Scripts\activate.bat

.\.venv\Scripts\python.exe -m streamlit run app.py
```

---

# 8. Como atualizar dados

## População, PIB, IDH e expansão

```bat
.\.venv\Scripts\python.exe scripts\run_expansao_publica.py --estados MG,SP,RJ,ES
.\.venv\Scripts\python.exe scripts\run_idh_automatico.py
.\.venv\Scripts\python.exe scripts\preencher_idh_faltantes_ibge.py
```

## Demografia e renda

```bat
.\.venv\Scripts\python.exe scripts\run_censo_demografico_2022.py --estados MG,SP,RJ,ES --sobrescrever
```

## PDV proxy

```bat
.\.venv\Scripts\python.exe scripts\run_pdv_proxy.py --estados MG,SP,RJ,ES --sobrescrever
```

## CEAGESP manual

```bat
.\.venv\Scripts\python.exe scripts\criar_template_ceagesp_manual.py
.\.venv\Scripts\python.exe scripts\load_ceagesp_manual_file.py --arquivo "data\input\ceagesp_manual.csv"
```

## Base de compra manual

```bat
.\.venv\Scripts\python.exe scripts\criar_templates_etapas27_28.py
.\.venv\Scripts\python.exe scripts\load_compra_manual_file.py --arquivo "data\input\base_compra_manual.csv"
```

## Prévia vendedores

```bat
.\.venv\Scripts\python.exe scripts\load_previa_vendedores_file.py --arquivo "data\input\previa_vendedores.csv"
```

## Comex refinado

```bat
.\.venv\Scripts\python.exe scripts\run_comex_refinado.py --ano-inicio 2020 --ano-fim 2026 --delay 12 --max-tentativas 2
```

---

# 9. Futuras atualizações recomendadas

## Curto prazo

```text
trocar demografia/renda proxy por SIDRA municipal fino
trocar PDV proxy por CNPJ/CNAE ou Overpass
melhorar importação manual de compras
melhorar importação manual de prévia vendedores
criar botões de upload dentro do Streamlit
```

## Médio prazo

```text
criar controle de versão das cargas
criar painel de qualidade dos dados
criar agenda automática de atualização
criar exportação executiva em Excel/PDF
melhorar relatório executivo automático
```

## Longo prazo

```text
previsão de preço
previsão de demanda
score de oportunidade regional por Machine Learning
segmentação de regiões
detecção de anomalias
cenários: catástrofe, pessimista, realista, otimista e otimista+
```

---

# 10. Observação importante

Os dados marcados como proxy são úteis para MVP, ranking e priorização inicial.

Eles não devem ser tratados como contagem oficial.

Campos proxy atuais:

```text
demografia/renda, até carga SIDRA fina
PDV, até carga CNPJ/CNAE ou fonte geográfica oficial
```

O app sempre deve manter a coluna de fonte clara:

```text
fonte_demografia
fonte_renda
fonte_pdv
```
