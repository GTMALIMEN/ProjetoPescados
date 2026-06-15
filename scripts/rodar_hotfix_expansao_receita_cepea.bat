@echo off
cd /d "%~dp0\.."
call .venv\Scripts\activate.bat

echo Aplicando estrutura receita manual expansao...
.\.venv\Scripts\python.exe scripts\apply_hotfix_expansao_receita_cepea.py

echo Criando template receita manual expansao...
.\.venv\Scripts\python.exe scripts\criar_template_receita_manual_expansao.py

echo Diagnostico...
.\.venv\Scripts\python.exe scripts\diagnosticar_v2_plano.py

echo Abrindo app...
.\.venv\Scripts\python.exe -m streamlit run app.py
pause
