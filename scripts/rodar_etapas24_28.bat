@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0\.."

set PY=.venv\Scripts\python.exe

if not exist "%PY%" (
    echo ERRO: .venv nao encontrada. Rode primeiro scripts\rodar_tudo_etapa23.bat
    exit /b 1
)

call .venv\Scripts\activate.bat

echo ============================================================
echo Radar Pescados IA - Etapas 24 a 28
echo ============================================================

echo.
echo [1/8] Aplicando estruturas Etapas 24 a 28...
"%PY%" scripts\apply_etapas24_28.py
if errorlevel 1 goto ERRO

echo.
echo [2/8] Etapa 24 - Censo/Demografia/Renda proxy controlado...
"%PY%" scripts\run_censo_demografico_2022.py --estados MG,SP,RJ,ES
if errorlevel 1 goto ERRO

echo.
echo [3/8] Etapa 25 - PDV proxy...
"%PY%" scripts\run_pdv_proxy.py --estados MG,SP,RJ,ES
if errorlevel 1 goto ERRO

echo.
echo [4/8] Etapas 27/28 - Criando templates de compra e previa...
"%PY%" scripts\criar_templates_etapas27_28.py
if errorlevel 1 goto ERRO

echo.
echo [5/8] Carregando base de compra manual se existir...
if exist "data\input\base_compra_manual.csv" (
    "%PY%" scripts\load_compra_manual_file.py --arquivo "data\input\base_compra_manual.csv"
) else (
    echo PULADO: data\input\base_compra_manual.csv nao existe.
)

echo.
echo [6/8] Carregando previa vendedores se existir...
if exist "data\input\previa_vendedores.csv" (
    "%PY%" scripts\load_previa_vendedores_file.py --arquivo "data\input\previa_vendedores.csv"
) else (
    echo PULADO: data\input\previa_vendedores.csv nao existe.
)

echo.
echo [7/8] Etapa 26 - Comex Stat refinado.
echo Esta etapa pode demorar e pode bater limite 429. Se quiser pular agora, feche e rode depois manualmente.
"%PY%" scripts\run_comex_refinado.py --ano-inicio 2020 --ano-fim 2026 --delay 12 --max-tentativas 2
if errorlevel 1 (
    echo AVISO: Comex refinado teve falhas. O pipeline continua; veja logs em Fontes Reais.
)

echo.
echo [8/8] Diagnostico final...
"%PY%" scripts\diagnosticar_v2_plano.py
if errorlevel 1 goto ERRO

echo.
echo ============================================================
echo Etapas 24 a 28 executadas. Abrindo app...
echo ============================================================
"%PY%" -m streamlit run app.py
exit /b 0

:ERRO
echo.
echo ERRO durante as Etapas 24 a 28. Copie o erro acima e envie.
exit /b 1
