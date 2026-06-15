@echo off
cd /d "%~dp0\.."
call .venv\Scripts\activate.bat
.\.venv\Scripts\python.exe scripts\apply_etapas24_28.py
.\.venv\Scripts\python.exe scripts\run_comex_refinado.py --ano-inicio 2020 --ano-fim 2026 --delay 12 --max-tentativas 2
.\.venv\Scripts\python.exe scripts\diagnosticar_v2_plano.py
pause
