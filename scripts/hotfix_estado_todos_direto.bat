@echo off
cd /d "%~dp0\.."
call .venv\Scripts\activate.bat
.\.venv\Scripts\python.exe scripts\hotfix_estado_todos_direto.py
pause
