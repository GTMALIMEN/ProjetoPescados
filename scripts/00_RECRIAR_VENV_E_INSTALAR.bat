@echo off
cd /d "%~dp0\.."

echo ============================================================
echo Radar Pescados IA - Recriar .venv com Python 3.12
echo ============================================================

py -3.12 --version
if errorlevel 1 (
    echo.
    echo ERRO: Python 3.12 nao encontrado.
    echo Instale com:
    echo winget install -e --id Python.Python.3.12
    pause
    exit /b 1
)

if exist .venv (
    echo Removendo .venv antiga/quebrada...
    rmdir /s /q .venv
)

echo Criando .venv...
py -3.12 -m venv .venv
if errorlevel 1 goto erro

call .venv\Scripts\activate.bat

echo Atualizando pip/setuptools/wheel...
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto erro

echo Instalando requirements...
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto erro

echo Validando imports principais...
.\.venv\Scripts\python.exe -c "import streamlit, pandas, psycopg, sqlalchemy, plotly, dotenv; print('IMPORTS OK')"
if errorlevel 1 goto erro

echo.
echo ✅ Ambiente Python pronto.
pause
exit /b 0

:erro
echo.
echo ❌ Erro ao preparar ambiente.
pause
exit /b 1
