@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0\.."

echo ============================================================
echo Radar Pescados IA - Rodar tudo Etapa 23
echo ============================================================
echo Pasta: %CD%
echo.

set PY=.venv\Scripts\python.exe

if not exist "%PY%" goto RECRIAR_VENV
"%PY%" --version >nul 2>&1
if errorlevel 1 goto RECRIAR_VENV
goto VENV_OK

:RECRIAR_VENV
echo [VENV] Ambiente .venv ausente ou quebrado. Recriando com Python 3.12...
if exist ".venv" rmdir /s /q ".venv"
py -3.12 -m venv .venv
if errorlevel 1 (
    echo.
    echo ERRO: Python 3.12 nao encontrado. Instale com:
    echo winget install -e --id Python.Python.3.12
    exit /b 1
)

:VENV_OK
call .venv\Scripts\activate.bat
"%PY%" --version

echo.
echo [1/16] Atualizando pip/setuptools/wheel...
"%PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto ERRO

echo.
echo [2/16] Instalando requirements...
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 goto ERRO

echo.
echo [3/16] Validando estrutura da Etapa 23...
"%PY%" scripts\validar_etapa23_integridade.py
if errorlevel 1 goto ERRO

echo.
echo [4/17] Aplicando preflight de views antigas...
"%PY%" scripts\preflight_drop_conflicting_views.py
if errorlevel 1 goto ERRO

echo.
echo [5/17] Inicializando banco completo...
"%PY%" scripts\init_db.py
if errorlevel 1 goto ERRO

echo.
echo [6/17] Aplicando estruturas V2/fontes automaticas...
"%PY%" scripts\apply_fontes_automaticas.py
if errorlevel 1 goto ERRO

echo.
echo [7/17] Aplicando CEAGESP manual/controlado...
"%PY%" scripts\apply_ceagesp_manual.py
if errorlevel 1 goto ERRO

echo.
echo [8/17] Aplicando Expansao V2 publica...
"%PY%" scripts\apply_expansao_v2_publica.py
if errorlevel 1 goto ERRO

echo.
echo [9/17] Aplicando regioes comerciais MG...
"%PY%" scripts\apply_regioes_mg.py
if errorlevel 1 goto ERRO

echo.
echo [10/17] Carregando IBGE Localidades...
"%PY%" scripts\run_ibge_localidades.py
if errorlevel 1 goto ERRO

echo.
echo [11/17] Carregando IBGE Populacao...
"%PY%" scripts\run_ibge_populacao.py
if errorlevel 1 goto ERRO

echo.
echo [12/17] Carregando dados publicos da expansao Sudeste...
"%PY%" scripts\run_expansao_publica.py --estados MG,SP,RJ,ES
if errorlevel 1 goto ERRO

echo.
echo [13/17] Carregando IDH/IDHM automatico...
"%PY%" scripts\run_idh_automatico.py
if errorlevel 1 (
    echo AVISO: IDH automatico falhou. Continuando para fallback dos faltantes.
)

echo.
echo [14/17] Preenchendo IDH faltantes via fallback IBGE/PNUD...
"%PY%" scripts\preencher_idh_faltantes_ibge.py
if errorlevel 1 (
    echo AVISO: fallback IDH encontrou problema. Verifique depois no diagnostico.
)

echo.
echo [15/17] Criando template CEAGESP manual...
"%PY%" scripts\criar_template_ceagesp_manual.py
if errorlevel 1 goto ERRO

echo.
echo [16/17] Carregando arquivos manuais se existirem...
if exist "data\input\ceagesp_manual.csv" (
    echo Encontrado data\input\ceagesp_manual.csv
    echo ATENCAO: se for apenas template de exemplo, edite antes de usar em producao.
    "%PY%" scripts\load_ceagesp_manual_file.py --arquivo "data\input\ceagesp_manual.csv"
) else (
    echo PULADO: data\input\ceagesp_manual.csv nao encontrado.
)

if exist "data\input\base_compra_manual.csv" (
    "%PY%" scripts\load_compra_manual_file.py --arquivo "data\input\base_compra_manual.csv"
) else (
    echo PULADO: base_compra_manual.csv nao encontrado.
)

if exist "data\input\previa_vendedores.csv" (
    "%PY%" scripts\load_previa_vendedores_file.py --arquivo "data\input\previa_vendedores.csv"
) else (
    echo PULADO: previa_vendedores.csv nao encontrado.
)

if exist "data\input\cepea_tilapia.xlsx" (
    "%PY%" scripts\load_cepea_file.py --arquivo "data\input\cepea_tilapia.xlsx" --categoria proteina --produto-default Tilápia --uf-default MG
) else (
    echo PULADO: cepea_tilapia.xlsx nao encontrado.
)

if exist "data\input\conab_precos_milho_soja.xlsx" (
    "%PY%" scripts\load_conab_file.py --arquivo "data\input\conab_precos_milho_soja.xlsx" --categoria graos_racao --produto-default Milho --uf-default MG
) else (
    echo PULADO: conab_precos_milho_soja.xlsx nao encontrado.
)

echo.
echo [17/17] Diagnostico final...
"%PY%" scripts\diagnosticar_v2_plano.py
if errorlevel 1 goto ERRO

echo.
echo ============================================================
echo Tudo executado. Abrindo Streamlit...
echo ============================================================
"%PY%" -m streamlit run app.py
exit /b 0

:ERRO
echo.
echo ============================================================
echo ERRO durante a execucao.
echo Copie o erro acima e me envie.
echo ============================================================
exit /b 1
