@echo off
cd /d "%~dp0\.."
call .venv\Scripts\activate.bat

echo Cole a DATABASE_URL do Supabase.
echo Exemplo:
echo postgresql+psycopg://postgres.PROJECT_REF:SENHA@aws-0-REGIAO.pooler.supabase.com:5432/postgres?sslmode=require
echo.
set /p DATABASE_URL=DATABASE_URL: 

echo.
echo Testando Supabase...
.\.venv\Scripts\python.exe scripts\testar_conexao.py
if errorlevel 1 goto erro

echo.
echo Criando estrutura principal...
.\.venv\Scripts\python.exe scripts\init_db.py
if errorlevel 1 goto erro

if exist scripts\apply_fontes_automaticas.py (
    .\.venv\Scripts\python.exe scripts\apply_fontes_automaticas.py
)

if exist scripts\apply_hotfix_expansao_receita_cepea.py (
    .\.venv\Scripts\python.exe scripts\apply_hotfix_expansao_receita_cepea.py
)

if exist scripts\diagnosticar_v2_plano.py (
    .\.venv\Scripts\python.exe scripts\diagnosticar_v2_plano.py
)

echo.
echo ✅ Supabase testado e estrutura aplicada.
pause
exit /b 0

:erro
echo.
echo ❌ Erro no Supabase. Verifique URL, senha, sslmode=require e pooler.
pause
exit /b 1
