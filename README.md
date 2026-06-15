https://projetopescados-wscfj2qoztdevsyeqdrzyi.streamlit.app/
# Radar Pescados IA

Sistema de inteligência comercial, econômica e setorial para empresas de pescados.

O projeto integra dados internos de vendas com indicadores públicos e setoriais, calcula scores regionais, gera recomendações, simula cenários, emite alertas ativos, produz relatório executivo e executa o fluxo completo por pipeline.

---

## 1. Objetivo do projeto

O Radar Pescados IA foi criado para responder perguntas de negócio como:

- Quais regiões têm maior potencial de expansão?
- Onde vale adicionar vendedor, promotor ou campanha?
- O pescado está perdendo competitividade para frango, suíno, boi ou ovos?
- A pressão de custo de grãos, ração, dólar ou importação está aumentando?
- Quais regiões exigem atenção comercial imediata?
- O que aconteceria se o dólar subisse, o frango caísse ou a tilápia encarecesse?
- Quais alertas precisam chegar ao Comercial, Marketing, Compras ou Precificação?

A proposta é transformar dados em decisão, não apenas mostrar gráficos.

---

## 2. Stack utilizada

- Python
- Streamlit
- PostgreSQL
- SQLAlchemy
- Pandas
- Plotly
- OpenPyXL
- Requests
- APIs públicas:
  - Banco Central do Brasil
  - IBGE
  - Comex Stat
- Arquivos externos:
  - CONAB
  - CEPEA
  - Vendas internas

---

## 3. Arquitetura resumida

```text
APIs / Arquivos / Vendas
        ↓
Raw / Staging
        ↓
DW PostgreSQL
        ↓
Indicadores e Scores
        ↓
Recomendações
        ↓
What-if / Alertas / Relatório Executivo
        ↓
Streamlit + Pipeline Mestre
```

Schemas principais:

```text
raw       → payloads brutos de API
staging   → dados temporários de carga
dw        → fatos e dimensões analíticas
app       → scores, recomendações, alertas, relatórios e pipeline
ml        → reservado para evolução de modelos
```

---

## 4. Funcionalidades principais

### Radar Econômico

- Dólar
- Selic
- IPCA geral
- IPCA alimentação e bebidas

### Geografia e Potencial Regional

- Municípios do Brasil
- Regiões comerciais de Minas Gerais
- População estimada
- Potencial por região
- Venda per capita
- Cobertura de clientes

### Vendas Internas

- Carga de arquivo de vendas
- Dimensões de cliente, produto, vendedor e canal
- Fato de vendas
- Faturamento, volume e clientes

### Proteínas e Grãos

- Comparação entre proteínas
- Tilápia, salmão, bacalhau, camarão, frango, suíno, bovino e ovos
- Milho, soja, farelo de soja e farinha de peixe
- Base 100
- Razão entre proteínas
- Indicadores setoriais

### Fontes Reais

- Comex Stat
- CONAB
- CEPEA
- NCMs configuráveis para pescados
- Histórico de cargas reais

### Scores e Recomendações

- Score de oportunidade
- Score de risco
- Score de potencial
- Score setorial
- Cenário de 1 a 10
- Confiança
- Motor de decisão
- Recomendação comercial

### What-if / Sandbox

Simula cenários como:

- Dólar +10%
- Frango -8%
- Tilápia +5%
- Grãos +12%
- Adicionar vendedor
- Adicionar promotor
- Fazer campanha
- Melhorar cobertura
- Aumentar mix premium

### Alertas Ativos

Gera alertas para:

- Comercial
- Marketing
- Compras
- Precificação
- Gestão
- Gestão de Dados

### Relatório Executivo

Gera:

- Excel
- HTML
- Mensagem pronta para WhatsApp
- Histórico no PostgreSQL

### Pipeline Mestre

Executa o fluxo completo com um comando:

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos
```

---

## 5. Como rodar o projeto

### 5.1 Ativar ambiente

```bash
cd "C:\Users\ducar\OneDrive\Área de Trabalho\Pescados"
.venv\Scripts\activate
```

### 5.2 Configurar `.env`

Crie um arquivo `.env` na raiz:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=PESCADOSTESTE
DB_USER=postgres
DB_PASSWORD=postgres

APP_ENV=local
DATA_INICIO_PADRAO=2000-01-01
```

### 5.3 Inicializar banco

```bash
python scripts\init_db.py
```

### 5.4 Rodar pipeline completo

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos
```

### 5.5 Abrir app

```bash
streamlit run app.py
```

---

## 6. Pipeline principal

Pipeline padrão:

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos
```

Com Comex Stat:

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos --comex --comex-delay 30
```

Com arquivos CONAB e CEPEA:

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos --conab-file "data\input\conab_precos_milho_soja.xlsx" --cepea-file "data\input\cepea_tilapia.xlsx"
```

Com vendas reais:

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos --vendas-file "data\input\vendas.xlsx"
```

Sem relatório:

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos --sem-relatorio
```

---

## 7. Scripts principais

```text
scripts/init_db.py                         Inicializa banco e schemas
scripts/run_bcb_load.py                    Carrega Banco Central
scripts/run_ibge_localidades.py            Carrega localidades IBGE
scripts/calculate_potencial.py             Calcula potencial regional
scripts/load_vendas_file.py                Carrega vendas internas
scripts/load_indicadores_setoriais_file.py Carrega indicadores setoriais por arquivo
scripts/run_comex_pescados.py              Carrega Comex Stat
scripts/load_conab_file.py                 Carrega arquivo CONAB
scripts/load_cepea_file.py                 Carrega arquivo CEPEA
scripts/calculate_indices_setoriais.py     Calcula índices de proteínas/grãos
scripts/calculate_scores.py                Calcula scores regionais
scripts/generate_recommendations.py        Gera recomendações
scripts/simulate_whatif.py                 Simula cenário por terminal
scripts/generate_active_alerts.py          Gera alertas ativos
scripts/generate_executive_report.py       Gera relatório executivo
scripts/run_pipeline_full.py               Executa pipeline mestre
scripts/check_db.py                        Verifica saúde do banco
scripts/validate_project.py                Valida estrutura do projeto
```

---

## 8. Estrutura de pastas

```text
Pescados/
├─ app.py
├─ README.md
├─ requirements.txt
├─ .env.example
├─ config/
├─ data/
│  ├─ exemplo/
│  └─ input/
├─ docs/
├─ outputs/
│  └─ relatorios/
├─ scripts/
└─ src/
   ├─ collectors/
   ├─ config/
   ├─ database/
   ├─ etl/
   ├─ services/
   └─ utils/
```

---

## 9. Documentação complementar

Consulte a pasta `docs/`:

```text
docs/ARQUITETURA.md
docs/GUIA_EXECUCAO.md
docs/DICIONARIO_DADOS.md
docs/DECISOES_TECNICAS.md
docs/TROUBLESHOOTING.md
docs/PORTFOLIO.md
docs/ROADMAP.md
docs/CHANGELOG.md
docs/CHECKLIST_APRESENTACAO.md
```

---

## 10. Observação importante

Os resultados são probabilísticos e dependem da qualidade das fontes internas e externas.

O app não deve ser tratado como verdade absoluta. Ele é uma ferramenta de apoio à decisão, análise e priorização.

---

## 11. Status

Versão atual:

```text
Etapa 17 — Limpeza, README final e preparação para portfólio
```

Projeto com fluxo completo validado:

```text
Coleta → DW → Scores → Recomendações → Simulações → Alertas → Relatório → Pipeline
```


---

# Etapa 18 — Testes Automatizados

Esta etapa adiciona testes com `pytest`.

## Rodar todos os testes

```bash
python scripts\run_tests.py
```

## Rodar testes sem banco

```bash
python scripts\run_tests_no_db.py
```

## Rodar diretamente com pytest

```bash
python -m pytest -q
```

## Documentação

Consulte:

```text
docs/TESTES.md
```


---

## Instalação rápida no notebook

Para notebook novo, leia primeiro:

```text
LEIA_PRIMEIRO_NOTEBOOK.md
docs/INSTALACAO_NOTEBOOK_POSTGRES.md
```

Fluxo resumido:

```bat
scripts\setup_notebook.bat
python scripts\create_database.py
python scripts\init_db.py
scripts\primeiro_uso_notebook.bat
streamlit run app.py
```

O `.env` deste pacote está preparado para:

```env
DB_NAME=pescadosteste
DB_USER=postgres
DB_PASSWORD=12345
```

Se você usar outra senha no PostgreSQL, altere o `.env`.


---

## Hotfix fontes 2020–2026

Se a aba de proteínas/grãos aparecer só com 2024–2026 ou poucos itens, rode:

```bat
scripts\recarregar_fontes_2020_2026.bat
```

Ou pelo pipeline:

```bat
python scripts\run_pipeline_full.py --uf MG --usuario Marcos --ibge-localidades --ibge-populacao --comex --comex-ano-inicio 2020 --comex-ano-fim 2026 --comex-delay 60 --conab-file "data\input\conab_precos_milho_soja.xlsx" --cepea-file "data\input\cepea_tilapia.xlsx" --vendas-file "data\exemplo\vendas_exemplo.csv" --continuar-no-erro
```

Para corrigir a aba Região Comercial MG:

```bat
python scripts\apply_regioes_mg.py
```

Diagnóstico:

```bat
python scripts\diagnosticar_fontes_setoriais.py
```

Detalhes:

```text
docs/HOTFIX_FONTES_2020_2026.md
```


---

# Etapa 21 — Mapas Geográficos Reais

Esta etapa adiciona mapas reais do IBGE:

- Brasil por UF;
- Minas Gerais por município;
- regiões comerciais de MG coloridas no mapa;
- mapa de potencial regional;
- clique no mapa para selecionar região comercial.

## Rodar

```bat
python scripts\baixar_malhas_ibge.py
python scripts\apply_regioes_mg.py
streamlit run app.py
```

Ou:

```bat
scripts\atualizar_mapas_ibge.bat
```

Documentação:

```text
docs/ETAPA21_MAPAS_GEOGRAFICOS.md
```


---

# Hotfix mapas reais retângulo/zoom

Se o mapa aparecer como um retângulo gigante ou MG minúsculo, rode:

```bat
scripts\limpar_cache_mapas.bat
```

ou manualmente:

```bat
python scripts\baixar_malhas_ibge.py --force
python scripts\diagnosticar_mapas.py
streamlit run app.py
```

Documentação:

```text
docs/HOTFIX_MAPAS_RETANGULO_ZOOM.md
```


---

# Hotfix definitivo mapas Folium/Leaflet

```bat
pip install -r requirements.txt
scripts\limpar_cache_mapas_folium.bat
streamlit run app.py
```


---

# Hotfix colormap dos mapas

Corrige erro:

```text
'_LinearColormaps' object has no attribute 'Viridis_09'
```

Rode:

```bat
pip install -r requirements.txt
streamlit run app.py
```

Documentação:

```text
docs/HOTFIX_MAPAS_COLORMAP.md
```


---

# Hotfix mapas simples em blocos

A visualização geográfica real foi substituída por mapas simples em blocos/treemap para evitar erros visuais e dependência de GeoJSON.

## Rodar

```bat
streamlit run app.py
```

Não precisa rodar download de malhas.

Documentação:

```text
docs/HOTFIX_MAPAS_SIMPLES.md
```


---

# Hotfix métricas dos mapas simples

Corrige erro ao trocar métrica dos mapas simples para Faturamento, Volume ou Clientes quando os valores estão zerados.

A área dos blocos agora usa `qtd_municipios`, e a métrica selecionada controla a cor.

```bat
streamlit run app.py
```

Documentação:

```text
docs/HOTFIX_METRICAS_MAPAS_SIMPLES.md
```


---

# Etapa 22 — Reestruturação V2

A aba `🌎 Potencial Regional` foi evoluída para:

```text
🌎 Análise de Expansão
```

E foi criada a nova aba:

```text
📈 Análise Previsão de Mercado
```

## Rodar

```bat
streamlit run app.py
```

## Documentação

```text
docs/ETAPA22_V2_ABAS_EXPANSAO_PREVISAO.md
README_V2_EXPANSAO_PREVISAO.md
```


---

# Rodar do zero

Leia:

```text
RODAR_DO_ZERO.md
```

Comandos:

```bat
cd /d "C:\Users\ducar\OneDrive\Área de Trabalho\Nova pasta"
scripts\setup_do_zero.bat
scripts\primeira_execucao_do_zero.bat
scripts\abrir_app.bat
```


---

# Correção importante — Python 3.12

Use Python 3.12 para rodar o projeto.

Não use Python 3.14, pois o pandas pode tentar compilar do zero e quebrar.

Comandos:

```bat
py -0p
scripts\recriar_venv_python312.bat
```


---

# Ajuste V2 — dados públicos e aderência ao plano

A interface foi alinhada ao plano da versão 2.0 e passou a diferenciar dado real, pendente e estrutura preparada.

## Novos comandos

```bat
python scripts/apply_expansao_v2_publica.py
python scripts/run_expansao_publica.py --estados MG,SP,RJ,ES
python scripts/run_ceagesp_pescados.py
python scripts/diagnosticar_v2_plano.py
```

## Documentação

```text
docs/AJUSTE_PLANO_V2_DADOS_PUBLICOS.md
```


---

# Hotfix V2 — 100% alinhado ao plano

Correções principais:

```text
Geografia IBGE sem erro de metric
Saúde do Sistema sem erro de dict
What-if com parâmetros corretos
Sem zeros falsos em IDH/renda/PDV
CEAGESP com chave de carga robusta
Abas finais exatamente conforme plano V2
```

Documentação:

```text
docs/HOTFIX_V2_100_ALINHADO.md
```


---

# Hotfix CEAGESP + Arrow

Correções:

```text
lxml/html5lib adicionados ao requirements
CEAGESP não derruba mais o pipeline se a leitura HTML falhar
FutureWarning do read_html corrigido com StringIO
Warning Arrow da coluna variacao_mensal_pct corrigido
```

Comandos:

```bat
pip install -r requirements.txt
python scripts\run_ceagesp_pescados.py
python scripts\diagnosticar_v2_plano.py
streamlit run app.py
```

Documentação:

```text
docs/HOTFIX_CEAGESP_ARROW.md
```


---

# Importadores manuais e IDH

Novos scripts:

```bat
python scripts\criar_templates_importacao.py
python scripts\load_ceagesp_manual_file.py --arquivo "data\input\ceagesp_manual.csv"
python scripts\load_compra_manual_file.py --arquivo "data\input\base_compra.csv"
python scripts\load_previa_vendedores_file.py --arquivo "data\input\previa_vendedores.csv"
python scripts\load_idh_file.py --arquivo "data\input\idh_municipal.csv"
```

Documentação:

```text
docs/IMPORTADORES_MANUAIS_E_IDH.md
```


---
# Fontes automáticas — IDH/IDHM e CEAGESP
```bat
python scripts\apply_fontes_automaticas.py
python scripts\run_idh_automatico.py
python scripts\run_ceagesp_automatico.py --dias-busca 21
python scripts\diagnosticar_v2_plano.py
```


---

# Hotfix IDH automático — API + join

Corrige o IDH automático quando:

```text
PNUD retorna 403
dados.gov.br exige JavaScript
tabela IDHM não tem código IBGE
```

Comandos:

```bat
python scripts\apply_fontes_automaticas.py
python scripts\run_idh_automatico.py
python scripts\diagnosticar_v2_plano.py
```

Documentação:

```text
docs/HOTFIX_IDH_AUTOMATICO_API_JOIN.md
```


---

# Hotfix IDH automático — Atlas rawData XLSX

Agora o coletor tenta primeiro:

```text
http://atlasbrasil.org.br/2013/data/rawData/atlas2013_dadosbrutos_pt.xlsx
```

Comandos:

```bat
python scripts\apply_fontes_automaticas.py
python scripts\run_idh_automatico.py
python scripts\diagnosticar_v2_plano.py
```

Documentação:

```text
docs/HOTFIX_IDH_ATLAS_RAW_XLSX.md
```


---

# Hotfix IDH automático — Jina Reader

O coletor de IDH/IDHM agora usa fallback automático:

```text
https://r.jina.ai/https://www.undp.org/pt/brazil/idhm-municipios-2010
```

Comandos:

```bat
python scripts\apply_fontes_automaticas.py
python scripts\run_idh_automatico.py
python scripts\diagnosticar_v2_plano.py
```

Documentação:

```text
docs/HOTFIX_IDH_JINA_READER.md
```


---

# Hotfix IDH Jina Reader — Parser flexível

O `r.jina.ai` respondeu 200, mas o formato do texto não foi reconhecido. O parser agora aceita mais variações e salva um debug em:

```text
data/cache/idh_jina_reader_raw.txt
```

Comandos:

```bat
python scripts\run_idh_automatico.py
python scripts\debug_idh_jina.py
```

Documentação:

```text
docs/HOTFIX_IDH_JINA_PARSER.md
```


---

# Hotfix — IDH aliases + CEAGESP rápido

Comandos:

```bat
python scripts\corrigir_idh_aliases.py
python scripts\diagnosticar_v2_plano.py
python scripts\run_ceagesp_automatico.py --dias-busca 60 --timeout 8 --max-tentativas 12
```

Documentação:

```text
docs/HOTFIX_IDH_ALIAS_CEAGESP_FAST.md
```


---

# Hotfix — IDH fallback IBGE + CEAGESP formulário real

Comandos:

```bat
python scripts\preencher_idh_faltantes_ibge.py
python scripts\diagnosticar_v2_plano.py

python scripts\run_ceagesp_automatico.py --dias-busca 60 --timeout 8 --max-tentativas 20
python scripts\diagnosticar_v2_plano.py
```

Documentação:

```text
docs/HOTFIX_IDH_IBGE_CEAGESP_FORM.md
```


---

# Hotfix CEAGESP — Playwright

Quando `requests` não retorna a tabela da CEAGESP, use o coletor com navegador:

```bat
scripts\instalar_playwright_ceagesp.bat
python scripts\run_ceagesp_playwright.py --dias-busca 60 --max-datas 12
python scripts\diagnosticar_v2_plano.py
```

Para depurar com navegador visível:

```bat
python scripts\run_ceagesp_playwright.py --dias-busca 60 --max-datas 5 --visivel
```

Documentação:

```text
docs/HOTFIX_CEAGESP_PLAYWRIGHT.md
```


---

# CEAGESP Manual

A carga CEAGESP agora é manual/controlada.

```bat
python scripts\apply_ceagesp_manual.py
python scripts\criar_template_ceagesp_manual.py
python scripts\load_ceagesp_manual_file.py --arquivo "data\input\ceagesp_manual.csv"
python scripts\diagnosticar_v2_plano.py
```

Documentação:

```text
docs/CEAGESP_MANUAL.md
```


---

# Etapa 22 — Abas principais

O app agora está separado em 2 abas principais:

```text
🌎 Análise de Expansão
📈 Análise Previsão de Mercado
```

Cada aba principal mantém suas subabas internas em ordem de implementação.

Documentação:

```text
docs/ETAPA22_ABAS_PRINCIPAIS.md
```


---

# Etapa 23 — Expansão por estado/região

A aba **🌎 Análise de Expansão** agora permite selecionar:

```text
Estado base
Região econômica/comercial
```

Regra atual:

```text
MG usa Região Comercial MG
SP/RJ/ES usam mesorregião IBGE como região econômica inicial
```

Documentações:

```text
docs/ETAPA23_EXPANSAO_REGIOES_E_FORMULAS.md
docs/FORMULAS_E_ONDE_SAO_APLICADAS.md
```


---

# Rodar tudo — Etapa 23

Execute:

```bat
scripts\rodar_tudo_etapa23.bat
```

Para apenas abrir o app depois:

```bat
scripts\abrir_app_etapa23.bat
```

Documentação:

```text
docs/RODAR_TUDO_ETAPA23.md
```


---

# Hotfix — init_db views conflitantes

Quando o banco já tem views antigas, o PostgreSQL pode falhar com:

```text
não é possível alterar o nome da coluna ... da visão
```

Agora o projeto possui preflight automático:

```bat
.\.venv\Scripts\python.exe scripts\preflight_drop_conflicting_views.py
.\.venv\Scripts\python.exe scripts\init_db.py
```

Ou rode tudo:

```bat
scripts\rodar_tudo_etapa23.bat
```

Documentação:

```text
docs/HOTFIX_INIT_DB_VIEWS_CONFLITANTES.md
```


---

# Etapas 24 a 28 — Implementação

Execute:

```bat
scripts\rodar_etapas24_28.bat
```

Ou etapa por etapa:

```bat
.\.venv\Scripts\python.exe scripts\apply_etapas24_28.py
.\.venv\Scripts\python.exe scripts\run_censo_demografico_2022.py --estados MG,SP,RJ,ES
.\.venv\Scripts\python.exe scripts\run_pdv_proxy.py --estados MG,SP,RJ,ES
.\.venv\Scripts\python.exe scripts\criar_templates_etapas27_28.py
.\.venv\Scripts\python.exe scripts\run_comex_refinado.py --ano-inicio 2020 --ano-fim 2026 --delay 12 --max-tentativas 2
.\.venv\Scripts\python.exe scripts\diagnosticar_v2_plano.py
```

Documentação:

```text
docs/ETAPAS24_28_IMPLEMENTACAO.md
```


---

# Hotfix Layout V2.1

Ajustes aplicados:

```text
Filtro de período na Análise Previsão de Mercado
Dólar/Câmbio em bloco separado
Região Comercial MG consolidada na Análise de Expansão
Proteínas e Grãos consolidado na Análise Previsão de Mercado
Tabelas duplicadas limpas visualmente
```

Documentação:

```text
docs/HOTFIX_LAYOUT_V21_FILTROS_CONSOLIDACAO.md
```


---

# Validação Layout V2.1

Ajustes aplicados:

```text
Filtro de período/data na Análise Previsão de Mercado
Dólar/Câmbio separado
Região Comercial MG consolidada dentro da Análise de Expansão
Proteínas e Grãos consolidado dentro da Análise Previsão de Mercado
Mapa comercial/econômico simplificado dentro da Análise de Expansão
Tabelas duplicadas limpas visualmente
```

Validar:

```bat
.\.venv\Scripts\python.exe scripts\validar_layout_v21.py
```

Documentação:

```text
docs/VALIDACAO_LAYOUT_V21_FILTROS_CONSOLIDACAO.md
```


---

# Hotfix Expansão Receita IDC CEPEA

Execute:

```bat
scripts\rodar_hotfix_expansao_receita_cepea.bat
```

Base manual de receita:

```text
parceiro
cidade
estado
data_competencia
grupo_produto
vlr_total_liquido
```

Documentação:

```text
docs/HOTFIX_EXPANSAO_RECEITA_IDC_CEPEA.md
```


---

# Deploy Streamlit + Supabase

Este projeto está preparado para rodar localmente via `.env` ou online via `DATABASE_URL`.

Para publicar no Streamlit Cloud com Supabase:

```text
docs/DEPLOY_STREAMLIT_SUPABASE.md
```

Teste a conexão:

```powershell
$env:DATABASE_URL="postgresql+psycopg://postgres.PROJECT_REF:SUA_SENHA@aws-0-REGIAO.pooler.supabase.com:5432/postgres?sslmode=require"
.\.venv\Scripts\python.exe scripts\test_supabase_connection.py
```
