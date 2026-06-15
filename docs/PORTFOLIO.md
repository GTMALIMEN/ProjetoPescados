# Portfólio — Radar Pescados IA

## Título sugerido

Radar Pescados IA — Sistema de Inteligência Comercial, Econômica e Setorial para tomada de decisão no mercado de pescados.

## Descrição curta

Projeto de análise de dados que integra vendas internas, indicadores econômicos, dados geográficos, fontes setoriais e comércio exterior para gerar scores, recomendações, simulações, alertas e relatórios executivos.

## Problema de negócio

Empresas de pescados precisam decidir onde vender mais, onde abrir mercado, quando ajustar preço, quando acionar marketing e como reagir a movimentos de dólar, custo de ração e concorrência entre proteínas.

## Solução

Um app em Streamlit com PostgreSQL que centraliza dados, calcula indicadores, cria scores regionais e transforma análises em recomendações práticas.

## Principais diferenciais

- Integração com Banco Central, IBGE e Comex Stat.
- Modelagem em PostgreSQL com DW.
- Indicadores setoriais de proteínas e grãos.
- Score regional com potencial e risco.
- Recomendações com motor de decisão.
- Simulador What-if.
- Alertas ativos por área responsável.
- Relatório executivo automático.
- Pipeline mestre com logs e rastreabilidade.

## Prints recomendados

Inclua prints das abas:

1. Radar Econômico
2. Potencial Regional
3. Proteínas e Grãos
4. Scores
5. Recomendações
6. What-if
7. Alertas Ativos
8. Relatório Executivo
9. Pipeline

## Como explicar em entrevista

> Desenvolvi um sistema analítico de ponta a ponta para apoiar decisões comerciais em uma empresa de pescados. O projeto integra dados internos e externos, organiza tudo em PostgreSQL, calcula scores regionais, identifica riscos e oportunidades, gera recomendações, permite simular cenários e cria relatórios executivos automáticos.

## Competências demonstradas

- Engenharia de dados
- Modelagem dimensional
- APIs
- ETL
- SQL
- Python
- PostgreSQL
- Streamlit
- Estatística aplicada
- Economia aplicada
- Data storytelling
- Produto de dados
- Automação
- Observabilidade

## Métricas para destacar

- 5.571 municípios carregados
- 853 municípios de MG regionalizados
- Séries históricas macroeconômicas desde 2000
- Integração com dados reais de Comex, CONAB e CEPEA
- Pipeline completo em comando único
- Relatório executivo automático

## Limitações assumidas

- Alguns dados setoriais ainda podem vir de arquivos exportados.
- As recomendações são probabilísticas.
- A qualidade da recomendação depende da base real de vendas.
- O modelo ainda pode evoluir para ML supervisionado com histórico maior.

## Próximas evoluções

- Autenticação
- Deploy
- Docker
- Testes automatizados
- Agendamento de pipeline
- Alertas por e-mail/WhatsApp
- Modelos preditivos
- Feature store
- Data quality formal
