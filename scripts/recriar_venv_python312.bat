@echo off
cd /d "%~dp0\.."

echo ============================================
echo Recriar .venv com Python 3.12
echo ============================================

py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python 3.12 nao encontrado.
    echo Instale Python 3.12 e rode novamente.
    pause
    exit /b 1
)

if exist .venv (
    echo Removendo .venv antiga...
    rmdir /s /q .venv
)

echo Criando .venv com Python 3.12...
py -3.12 -m venv .venv

call .venv\Scripts\activate
python --version

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

python scripts\validate_project.py

echo.
echo .venv recriada com Python 3.12.
pause
