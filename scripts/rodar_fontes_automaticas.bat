@echo off
REM ============================================================
REM Fontes automáticas — SEM CEPEA/CEAGESP
REM ============================================================
REM CEPEA e CEAGESP agora são 100%% manuais/controlados pelo app.
REM Use a aba "Importações Manuais" e o modo "Limpar base antiga e carregar somente este arquivo".
REM Este script não executa scraper, proxy ou Playwright para CEPEA/CEAGESP.

python scripts\apply_fontes_automaticas.py
python scripts\run_idh_automatico.py
python scripts\run_bcb_load.py

echo.
echo CEPEA/CEAGESP automatico desativado. Use importacao manual no app.
