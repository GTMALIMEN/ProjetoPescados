@echo off
cd /d "%~dp0\.."

echo ============================================
echo Radar Pescados IA - Setup Notebook
echo ============================================

if not exist .venv (
    echo Criando ambiente virtual...
    py -3 -m venv .venv
)

call .venv\Scripts\activate

echo Atualizando pip...
python -m pip install --upgrade pip

echo Instalando dependencias...
pip install -r requirements.txt

echo Validando estrutura...
python scripts\validate_project.py

echo.
echo Setup Python concluido.
echo Agora instale/configure o PostgreSQL e depois rode:
echo python scripts\create_database.py
echo python scripts\init_db.py
echo.
pause
