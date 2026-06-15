# Decisões Técnicas

## 1. PostgreSQL como base central

Foi escolhido PostgreSQL porque permite:

- schemas separados;
- integridade relacional;
- índices;
- materialized views;
- JSONB;
- auditoria;
- evolução futura para TimescaleDB.

## 2. Streamlit como camada de apresentação

Streamlit foi escolhido por:

- velocidade de desenvolvimento;
- facilidade para dashboards;
- boa integração com Pandas;
- uso local e corporativo simples.

## 3. Separação por schemas

```text
raw       → dados brutos
staging   → transição
dw        → modelo analítico
app       → aplicação e decisão
ml        → evolução futura
```

## 4. Uso de materialized views

Materialized views foram usadas para:

- score atual;
- recomendação atual;
- potencial atual;
- alertas atuais;
- índices setoriais atuais.

Isso simplifica o consumo no app.

## 5. JSONB em fatores explicativos

Campos como `principais_fatores` usam JSONB para permitir:

- explicabilidade;
- flexibilidade;
- evolução sem quebrar schema;
- renderização futura em UI.

## 6. Pipeline por subprocesso

O pipeline executa scripts existentes para:

- reaproveitar etapas;
- facilitar debug;
- manter cada etapa isolada;
- registrar stdout/stderr.

## 7. Cuidado com previsões

O projeto evita afirmar certeza. Usa termos como:

- probabilidade;
- simulação;
- apoio à decisão;
- heurística;
- cenário.

## 8. Fontes reais por arquivo quando necessário

CONAB e CEPEA podem mudar layout e disponibilidade. Por isso foram implementados loaders flexíveis por arquivo.

## 9. Comex Stat com delay

A API pode retornar rate limit. O coletor possui retry e delay configurável.

## 10. Baixa confiança sem vendas reais

Quando há pouca venda interna, o sistema recomenda prudência:

```text
aguardar_dados_reais
dados_insuficientes
monitoramento
```
