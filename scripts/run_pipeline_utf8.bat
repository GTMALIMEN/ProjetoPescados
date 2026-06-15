@echo off
REM Executa o pipeline com UTF-8 no Windows.
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
python scripts\run_pipeline_full.py --uf MG --usuario Marcos
