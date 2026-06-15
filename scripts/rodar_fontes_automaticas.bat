@echo off
cd /d "%~dp0\.."
call .venv\Scripts\activate
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
python scripts\apply_fontes_automaticas.py
python scripts\run_idh_automatico.py
python scripts\run_ceagesp_automatico.py --dias-busca 21
python scripts\diagnosticar_v2_plano.py
pause
