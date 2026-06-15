@echo off
cd /d "%~dp0\.."

echo ============================================
echo Radar Pescados IA V2 - Setup do zero
echo ============================================
echo.

echo Verificando Python instalado...
py -0p

echo.
echo IMPORTANTE:
echo Este projeto deve rodar com Python 3.12.
echo Nao use Python 3.14, pois pandas/streamlit podem tentar compilar dependencias.
echo.

py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python 3.12 nao encontrado.
    echo.
    echo Instale o Python 3.12 no Windows e marque "Add python.exe to PATH".
    echo Depois feche e abra o CMD novamente.
    echo.
    echo Para conferir as versoes instaladas:
    echo py -0p
    echo.
    pause
    exit /b 1
)

if not exist .env (
    call scripts\criar_env_local.bat
) else (
    if not exist .env.example (
        copy /Y .env .env.example >nul
        copy /Y .env env.example.txt >nul
    )
)

if exist .venv (
    echo.
    echo Ambiente .venv ja existe.
    echo Validando versao do Python da .venv...
    .venv\Scripts\python.exe -c "import sys; raise SystemExit(0 if sys.version_info[:2]==(3,12) else 1)" >nul 2>&1
    if errorlevel 1 (
        echo.
        echo A .venv atual nao usa Python 3.12.
        echo Removendo .venv antiga...
        rmdir /s /q .venv
    )
)

if not exist .venv (
    echo.
    echo Criando ambiente virtual com Python 3.12...
    py -3.12 -m venv .venv
)

call .venv\Scripts\activate

echo.
echo Versao Python da .venv:
python --version

echo.
echo Atualizando pip/setuptools/wheel...
python -m pip install --upgrade pip setuptools wheel

echo.
echo Instalando dependencias...
pip install -r requirements.txt

echo.
echo Validando estrutura do projeto...
python scripts\validate_project.py

echo.
echo Setup Python finalizado.
echo Agora rode:
echo scripts\primeira_execucao_do_zero.bat
echo.
pause
