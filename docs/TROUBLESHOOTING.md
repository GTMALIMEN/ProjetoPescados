# Troubleshooting

## Erro: ModuleNotFoundError: No module named 'src'

Execute sempre a partir da raiz do projeto:

```bash
cd "C:\Users\ducar\OneDrive\Área de Trabalho\Pescados"
python scripts\init_db.py
```

## Erro: senha falhou para usuário postgres

Verifique o `.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=PESCADOSTESTE
DB_USER=postgres
DB_PASSWORD=postgres
```

## Erro: relação não existe

Rode:

```bash
python scripts\init_db.py
```

ou a etapa específica:

```bash
python scripts\apply_etapa16.py
```

## Erro Comex 429

A API limitou requisições. Rode com delay maior:

```bash
python scripts\run_comex_pescados.py --ano-inicio 2024 --ano-fim 2026 --delay 30
```

## Erro UnicodeEncodeError no Windows

Use:

```bash
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
python scripts\run_pipeline_full.py --uf MG --usuario Marcos
```

ou:

```bash
scripts\run_pipeline_utf8.bat
```

## Pipeline aparece como INICIADO no check final

Isso ocorre porque o `check_db.py` roda antes do pipeline atualizar o próprio status final.

Rode depois:

```bash
python scripts\check_db.py
```

## Alertas demais de competitividade

Verifique:

- base setorial;
- pesos;
- score de competitividade;
- dados simulados vs reais.

## Recomendação fica aguardando dados reais

Isso é esperado quando a base de vendas é pequena.

Carregue vendas reais:

```bash
python scripts\load_vendas_file.py --arquivo "data\input\vendas.xlsx"
```

ou pelo pipeline:

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos --vendas-file "data\input\vendas.xlsx"
```

## Streamlit não abre

Rode:

```bash
streamlit run app.py
```

Verifique se o ambiente virtual está ativado.

## Relatório não baixa pelo app

Confirme se o arquivo foi gerado em:

```text
outputs/relatorios/
```
