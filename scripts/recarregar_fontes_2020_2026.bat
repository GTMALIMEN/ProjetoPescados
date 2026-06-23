@echo off
cd /d "%~dp0\.."
call .venv\Scripts\activate

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo ============================================
echo Radar Pescados IA - Recarregar fontes 2020-2026
echo ============================================

echo Aplicando regioes comerciais MG...
python scripts\apply_regioes_mg.py

echo Carregando Banco Central...
python scripts\run_bcb_load.py

echo Carregando IBGE localidades e populacao...
python scripts\run_ibge_localidades.py
python scripts\apply_regioes_mg.py
python scripts\run_ibge_populacao.py

echo Carregando Comex Stat 2020-2026...
python scripts\run_comex_pescados.py --ano-inicio 2020 --ano-fim 2026 --delay 60

echo Carregando proteinas 2020-2026...
REM CEPEA antigo removido: use Importacoes Manuais CEPEA Manual

echo Carregando graos e insumos 2020-2026...
python scripts\load_conab_file.py --arquivo "data\input\conab_precos_milho_soja.xlsx" --categoria graos_racao --produto-default Milho --uf-default MG

echo Recalculando tudo...
python scripts\calculate_indices_setoriais.py --uf MG --salvar
python scripts\calculate_potencial.py --uf MG --salvar
python scripts\apply_etapa9.py
python scripts\apply_etapa12.py
python scripts\calculate_scores.py --uf MG --salvar
python scripts\generate_recommendations.py --uf MG --salvar
python scripts\generate_active_alerts.py --uf MG --salvar
python scripts\generate_executive_report.py --uf MG --usuario Marcos

echo Check final...
python scripts\check_db.py

echo.
echo Finalizado. Para abrir o app:
echo streamlit run app.py
pause
