@echo off
cd /d "%~dp0\.."
call .venv\Scripts\activate
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
python scripts\validate_project.py
python scripts\run_tests.py
python scripts\check_db.py
pause
