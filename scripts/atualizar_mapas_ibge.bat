@echo off
cd /d "%~dp0\.."
call .venv\Scripts\activate

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo Limpando cache antigo...
if exist data\geojson\brasil_ufs_ibge.geojson del /f /q data\geojson\brasil_ufs_ibge.geojson
if exist data\geojson\mg_municipios_ibge.geojson del /f /q data\geojson\mg_municipios_ibge.geojson

echo Baixando malhas reais do IBGE...
python scripts\baixar_malhas_ibge.py --force

echo Aplicando regiões comerciais MG...
python scripts\apply_regioes_mg.py

echo Diagnóstico dos mapas...
python scripts\diagnosticar_mapas.py

echo.
echo Finalizado. Agora rode:
echo streamlit run app.py
pause
