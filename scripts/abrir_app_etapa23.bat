@echo off
cd /d "%~dp0\.."
call .venv\Scripts\activate.bat
.\.venv\Scripts\python.exe scripts\diagnosticar_v2_plano.py
.\.venv\Scripts\python.exe -m streamlit run app.py
pause
