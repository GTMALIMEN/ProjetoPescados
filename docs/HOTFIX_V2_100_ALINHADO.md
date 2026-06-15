
# Hotfix V2 — 100% alinhado ao plano

## Correções

- Corrigido erro de Geografia IBGE com `st.metric` recebendo Series.
- Corrigido erro da Saúde do Sistema com dict em vez de DataFrame.
- Corrigido erro do What-if com nomes incorretos do `WhatIfParams`.
- Corrigidos zeros falsos em PIB, IDH, renda e PDV.
- Campos sem fonte passam a aparecer como `N/A`/pendente.
- Receita por categoria mostra `Sem venda real no recorte` quando não há receita.
- CEAGESP corrigido para usar chave robusta `chave_registro`.
- SQL da CEAGESP corrigido para não usar `COALESCE` dentro de constraint UNIQUE.
- Abas do app mantidas exatamente conforme o plano V2.

## Abas finais

```text
📈 Radar Econômico
🗺️ Geografia IBGE
🧭 Região Comercial MG
🌎 Análise de Expansão
🥩 Proteínas e Grãos
🔌 Fontes Reais
📈 Análise Previsão de Mercado
🧪 What-if
🚨 Alertas Ativos
📄 Relatório Executivo
🩺 Saúde do Sistema
```

## Rodar depois de substituir arquivos

```bat
python scripts\init_db.py
python scripts\run_ibge_localidades.py
python scripts\run_ibge_populacao.py
python scripts\apply_expansao_v2_publica.py
python scripts\run_expansao_publica.py --estados MG,SP,RJ,ES
python scripts\run_ceagesp_pescados.py
python scripts\diagnosticar_v2_plano.py
python scripts\check_db.py
streamlit run app.py
```
