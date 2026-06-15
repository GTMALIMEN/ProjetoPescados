@echo off
cd /d "%~dp0\.."
call .venv\Scripts\activate.bat

.\.venv\Scripts\python.exe scripts\validar_pronto_para_rodar.py
pause
