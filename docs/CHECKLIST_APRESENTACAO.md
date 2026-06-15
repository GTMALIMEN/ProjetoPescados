# Checklist de Apresentação

## Antes de apresentar

- [ ] Rodar pipeline completo
- [ ] Confirmar `check_db.py` sem erros
- [ ] Rodar testes automatizados
- [ ] Gerar relatório executivo
- [ ] Abrir Streamlit
- [ ] Conferir abas principais
- [ ] Tirar prints
- [ ] Atualizar README
- [ ] Fazer commit no Git

## Comandos

```bash
python scripts\run_pipeline_full.py --uf MG --usuario Marcos
python scripts\check_db.py
python scripts\run_tests.py
streamlit run app.py
```

## Abas para demonstrar

- [ ] Radar Econômico
- [ ] Geografia IBGE
- [ ] Potencial Regional
- [ ] Proteínas e Grãos
- [ ] Fontes Reais
- [ ] What-if
- [ ] Alertas Ativos
- [ ] Relatório Executivo
- [ ] Pipeline

## Explicação em 1 minuto

Este projeto é um sistema de inteligência comercial para pescados. Ele integra dados internos de vendas com indicadores econômicos, geográficos e setoriais, calcula potencial e risco por região, gera recomendações, simula cenários, emite alertas e gera relatório executivo automático.

## Explicação técnica

- Dados coletados via API e arquivos.
- PostgreSQL organizado em raw, staging, dw e app.
- ETL em Python.
- Scores e recomendações com regras explicáveis.
- Streamlit para visualização.
- Pipeline mestre para orquestração.
- Relatório executivo exportável.

## Pontos fortes

- Projeto ponta a ponta.
- Problema real de negócio.
- Dados públicos e internos.
- Explicabilidade.
- Automação.
- Simulação.
- Alertas.
- Relatório executivo.

## Pontos a mencionar como evolução

- Deploy.
- Docker.
- Autenticação.
- Testes.
- Scheduler.
- Modelos de ML.
