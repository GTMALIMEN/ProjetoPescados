@echo off
cd /d "%~dp0\.."
call .venv\Scripts\activate
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
streamlit run app.py
