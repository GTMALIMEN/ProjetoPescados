# Testes Automatizados

## Objetivo

A Etapa 18 adiciona testes automatizados para evitar que alterações futuras quebrem o projeto.

## Ferramenta

```text
pytest
```

## Instalação

```bash
pip install -r requirements.txt
```

## Rodar todos os testes

```bash
python scripts\run_tests.py
```

ou:

```bash
python -m pytest -q
```

## Rodar testes sem banco

```bash
python scripts\run_tests_no_db.py
```

## Rodar apenas testes de banco

```bash
python -m pytest -q -m db
```

## Testes criados

```text
tests/test_project_structure.py
tests/test_math_rules.py
tests/test_whatif_rules.py
tests/test_config_files.py
tests/test_database_connection.py
tests/test_database_tables.py
tests/test_database_views.py
tests/test_score_weights.py
tests/test_pipeline_metadata.py
```

## O que os testes validam

- estrutura de pastas;
- arquivos obrigatórios;
- README;
- configuração de NCM;
- funções matemáticas;
- regras do What-if;
- conexão com PostgreSQL;
- schemas principais;
- tabelas principais;
- views principais;
- pesos dos scores;
- tabelas e views do pipeline.

## Observação

Os testes de banco exigem:

- PostgreSQL rodando;
- `.env` configurado;
- banco inicializado com `python scripts/init_db.py`.

Se quiser validar apenas estrutura e lógica sem banco, use:

```bash
python scripts\run_tests_no_db.py
```
