@echo off
cd /d "%~dp0\.."
call .venv\Scripts\activate
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo Exemplos de uso dos importadores manuais:
echo.
echo python scripts\load_ceagesp_manual_file.py --arquivo "data\input\ceagesp_manual.csv"
echo python scripts\load_compra_manual_file.py --arquivo "data\input\base_compra.csv"
echo python scripts\load_previa_vendedores_file.py --arquivo "data\input\previa_vendedores.csv"
echo python scripts\load_idh_file.py --arquivo "data\input\idh_municipal.csv"
echo.
pause
