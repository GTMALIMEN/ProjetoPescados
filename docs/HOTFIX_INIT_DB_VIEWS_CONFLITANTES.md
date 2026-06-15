
# Hotfix — init_db views conflitantes

## Problema

O `init_db.py` falhou na etapa `setorial.sql` com:

```text
psycopg.errors.InvalidTableDefinition:
não é possível alterar o nome da coluna "uf" da visão para "fonte"
```

Isso acontece quando já existe uma view antiga com o mesmo nome, mas a nova definição tem outra ordem/nome de colunas.

## Correção

Foi criado:

```text
src/database/preflight_drop_conflicting_views.sql
scripts/preflight_drop_conflicting_views.py
```

E o `scripts/init_db.py` agora executa esse preflight antes de aplicar os arquivos SQL.

## Views tratadas

```text
app.vw_indicador_setorial_mensal
app.vw_saude_setorial
app.vw_etl_ultimas_execucoes
app.vw_etl_resumo_fonte_historico
app.vw_etl_controle_carga
app.vw_etl_status_atual
app.vw_etl_resumo_fonte
app.vw_etl_erros_ativos
app.vw_data_quality_resumo
app.vw_saude_sistema
app.vw_diagnostico_v2_plano
app.vw_ceagesp_pescados_historico
```

## Como rodar

```bat
scripts\rodar_tudo_etapa23.bat
```

Ou manualmente:

```bat
.\.venv\Scripts\python.exe scripts\preflight_drop_conflicting_views.py
.\.venv\Scripts\python.exe scripts\init_db.py
```
