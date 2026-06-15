# Deploy — Streamlit Cloud + Supabase

## Resumo

```text
GitHub → código
Streamlit Cloud → app online
Supabase → PostgreSQL online
Streamlit Secrets → DATABASE_URL
```

## DATABASE_URL recomendada

Use Session Pooler no Supabase:

```text
postgresql+psycopg://postgres.PROJECT_REF:SUA_SENHA@aws-0-REGIAO.pooler.supabase.com:5432/postgres?sslmode=require
```

## Testar localmente

```powershell
$env:DATABASE_URL="postgresql+psycopg://postgres.PROJECT_REF:SUA_SENHA@aws-0-REGIAO.pooler.supabase.com:5432/postgres?sslmode=require"
.\.venv\Scripts\python.exe scripts\testar_conexao.py
```

## Criar estrutura no Supabase

```powershell
.\.venv\Scripts\python.exe scripts\init_db.py
.\.venv\Scripts\python.exe scripts\apply_fontes_automaticas.py
.\.venv\Scripts\python.exe scripts\apply_hotfix_expansao_receita_cepea.py
```

## Streamlit Secrets

```toml
DATABASE_URL = "postgresql+psycopg://postgres.PROJECT_REF:SUA_SENHA@aws-0-REGIAO.pooler.supabase.com:5432/postgres?sslmode=require"
```
