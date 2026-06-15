@echo off
cd /d "%~dp0\.."

echo Limpando cache de mapas...
if exist data\geojson\brasil_ufs_ibge.geojson del /f /q data\geojson\brasil_ufs_ibge.geojson
if exist data\geojson\mg_municipios_ibge.geojson del /f /q data\geojson\mg_municipios_ibge.geojson

echo Baixando novamente as malhas do IBGE...
call .venv\Scripts\activate
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
python scripts\baixar_malhas_ibge.py --force

echo.
echo Cache de mapas atualizado.
pause
