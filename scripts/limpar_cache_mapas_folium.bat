@echo off
cd /d "%~dp0\.."
call .venv\Scripts\activate
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo Limpando cache antigo de mapas...
if exist data\geojson (
    del /f /q data\geojson\*.geojson
) else (
    mkdir data\geojson
)

echo Baixando mapas com Folium/Leaflet...
python scripts\baixar_malhas_ibge.py --force

echo Diagnostico...
python scripts\diagnosticar_mapas.py

echo.
echo Agora rode: streamlit run app.py
pause
