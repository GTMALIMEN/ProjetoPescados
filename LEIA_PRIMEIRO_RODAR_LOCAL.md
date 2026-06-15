# LEIA PRIMEIRO — Rodar Radar Pescados IA

Este pacote foi limpo para rodar em outro computador.

## O que foi removido

```text
.venv/
.env
__pycache__/
.pytest_cache/
arquivos .pyc/.log
```

A `.venv` antiga não deve ser reaproveitada porque ela guarda caminhos do computador anterior.

---

# Rodar localmente

## 1. Instalar Python 3.12

No PowerShell:

```powershell
winget install -e --id Python.Python.3.12
```

Feche e abra o PowerShell, depois teste:

```powershell
py -3.12 --version
```

---

## 2. Recriar ambiente

Na pasta do projeto:

```powershell
cd "C:\Caminho\Para\Pescados"
scripts\00_RECRIAR_VENV_E_INSTALAR.bat
```

---

## 3. Criar .env local

```powershell
scripts\01_CRIAR_ENV_LOCAL.bat
```

Ajuste a senha do PostgreSQL local.

Exemplo:

```text
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=radar_pescados_ia
DB_USER=postgres
DB_PASSWORD=12345
```

---

## 4. Testar conexão

```powershell
scripts\02_TESTAR_CONEXAO_LOCAL.bat
```

---

## 5. Rodar app

```powershell
scripts\04_RODAR_APP_LOCAL.bat
```

Ou manualmente:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

---

# Publicar com Supabase

## 1. Criar projeto Supabase

Use a connection string do **Session Pooler**.

Formato recomendado:

```text
postgresql+psycopg://postgres.PROJECT_REF:SUA_SENHA@aws-0-REGIAO.pooler.supabase.com:5432/postgres?sslmode=require
```

## 2. Testar e criar estrutura

```powershell
scripts\05_SUPABASE_TESTAR_E_CRIAR_ESTRUTURA.bat
```

---

# Subir para GitHub / Streamlit Cloud

No GitHub, não envie:

```text
.env
.venv/
.streamlit/secrets.toml
*.dump
```

No Streamlit Cloud, coloque em Secrets:

```toml
DATABASE_URL = "postgresql+psycopg://postgres.PROJECT_REF:SUA_SENHA@aws-0-REGIAO.pooler.supabase.com:5432/postgres?sslmode=require"
```

Arquivo principal:

```text
app.py
```

Python:

```text
3.12
```
