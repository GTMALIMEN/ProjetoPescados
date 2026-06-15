# Guia de Execução

## 1. Execução rápida

```bash
cd "C:\Users\ducar\OneDrive\Área de Trabalho\Pescados"
.venv\Scripts\activate
python scripts\run_pipeline_full.py --uf MG --usuario Marcos
streamlit run app.py
```

## 2. Execução inicial

```bash
python scripts\init_db.py
python scripts\run_bcb_load.py
python scripts\run_ibge_localidades.py
python scripts\calculate_potencial.py --uf MG --salvar
python scripts\calculate_indices_setoriais.py --uf MG --salvar
python scripts\calculate_scores.py --uf MG --salvar
python scripts\generate_recommendations.py --uf MG --salvar
python scripts\generate_active_alerts.py --uf MG --salvar
python scripts\generate_executive_report.py --uf MG --usuario Marcos
python scripts\check_db.py
streamlit run app.py
```

## 3. Atualização diária recomendada

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos
```

## 4. Atualizar fontes reais

### Comex Stat

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos --comex --comex-delay 30
```

### CONAB / CEPEA

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos --conab-file "data\input\conab_precos_milho_soja.xlsx" --cepea-file "data\input\cepea_tilapia.xlsx"
```

### Vendas reais

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos --vendas-file "data\input\vendas.xlsx"
```

## 5. Validação

```bash
python scripts\check_db.py
python scripts\validate_project.py
```

## 6. Relatório executivo

```bash
python scripts\generate_executive_report.py --uf MG --usuario Marcos
```

Arquivos gerados:

```text
outputs/relatorios/
```
