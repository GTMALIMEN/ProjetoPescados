@echo off
cd /d "%~dp0\.."
call .venv\Scripts\activate

echo ============================================
echo Radar Pescados IA - Primeiro uso notebook
echo ============================================

echo Criando banco se necessario...
python scripts\create_database.py

echo Inicializando schemas/tabelas...
python scripts\init_db.py

echo Carregando Banco Central...
python scripts\run_bcb_load.py

echo Carregando IBGE localidades...
python scripts\run_ibge_localidades.py

echo Carregando IBGE populacao...
python scripts\run_ibge_populacao.py

echo Aplicando regioes comerciais MG...
python scripts\apply_regioes_mg.py

echo Carregando vendas exemplo...
python scripts\load_vendas_file.py --arquivo "data\exemplo\vendas_exemplo.csv"

echo Carregando arquivos expandidos CONAB/CEPEA 2020-2026...
python scripts\load_conab_file.py --arquivo "data\input\conab_precos_milho_soja.xlsx" --categoria graos_racao --produto-default Milho --uf-default MG
REM CEPEA antigo removido: use Importacoes Manuais CEPEA Manual

echo Calculando indices, potencial, scores, recomendacoes e alertas...
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
