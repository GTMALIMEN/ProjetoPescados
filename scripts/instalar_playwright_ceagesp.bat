@echo off
cd /d "%~dp0\.."
call .venv\Scripts\activate

echo Instalando Playwright para coleta CEAGESP via navegador...
python -m pip install playwright==1.49.1
python -m playwright install chromium

echo.
echo Playwright CEAGESP instalado.
pause
