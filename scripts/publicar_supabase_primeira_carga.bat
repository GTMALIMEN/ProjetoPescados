@echo off
cd /d "%~dp0\.."

echo ============================================================
echo Publicar/Carregar banco Supabase - Radar Pescados IA
echo ============================================================
echo.
echo Antes de rodar, configure DATABASE_URL nesta janela:
echo set "DATABASE_URL=postgresql+psycopg://postgres.PROJECT_REF:SENHA@aws-0-REGIAO.pooler.supabase.com:5432/postgres?sslmode=require"
echo.
pause

call .venv\Scripts\activate.bat

echo Testando conexao...
.\.venv\Scripts\python.exe scripts\test_supabase_connection.py
if errorlevel 1 goto erro

echo Inicializando banco...
.\.venv\Scripts\python.exe scripts\init_db.py
if errorlevel 1 goto erro

echo Aplicando fontes automaticas...
.\.venv\Scripts\python.exe scripts\apply_fontes_automaticas.py

echo Aplicando hotfix expansao/receita/cepea...
.\.venv\Scripts\python.exe scripts\apply_hotfix_expansao_receita_cepea.py

echo Diagnostico...
.\.venv\Scripts\python.exe scripts\diagnosticar_v2_plano.py

echo.
echo ✅ Estrutura aplicada no Supabase.
goto fim

:erro
echo.
echo ❌ Erro na carga do Supabase. Verifique DATABASE_URL, senha e pooler.
:fim
pause
