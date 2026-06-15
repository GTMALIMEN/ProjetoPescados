@echo off
cd /d "%~dp0\.."
call .venv\Scripts\activate

echo Instalando dependencias para leitura de HTML/CEAGESP...
python -m pip install lxml==5.3.0 html5lib==1.1

echo.
echo Dependencias CEAGESP instaladas.
pause
