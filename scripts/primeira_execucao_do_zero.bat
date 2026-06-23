@echo off
cd /d "%~dp0\.."
call .venv\Scripts\activate

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo ============================================
echo Radar Pescados IA V2 - Primeira execucao
echo ============================================

python scripts\create_database.py
python scripts\init_db.py

python scripts\run_bcb_load.py
python scripts\run_ibge_localidades.py

if exist scripts\apply_regioes_mg.py (
    python scripts\apply_regioes_mg.py
)

python scripts\run_ibge_populacao.py

python scripts\apply_expansao_v2_publica.py
python scripts\run_expansao_publica.py --estados MG,SP,RJ,ES

if exist data\exemplo\vendas_exemplo.csv (
    python scripts\load_vendas_file.py --arquivo "data\exemplo\vendas_exemplo.csv"
)

if exist data\input\cepea_tilapia.xlsx (
REM CEPEA antigo removido: use Importacoes Manuais CEPEA Manual
)

if exist data\input\conab_precos_milho_soja.xlsx (
    python scripts\load_conab_file.py --arquivo "data\input\conab_precos_milho_soja.xlsx" --categoria graos_racao --produto-default Milho --uf-default MG
)

python scripts\calculate_indices_setoriais.py --uf MG --salvar

if exist scripts\calculate_potencial.py (
    python scripts\calculate_potencial.py --uf MG --salvar
)

if exist scripts\apply_etapa9.py (
    python scripts\apply_etapa9.py
)

if exist scripts\apply_etapa12.py (
    python scripts\apply_etapa12.py
)

python scripts\calculate_scores.py --uf MG --salvar
python scripts\generate_recommendations.py --uf MG --salvar

if exist scripts\generate_active_alerts.py (
    python scripts\generate_active_alerts.py --uf MG --salvar
)

if exist scripts\generate_executive_report.py (
    python scripts\generate_executive_report.py --uf MG --usuario Marcos
)

REM CEAGESP automatico removido: use Importacoes Manuais CEAGESP Manual

python scripts\diagnosticar_v2_plano.py
python scripts\check_db.py

echo.
echo Finalizado. Para abrir:
echo scripts\abrir_app.bat
pause
