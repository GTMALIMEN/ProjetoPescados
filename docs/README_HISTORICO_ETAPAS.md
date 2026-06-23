

## Modo manual controlado CEPEA/CEAGESP

CEPEA e CEAGESP não usam mais proxy, scraper, Playwright ou coleta automática. Use somente a aba **Importações Manuais** com os modelos novos e o modo **Limpar base antiga e carregar somente este arquivo**.

# Radar Pescados IA

Projeto de inteligência de mercado para pescados, proteínas, grãos, ração, economia, importação e regiões comerciais.

Esta primeira implementação cobre a **Etapa 1 — Fundação + Banco + Coletor BCB**.

## O que já vem nesta base

- Estrutura modular do projeto;
- Streamlit inicial;
- PostgreSQL com schemas `raw`, `staging`, `dw`, `ml`, `app`;
- Tabelas principais de ETL, raw, staging BCB e série histórica;
- Índices iniciais;
- Materialized views iniciais;
- Configuração via `.env`;
- Coletor do Banco Central SGS;
- Carga `raw → staging → dw`;
- Controle de execução com `run_id`;
- Data Quality simples;
- Scripts de inicialização e carga BCB.

## Como rodar

### 1. Criar ambiente virtual

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/Mac:

```bash
source .venv/bin/activate
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar `.env`

Copie o arquivo `.env.example` para `.env`:

```bash
copy .env.example .env
```

ou:

```bash
cp .env.example .env
```

Edite os dados do PostgreSQL.

### 4. Criar banco e tabelas

Crie o banco no PostgreSQL, por exemplo:

```sql
CREATE DATABASE radar_pescados_ia;
```

Depois rode:

```bash
python scripts/init_db.py
```

### 5. Carregar histórico BCB

```bash
python scripts/run_bcb_load.py
```

Por padrão, o script tenta carregar desde `2000-01-01`.

### 6. Rodar o app

```bash
streamlit run app.py
```

## Próxima etapa depois desta base

- Adicionar coletor IBGE Localidades;
- Criar `dim_geografia`;
- Criar mapa Brasil/UF;
- Depois carregar vendas internas.


## Correção de execução no Windows

Se aparecer:

```text
ModuleNotFoundError: No module named 'src'
```

rode sempre os comandos dentro da pasta raiz do projeto, onde ficam `app.py`, `src/` e `scripts/`.

Comandos recomendados:

```bash
.venv\Scripts\activate
python scripts\init_db.py
python scripts\run_bcb_load.py
streamlit run app.py
```

Alternativa:

```bash
python -m scripts.init_db
python -m scripts.run_bcb_load
```

Não cole o caminho do `activate.bat` depois do comando `streamlit run app.py`.
Primeiro ative a venv. Depois rode o Streamlit em uma linha separada.


## Correção PostgreSQL: expressão de geração não é imutável

Se aparecer:

```text
psycopg.errors.InvalidObjectDefinition: a expressão de geração não é imutável
```

use esta versão corrigida. Ela remove as colunas `GENERATED ALWAYS AS` e usa uma chave natural `UNIQUE` segura para a série histórica.

Se o banco ficou parcialmente criado, rode:

```bash
python scripts\reset_db.py
python scripts\init_db.py
python scripts\run_bcb_load.py
streamlit run app.py
```

O `reset_db.py` apaga apenas os schemas do projeto: `app`, `raw`, `staging`, `dw` e `ml`.


## Correção AmbiguousParameter

Se aparecer:

```text
psycopg.errors.AmbiguousParameter: não foi possível determinar o tipo de dados do parâmetro
```

a função `carregar_series_dw` foi corrigida para montar a query com `WHERE` apenas quando houver indicador selecionado.

Para testar o banco:

```bash
python scripts\check_db.py
```

Depois:

```bash
streamlit run app.py
```


## Correção BCB HTTP 406

Se aparecer erro:

```text
406 Client Error: Not Acceptable
```

em séries como `Dólar venda` ou `Selic diária`, o coletor foi corrigido para buscar séries diárias em blocos anuais.

Depois de atualizar esta versão, rode:

```bash
python scripts\run_bcb_load.py
python scripts\check_db.py
streamlit run app.py
```

O app agora também lista apenas indicadores que existem no banco.


# Etapa 2 — IBGE Localidades + Geografia

Esta etapa adiciona:

- coletor IBGE Localidades;
- carga de UFs;
- carga de municípios;
- staging `staging.ibge_ufs`;
- staging `staging.ibge_municipios`;
- dimensão `dw.dim_geografia`;
- tabela `app.dim_regiao_comercial`;
- aba `Geografia IBGE` no Streamlit.

## Rodar a Etapa 2

Primeiro atualize o banco:

```bash
python scripts\init_db.py
```

Depois rode a carga IBGE:

```bash
python scripts\run_ibge_localidades.py
```

Verifique:

```bash
python scripts\check_db.py
```

Rode o app:

```bash
streamlit run app.py
```

Resultado esperado:

```text
Municípios em dw.dim_geografia: 5570
```

A quantidade pode variar se o IBGE atualizar a base.


## Correção IBGE NumericValueOutOfRange

Se aparecer:

```text
psycopg.errors.NumericValueOutOfRange: inteiro fora do intervalo
```

na carga `run_ibge_localidades.py`, isso ocorre quando o IBGE retorna algum município com campos hierárquicos antigos ausentes, como microrregião/mesorregião/UF, e o pandas envia `NaN` para colunas inteiras.

Esta versão corrige:

- `NaN` → `None` antes do insert;
- IDs convertidos para `int` Python puro;
- colunas de ID alteradas para `BIGINT`;
- UF/região inferida pelo prefixo do código IBGE quando a estrutura antiga vier ausente.

Rode:

```bash
python scripts\init_db.py
python scripts\reset_ibge.py
python scripts\run_ibge_localidades.py
python scripts\check_db.py
streamlit run app.py
```


# Etapa 3 — Região Comercial MG

Esta etapa adiciona:

- classificação inicial dos municípios de MG por região comercial;
- script `scripts/apply_regioes_mg.py`;
- atualização de `app.dim_regiao_comercial`;
- atualização de `dw.dim_geografia.regiao_comercial`;
- funções comerciais em `geografia_service.py`;
- aba `Região Comercial MG` no Streamlit;
- gráfico de barras por região comercial;
- treemap comercial simplificado.

## Rodar a Etapa 3

Garanta que a Etapa 2 já funcionou:

```bash
python scripts\run_ibge_localidades.py
```

Depois aplique as regiões de MG:

```bash
python scripts\apply_regioes_mg.py
```

Verifique:

```bash
python scripts\check_db.py
```

Rode o app:

```bash
streamlit run app.py
```

Resultado esperado:

```text
Municípios MG com região comercial: 853
```

A classificação inicial usa a mesorregião do IBGE. Depois, o cadastro pode ser ajustado manualmente para refletir a regra comercial real da empresa.


# Etapa 4 — Carga de Vendas Internas

Esta etapa adiciona:

- importador flexível para `.csv`, `.xlsx`, `.xls` e `.xlsb`;
- detecção automática de colunas comuns da base Sankhya/vendas;
- staging `staging.vendas_internas`;
- carga de dimensões:
  - `dw.dim_cliente`;
  - `dw.dim_produto`;
  - `dw.dim_vendedor`;
  - `dw.dim_canal`;
- carga da `dw.fato_vendas`;
- cruzamento com `dw.dim_geografia`;
- herança de `regiao_comercial` para MG;
- `app.mv_vendas_mensal_geo`;
- aba `Vendas Internas` no Streamlit.

## Atualizar dependências

```bash
pip install -r requirements.txt
```

## Atualizar banco

```bash
python scripts\init_db.py
```

## Testar com arquivo exemplo

```bash
python scripts\load_vendas_file.py --arquivo data\exemplo\vendas_exemplo.csv
python scripts\check_db.py
streamlit run app.py
```

## Carregar arquivo real

Coloque seu arquivo em `data/input/` e rode:

```bash
python scripts\load_vendas_file.py --arquivo "data\input\SEU_ARQUIVO.xlsx"
```

Para `.xlsb`:

```bash
python scripts\load_vendas_file.py --arquivo "data\input\SEU_ARQUIVO.xlsb"
```

Se o arquivo Excel tiver várias abas:

```bash
python scripts\load_vendas_file.py --arquivo "data\input\SEU_ARQUIVO.xlsx" --sheet "Nome da Aba"
```

## Colunas esperadas ou detectadas automaticamente

O importador tenta detectar automaticamente colunas como:

- Dt. Faturamento;
- Nro. Único;
- Nro. Nota;
- Cod. Parceiro;
- Parceiro;
- CPF / CNPJ;
- Perfil Parceiro;
- Nome Cidade;
- UF;
- Cód. Produto;
- Desc. Produto;
- Desc. Grupo do Produto;
- Vendedor;
- Tipo de Negociação;
- Vlr. Total Liquido;
- Peso Líquido do Produto (Kg);
- Quantidade.

Depois da carga, confira o diagnóstico impresso no terminal com as colunas detectadas.


# Etapa 5 — Score Inicial de Oportunidade e Risco

Esta etapa adiciona:

- `app.config_score_versao`;
- `app.config_pesos_score`;
- `app.fato_score_regional`;
- `app.mv_score_regional_atual`;
- cálculo inicial de oportunidade regional;
- cálculo inicial de risco regional;
- cálculo do score final;
- cenário 1 a 10;
- confiança do score;
- JSONB `principais_fatores`;
- aba `Scores Iniciais` no Streamlit.

## Atualizar banco

```bash
python scripts\init_db.py
```

## Calcular scores

```bash
python scripts\calculate_scores.py --uf MG --salvar
```

## Verificar banco

```bash
python scripts\check_db.py
```

## Rodar app

```bash
streamlit run app.py
```

## Observação importante

O score inicial funciona mesmo sem a base real de vendas, usando geografia e pressão macroeconômica.  
Quando a base real de vendas for carregada, rode novamente:

```bash
python scripts\calculate_scores.py --uf MG --salvar
```

Assim o score passa a considerar vendas, volume, clientes e queda de demanda.


# Etapa 6 — Recomendações Comerciais

Esta etapa adiciona:

- `app.config_roi_acao`;
- `app.fato_recomendacao`;
- `app.feedback_recomendacao`;
- `app.mv_recomendacao_atual`;
- geração de recomendação por região comercial;
- decisão entre adicionar vendedor, adicionar promotor, campanha, monitorar, corrigir mix/preço ou aguardar dados reais;
- ROI estimado;
- scores concorrentes de vendedor, promotor e campanha;
- aba `Recomendações` no Streamlit.

## Rodar a Etapa 6

```bash
python scripts\init_db.py
python scripts\calculate_scores.py --uf MG --salvar
python scripts\generate_recommendations.py --uf MG --salvar
python scripts\check_db.py
streamlit run app.py
```

Sem base real de vendas, as recomendações serão conservadoras, geralmente `aguardar_dados_reais`.
Depois que a base real for carregada, rode novamente:

```bash
python scripts\calculate_scores.py --uf MG --salvar
python scripts\generate_recommendations.py --uf MG --salvar
```


# Etapa 7 — Saúde do Sistema / ETL / Auditoria

Esta etapa adiciona:

- `app.vw_etl_ultimas_execucoes`;
- `app.vw_etl_resumo_fonte`;
- `app.vw_etl_controle_carga`;
- `app.vw_data_quality_resumo`;
- `app.vw_saude_sistema`;
- serviço `health_service.py`;
- script `scripts/check_health.py`;
- aba `Saúde do Sistema` no Streamlit.

## Rodar a Etapa 7

```bash
python scripts\init_db.py
python scripts\check_health.py
streamlit run app.py
```

A aba `Saúde do Sistema` mostra:

- séries históricas carregadas;
- municípios carregados;
- vendas carregadas;
- scores;
- recomendações;
- execuções com erro;
- últimas cargas;
- contadores raw/staging/dw;
- Data Quality;
- tabelas do banco.

Essa etapa ajuda a validar a confiabilidade dos dados antes de tomar decisões comerciais.


# Hotfix — ON CONFLICT em dw.fato_vendas

Se aparecer o erro:

```text
psycopg.errors.InvalidColumnReference: não há nenhuma restrição de unicidade ou de exclusão que corresponda à especificação ON CONFLICT
```

na carga de vendas, aplique:

```bash
python scripts\hotfix_vendas_hash_index.py
```

Depois rode novamente:

```bash
python scripts\load_vendas_file.py --arquivo data\exemplo\vendas_exemplo.csv
python scripts\check_db.py
streamlit run app.py
```

Causa:
a versão anterior criou um índice único parcial em `chave_venda_hash`. O `ON CONFLICT (chave_venda_hash)` precisa de um índice único completo compatível.


# Hotfix 7.2 — View atual por data_calculo

Sintoma:

```text
calculate_scores.py mostra score novo,
mas check_db.py e o app continuam mostrando score antigo.
```

Causa:
a `app.mv_score_regional_atual` escolhia a maior `data_referencia`. Quando existia um score antigo sem vendas com data mais recente, ele continuava aparecendo como "atual".

Correção:
a view agora escolhe o cálculo mais recente por `data_calculo`. A recomendação atual também passa a escolher por `data_criacao`.

Rode:

```bash
python scripts\hotfix_latest_views.py
python scripts\calculate_scores.py --uf MG --salvar
python scripts\generate_recommendations.py --uf MG --salvar
python scripts\check_db.py
streamlit run app.py
```

Também foi ajustado o parser de datas para tratar datas ISO, como `2026-05-01`, sem inverter dia e mês.


# Etapa 7.3 — Saúde atual e correções finais

Correções aplicadas:

- A saúde do sistema agora separa erro histórico de erro ativo.
- `qtd_execucoes_com_erro` agora conta apenas fontes/indicadores cujo último status ainda é erro.
- `app.vw_etl_status_atual` mostra a última carga por fonte/indicador.
- `app.vw_etl_resumo_fonte` agora mostra o estado operacional atual.
- `app.vw_etl_resumo_fonte_historico` mantém o histórico completo de erros e sucessos.
- `app.mv_recomendacao_atual` passa a escolher a recomendação mais recente por `data_criacao`.
- O parser de datas de vendas agora trata corretamente datas ISO, como `2026-05-01`.
- A carga de vendas remove linhas antigas do mesmo `arquivo_origem` antes de recarregar, evitando duplicidade em reprocessamentos.

## Rodar correção

```bash
python scripts\init_db.py
python scripts\hotfix_health_current_status.py
python scripts\hotfix_latest_views.py
python scripts\load_vendas_file.py --arquivo data\exemplo\vendas_exemplo.csv
python scripts\calculate_scores.py --uf MG --salvar
python scripts\generate_recommendations.py --uf MG --salvar
python scripts\check_health.py
streamlit run app.py
```


# Etapa 8 — IBGE População e Potencial Regional

Esta etapa adiciona:

- coletor SIDRA/IBGE;
- carga da população residente estimada por município;
- `staging.ibge_sidra_municipal`;
- `dw.fato_indicador_municipal`;
- `app.fato_potencial_regional`;
- `app.mv_potencial_regional_atual`;
- `app.vw_indicador_municipal_geo`;
- scripts:
  - `scripts/run_ibge_populacao.py`;
  - `scripts/calculate_potencial.py`;
- nova aba no Streamlit: `Potencial Regional`.

## Rodar a Etapa 8

```bash
python scripts\init_db.py
python scripts\run_ibge_populacao.py
python scripts\calculate_potencial.py --uf MG --salvar
python scripts\check_db.py
streamlit run app.py
```

Para forçar um ano específico da tabela SIDRA 6579:

```bash
python scripts\run_ibge_populacao.py --periodo 2025
```

## O que o potencial mede

O score de potencial regional cruza:

- população estimada IBGE/SIDRA;
- faturamento interno;
- venda por habitante;
- cobertura de clientes por 100 mil habitantes;
- região comercial de MG.

Quanto maior a população e menor a penetração/cobertura atual, maior tende a ser a oportunidade não explorada.


# Etapa 8.1 — Correção init/auditoria

Correções aplicadas:

- `ibge_indicadores.sql` agora roda antes de `auditoria.sql` no `init_db.py`;
- `app.vw_saude_sistema` não referencia mais campos/tabelas antes de existirem;
- corrigido `status_atual` na auditoria;
- `mv_recomendacao_atual` agora mostra apenas a recomendação mais recente por região, evitando recomendação antiga + nova ao mesmo tempo;
- adicionado `scripts/hotfix_etapa8_db.py`.

Para aplicar:

```bash
python scripts\hotfix_etapa8_db.py
python scripts\init_db.py
python scripts\run_ibge_populacao.py
python scripts\calculate_potencial.py --uf MG --salvar
python scripts\check_db.py
streamlit run app.py
```


# Hotfix 8.2 — Potencial Regional MV ausente

Sintoma no Streamlit:

```text
ProgrammingError: relação "app.mv_potencial_regional_atual" não existe
```

Causa:
a aba Potencial Regional já estava no app, mas os objetos SQL da Etapa 8 ainda não tinham sido criados no banco, ou o `init_db.py` anterior falhou antes de executar `ibge_indicadores.sql`.

Correção:

```bash
python scripts\hotfix_potencial_mv.py
python scripts\run_ibge_populacao.py
python scripts\calculate_potencial.py --uf MG --salvar
python scripts\check_db.py
streamlit run app.py
```

O hotfix cria/verifica:

- `staging.ibge_sidra_municipal`;
- `dw.fato_indicador_municipal`;
- `app.fato_potencial_regional`;
- `app.mv_potencial_regional_atual`.

O serviço `potencial_service.py` também foi ajustado para mostrar aviso em vez de quebrar a tela caso a MV ainda não exista.


# Hotfix 8.3 — Auditoria e Potencial Regional

Corrige o erro:

```text
psycopg.errors.InvalidTableDefinition: não é possível alterar o nome da coluna "mensagem" da visão para "status_atual"
```

Causa: o PostgreSQL não permite `CREATE OR REPLACE VIEW` quando a troca altera a ordem/nome das colunas da view existente. A correção remove as views dependentes e recria em ordem segura.

Também corrige o script `hotfix_potencial_mv.py` para aplicar `ibge_indicadores.sql` e `auditoria.sql` em transações separadas, evitando rollback das tabelas da Etapa 8 caso a auditoria falhe.

Rode:

```bash
python scripts\hotfix_potencial_mv.py
python scripts\run_ibge_populacao.py
python scripts\calculate_potencial.py --uf MG --salvar
python scripts\check_db.py
streamlit run app.py
```


# Etapa 9 — Potencial Regional integrado aos Scores e Recomendações

Esta etapa integra o potencial regional calculado na Etapa 8 ao motor de decisão.

## O que muda

- `app.fato_score_regional` ganha `score_potencial`;
- `app.fato_recomendacao` ganha:
  - `score_potencial`;
  - `motor_decisao`;
- `app.mv_score_regional_atual` passa a exibir `score_potencial`;
- `app.mv_recomendacao_atual` passa a exibir `score_potencial` e `motor_decisao`;
- `calculate_scores.py` passa a usar população, venda per capita e cobertura comercial no score;
- `generate_recommendations.py` passa a decidir usando também o potencial não explorado;
- a aba `Scores Iniciais` mostra Potencial Regional x Oportunidade;
- a aba `Recomendações` mostra o motor da decisão.

## Rodar a Etapa 9

Garanta que a Etapa 8 já funcionou:

```bash
python scripts\hotfix_potencial_mv.py
python scripts\run_ibge_populacao.py
python scripts\calculate_potencial.py --uf MG --salvar
```

Depois aplique a Etapa 9:

```bash
python scripts\apply_etapa9.py
python scripts\calculate_scores.py --uf MG --salvar
python scripts\generate_recommendations.py --uf MG --salvar
python scripts\check_db.py
streamlit run app.py
```

## Resultado esperado

Agora o sistema passa a responder melhor:

```text
Onde eu vendi mais?
Onde eu tenho mais risco?
Onde eu tenho mais mercado ainda pouco explorado?
Qual recomendação veio por potencial, risco ou expansão comercial?
```

A recomendação pode mudar de `monitorar` para `campanha_marketing`, `adicionar_promotor` ou `adicionar_vendedor` quando houver potencial regional alto e base de vendas suficiente.


# Etapa 10 — Radar de Proteínas e Grãos

Esta etapa adiciona o radar setorial de proteínas, grãos e insumos.

## O que entra

- `staging.indicador_setorial`;
- `dw.fato_indicador_setorial`;
- `app.fato_indice_setorial`;
- `app.fato_alerta_setorial`;
- `app.mv_indice_setorial_atual`;
- `app.mv_alerta_setorial_atual`;
- `app.vw_indicador_setorial_mensal`;
- loader de arquivo setorial;
- cálculo de índices setoriais;
- aba `Proteínas e Grãos` no Streamlit.

## Índices calculados

- `competitividade_pescado`: compara tilápia/pescado contra frango, suíno, boi e ovos;
- `pressao_custo_racao`: monitora milho, soja, farelo, farinha de peixe e dólar;
- `risco_substituicao_proteinas`: detecta risco de substituição quando concorrentes ficam mais baratos e pescado encarece.

## Rodar a Etapa 10

```bash
python scripts\init_db.py
python scripts\load_indicadores_setoriais_file.py --arquivo data\exemplo\indicadores_setoriais_exemplo.csv
python scripts\calculate_indices_setoriais.py --uf MG --salvar
python scripts\check_db.py
streamlit run app.py
```

## Arquivo esperado

O loader aceita `.csv`, `.xlsx`, `.xls` e `.xlsb`.

Colunas esperadas/detectadas:

```text
data
fonte
indicador
categoria
subcategoria
produto
uf
regiao
valor
unidade
periodicidade
```

## Observação

A base de exemplo serve para validar o funcionamento. Depois ela pode ser substituída por dados reais de CEPEA, CONAB, Comex Stat, fornecedores, scraping autorizado ou bases internas.


# Etapa 10.1 — Melhorias no Radar de Proteínas

Esta melhoria deixa a aba `Proteínas e Grãos` mais útil para análise.

## Melhorias

- seleção manual das proteínas a comparar;
- seleção da proteína base;
- gráfico de preço original;
- gráfico normalizado em Base 100;
- gráfico de razão contra a proteína base;
- filtro de período;
- seleção de grãos/insumos;
- base exemplo histórica maior, de 2018 até 2026;
- novo arquivo:
  - `data/exemplo/indicadores_setoriais_historico_exemplo.csv`.

## Rodar a versão melhorada

```bash
python scripts\init_db.py
python scripts\load_indicadores_setoriais_file.py --arquivo data\exemplo\indicadores_setoriais_historico_exemplo.csv
python scripts\calculate_indices_setoriais.py --uf MG --salvar
python scripts\check_db.py
streamlit run app.py
```

## Observação importante

A base histórica incluída ainda é uma base de exemplo/simulação para validar a engenharia e a visualização.
Para decisão real, substitua por dados reais de fontes como bases internas, fornecedores, CEPEA, CONAB, Comex Stat ou scraping autorizado.


# Etapa 11 — Fontes reais setoriais

Esta etapa começa a substituir a base simulada por fontes reais.

## Fontes preparadas

- Comex Stat:
  - integração via API;
  - importações de salmão, bacalhau e camarão por NCM;
  - indicadores de valor FOB, kg e preço médio US$/kg.

- CONAB:
  - loader genérico para arquivos baixados do portal;
  - indicado para milho, soja, farelo e preços agropecuários.

- CEPEA:
  - loader genérico para planilhas exportadas pelo site;
  - indicado para tilápia, boi, frango, suíno, ovos, milho, soja etc.

## Rodar estrutura

```bash
python scripts\init_db.py
```

## Carregar Comex Stat

```bash
python scripts\run_comex_pescados.py --ano-inicio 2024 --ano-fim 2026
```

## Carregar arquivo CONAB

Baixe o arquivo no portal da CONAB e coloque em `data/input/`.

```bash
python scripts\load_conab_file.py --arquivo "data\input\conab_precos.xlsx" --categoria graos_racao --produto-default Milho --uf-default MG
```

## Carregar arquivo CEPEA

Exporte a planilha no site do CEPEA e coloque em `data/input/`.

```bash
python scripts\load_cepea_manual_file.py --criar-estrutura --substituir-tudo --arquivo "data\input\cepea_manual.xlsx"
```

## Recalcular índices

```bash
python scripts\calculate_indices_setoriais.py --uf MG --salvar
python scripts\check_db.py
streamlit run app.py
```

## Observações importantes

O CEPEA disponibiliza consultas e exportação de Excel pelo site, mas não foi tratado como API pública estável nesta etapa. Por isso o caminho mais seguro é exportar a planilha e carregar no DW.

A CONAB disponibiliza arquivos de download no portal. Como os layouts podem mudar por tipo de arquivo, o loader é flexível e detecta colunas de data, produto, UF e valor.

Os NCMs de pescados estão em `config/comex_pescados_ncm.json` e também em `app.config_ncm_pescado`. Ajuste conforme a classificação fiscal da empresa.


# Hotfix 11.1 — Comex Stat e fonte na view mensal

Correções:

- Comex Stat agora usa endpoint `/general?language=pt`;
- período no formato correto `AAAA-MM`;
- métricas reduzidas para `metricFOB` e `metricKG`;
- parser ajustado para resposta no formato `data.list`;
- `app.vw_indicador_setorial_mensal` agora inclui a coluna `fonte`;
- `fontes_reais_service.py` não quebra mais se a view antiga ainda estiver no banco.

## Rodar

```bash
python scripts\hotfix_comex_fontes_reais.py
python scripts\run_comex_pescados.py --ano-inicio 2024 --ano-fim 2026
python scripts\calculate_indices_setoriais.py --uf MG --salvar
python scripts\check_db.py
streamlit run app.py
```

Se a API retornar erro 400 novamente, o erro agora imprime também o `response` e o `payload`, facilitando ajustar filtro/NCM/métrica.


# Hotfix 11.2 — Rate limit Comex e arquivos input

Correções:

- Comex Stat agora faz retry automático quando receber erro `429 rate limit`;
- o coletor lê a mensagem da API e aguarda o tempo solicitado;
- adicionado delay entre grupos de NCMs;
- `scripts/run_comex_pescados.py` ganhou argumento `--delay`;
- criados arquivos de teste:
  - `data/input/conab_precos_milho_soja.xlsx`;
  - `data/input/cepea_tilapia.xlsx`.

## Rodar Comex com segurança

```bash
python scripts\run_comex_pescados.py --ano-inicio 2024 --ano-fim 2026 --delay 15
```

Se ainda aparecer rate limit, aumente:

```bash
python scripts\run_comex_pescados.py --ano-inicio 2024 --ano-fim 2026 --delay 30
```

## Testar CONAB e CEPEA com arquivos exemplo

```bash
python scripts\load_conab_file.py --arquivo "data/input/conab_precos_milho_soja.xlsx" --categoria graos_racao --produto-default Milho --uf-default MG

python scripts\load_cepea_manual_file.py --criar-estrutura --substituir-tudo --arquivo "data/input/cepea_manual.xlsx"

python scripts\calculate_indices_setoriais.py --uf MG --salvar
python scripts\check_db.py
streamlit run app.py
```

Observação: os arquivos em `data/input` são exemplos para validar o fluxo. Depois substitua pelos arquivos reais baixados de CONAB/CEPEA.


# Hotfix 11.3 — check_db atualizado

Correção do relatório `scripts/check_db.py`.

## Problema

O cálculo de scores e recomendações já estava correto, mas o `check_db.py` ainda não selecionava corretamente:

- `score_potencial` em `app.mv_score_regional_atual`;
- `motor_decisao` em `app.mv_recomendacao_atual`;
- `score_potencial` em `app.mv_recomendacao_atual`.

Por isso o terminal mostrava:

```text
potencial=0.00
motor=N/A
```

mesmo depois do cálculo correto.

## Rodar

```bash
python scripts\calculate_potencial.py --uf MG --salvar
python scripts\apply_etapa9.py
python scripts\calculate_scores.py --uf MG --salvar
python scripts\generate_recommendations.py --uf MG --salvar
python scripts\check_db.py
streamlit run app.py
```

Agora o `check_db.py` mostra o potencial e o motor da decisão corretamente.


# Etapa 12 — Indicadores Setoriais integrados aos Scores e Recomendações

Esta etapa conecta os índices setoriais ao motor de decisão.

## O que muda

Os índices abaixo deixam de ficar apenas na aba setorial e passam a influenciar os scores e recomendações:

- `competitividade_pescado`;
- `pressao_custo_racao`;
- `risco_substituicao_proteinas`.

## Novas colunas

Em `app.fato_score_regional`:

- `score_setorial`;
- `score_competitividade_setorial`;
- `score_pressao_custo_setorial`;
- `score_risco_substituicao_setorial`.

Em `app.fato_recomendacao`:

- `score_setorial`;
- `score_competitividade_setorial`;
- `score_pressao_custo_setorial`;
- `score_risco_substituicao_setorial`.

## Nova lógica

- Baixa competitividade do pescado aumenta risco.
- Alta pressão de custo aumenta risco.
- Alto risco de substituição aumenta risco.
- O score final considera oportunidade, risco, potencial e competitividade.
- A recomendação pode vir por:
  - `pressao_custo_setorial`;
  - `competitividade_substituicao`;
  - `potencial_regional`;
  - `potencial_execucao`;
  - `risco_regional`;
  - `dados_insuficientes`;
  - `monitoramento`.

## Rodar

```bash
python scripts\apply_etapa12.py
python scripts\calculate_indices_setoriais.py --uf MG --salvar
python scripts\calculate_potencial.py --uf MG --salvar
python scripts\calculate_scores.py --uf MG --salvar
python scripts\generate_recommendations.py --uf MG --salvar
python scripts\check_db.py
streamlit run app.py
```

## Leitura esperada

Se o pescado estiver perdendo competitividade:

```text
motor=competitividade_substituicao
ação=Criar ação defensiva de competitividade contra proteínas concorrentes
```

Se os custos estiverem pressionados:

```text
motor=pressao_custo_setorial
ação=Revisar preço, margem, compras e mix por pressão de custo
```


# Hotfix 12.1 — check_db sem erro no bloco de potencial

## Problema

O `check_db.py` tentava imprimir `score_setorial` dentro do bloco de `Potencial regional atual MG`.

A view `app.mv_potencial_regional_atual` não possui colunas setoriais, então aparecia:

```text
Could not locate column in row for column 'score_setorial'
```

## Correção

- O bloco de Potencial Regional agora imprime apenas:
  - `score_potencial`;
  - `cenario_1_10`;
  - `confianca`.

- O bloco de Scores imprime:
  - `score_setorial`;
  - `score_competitividade_setorial`;
  - `score_pressao_custo_setorial`;
  - `score_risco_substituicao_setorial`.

- O bloco de Recomendações imprime:
  - `motor_decisao`;
  - `score_setorial`;
  - `competitividade`;
  - `custo`;
  - `substituição`.

## Rodar

```bash
python scripts\check_db.py
streamlit run app.py
```


# Etapa 13 — Simulador What-if / Sandbox

Esta etapa adiciona uma aba para simular cenários antes de tomar decisão.

## O que entra

- `app.fato_simulacao_whatif`;
- `app.vw_whatif_ultimas_simulacoes`;
- `app.vw_whatif_resumo_regiao`;
- `src/services/whatif_service.py`;
- `scripts/apply_etapa13.py`;
- `scripts/simulate_whatif.py`;
- nova aba no Streamlit: `🧪 What-if`.

## O que o simulador responde

Exemplos:

```text
E se o dólar subir 10%?
E se o frango cair 8%?
E se a tilápia subir 5%?
E se grãos/ração subirem 12%?
E se eu fizer campanha no Sul de MG?
E se eu adicionar vendedor ou promotor?
E se eu melhorar cobertura comercial?
```

## Variáveis simuladas

Mercado:

- dólar;
- tilápia/pescado;
- frango;
- bovino;
- suíno;
- grãos/ração.

Ações comerciais:

- campanha;
- adicionar vendedor;
- adicionar promotor;
- melhorar cobertura;
- aumentar mix premium.

## Rodar

```bash
python scripts\apply_etapa13.py
python scripts\check_db.py
streamlit run app.py
```

## Testar por terminal

```bash
python scripts\simulate_whatif.py --regiao "Sul de MG" --dolar 10 --frango -8 --tilapia 5 --campanha --salvar
```

## Interpretação

A simulação é probabilística/heurística. Ela não dá certeza de resultado.
Ela serve para comparar cenários, entender direção provável e apoiar decisão.


# Etapa 14 — Alertas Ativos

Esta etapa transforma scores, recomendações, potencial e indicadores setoriais em alertas acionáveis.

## O que entra

- `app.config_alerta_ativo`;
- `app.fato_alerta_ativo`;
- `app.historico_alerta_ativo`;
- `app.config_notificacao_alerta`;
- `app.vw_alertas_ativos_atual`;
- `app.vw_alertas_resumo_area`;
- `app.vw_alertas_resumo_tipo`;
- `app.vw_alertas_historico_recente`;
- `src/services/active_alerts_service.py`;
- `scripts/apply_etapa14.py`;
- `scripts/generate_active_alerts.py`;
- `scripts/update_alert_status.py`;
- nova aba no Streamlit: `🚨 Alertas Ativos`.

## Tipos de alerta

- competitividade baixa do pescado;
- pressão de custo alta;
- risco de substituição entre proteínas;
- potencial alto com venda baixa;
- score regional baixo;
- dados insuficientes em região promissora;
- recomendação de correção de mix/preço.

## Áreas responsáveis

- Comercial;
- Marketing;
- Marketing/Comercial;
- Compras/Precificação;
- Precificação/Comercial;
- Gestão Comercial;
- Gestão de Dados/Comercial.

## Rodar

```bash
python scripts\apply_etapa14.py
python scripts\generate_active_alerts.py --uf MG --salvar
python scripts\check_db.py
streamlit run app.py
```

## Atualizar status pelo terminal

```bash
python scripts\update_alert_status.py --id 1 --status em_analise --comentario "Em tratativa com comercial" --usuario Marcos
python scripts\update_alert_status.py --id 1 --status resolvido --comentario "Ação executada" --usuario Marcos
```

## Observação

Nesta etapa, a notificação é dentro do painel.
Depois pode evoluir para e-mail, WhatsApp, Slack, Teams ou webhook.


# Etapa 15 — Relatório Executivo Automático

Esta etapa gera um relatório automático para diretoria/comercial.

## O que entra

- `app.fato_relatorio_executivo`;
- `app.vw_relatorios_executivos_recentes`;
- `app.vw_relatorio_executivo_ultimo`;
- `src/services/executive_report_service.py`;
- `scripts/apply_etapa15.py`;
- `scripts/generate_executive_report.py`;
- nova aba no Streamlit: `📄 Relatório Executivo`.

## O relatório inclui

- resumo executivo;
- mensagem pronta para WhatsApp;
- resumo de vendas;
- top oportunidades;
- top riscos;
- scores regionais;
- recomendações;
- alertas ativos;
- alertas por área;
- indicadores setoriais;
- simulações What-if recentes;
- fontes reais.

## Exportações

- Excel `.xlsx`;
- HTML `.html`;
- texto pronto para WhatsApp;
- histórico salvo no PostgreSQL.

## Rodar

```bash
python scripts\apply_etapa15.py
python scripts\generate_executive_report.py --uf MG --usuario Marcos
python scripts\check_db.py
streamlit run app.py
```

## Arquivos gerados

Os arquivos ficam em:

```text
outputs/relatorios/
```

## Observação

O relatório usa os dados disponíveis no banco no momento da geração.
Antes de gerar para uso real, rode as cargas e recálculos necessários:

```bash
python scripts\calculate_indices_setoriais.py --uf MG --salvar
python scripts\calculate_potencial.py --uf MG --salvar
python scripts\calculate_scores.py --uf MG --salvar
python scripts\generate_recommendations.py --uf MG --salvar
python scripts\generate_active_alerts.py --uf MG --salvar
```


# Etapa 16 — Pipeline Mestre / Orquestração

Esta etapa cria um pipeline único para executar o fluxo completo do Radar Pescados IA.

## O que entra

- `app.pipeline_execucao`;
- `app.pipeline_etapa_execucao`;
- `app.vw_pipeline_ultimas_execucoes`;
- `app.vw_pipeline_etapas_recentes`;
- `app.vw_pipeline_saude`;
- `src/services/pipeline_service.py`;
- `scripts/apply_etapa16.py`;
- `scripts/run_pipeline_full.py`;
- nova aba no Streamlit: `⚙️ Pipeline`.

## Fluxo principal

O pipeline pode executar:

1. estrutura da Etapa 16;
2. `init_db`;
3. Banco Central;
4. IBGE localidades;
5. IBGE população;
6. Comex Stat;
7. arquivo CONAB;
8. arquivo CEPEA;
9. arquivo de vendas;
10. índices setoriais;
11. potencial regional;
12. scores;
13. recomendações;
14. alertas ativos;
15. relatório executivo;
16. check final.

## Rodar estrutura

```bash
python scripts\apply_etapa16.py
```

## Rodar pipeline padrão

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos
```

## Rodar com Comex Stat

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos --comex --comex-delay 30
```

## Rodar com arquivos reais

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos --conab-file "data\input\conab_precos_milho_soja.xlsx" --cepea-file "data\input\cepea_tilapia.xlsx"
```

## Rodar com vendas reais

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos --vendas-file "data\input\vendas.xlsx"
```

## Rodar tudo, incluindo init_db

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos --init-db
```

## Não gerar relatório

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos --sem-relatorio
```

## Continuar mesmo se uma etapa obrigatória falhar

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos --continuar-no-erro
```

## Observação

Por padrão, o pipeline não roda Comex, IBGE e arquivos externos para evitar demora, rate limit ou erro por arquivo inexistente.

Ative essas cargas somente quando quiser atualizar essas fontes.


# Hotfix 16.1 — Encoding UTF-8 no Pipeline

## Problema

No Windows, o pipeline executava scripts filhos com encoding `cp1252`.
Quando um script imprimia emoji, por exemplo `✅`, ocorria:

```text
UnicodeEncodeError: 'charmap' codec can't encode character
```

## Correção

O `src/services/pipeline_service.py` agora executa subprocessos com:

```text
PYTHONUTF8=1
PYTHONIOENCODING=utf-8
encoding="utf-8"
errors="replace"
```

Também foi adicionado:

```text
scripts/run_pipeline_utf8.bat
```

## Rodar normalmente

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos
```

## Alternativa pelo BAT

```bash
scripts\run_pipeline_utf8.bat
```

## Alternativa manual no CMD

```bash
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
python scripts\run_pipeline_full.py --uf MG --usuario Marcos
```
