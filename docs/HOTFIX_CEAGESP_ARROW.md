# Hotfix CEAGESP + Arrow

## Corrigido

1. CEAGESP quebrava por falta de `lxml`.
2. `pandas.read_html` gerava FutureWarning por receber HTML literal.
3. Streamlit/Arrow gerava warning na coluna `variacao_mensal_pct`.

## Novas dependências

```text
lxml==5.3.0
html5lib==1.1
```

## Rodar no ambiente atual

```bat
pip install -r requirements.txt
```

Ou apenas:

```bat
scripts\instalar_dependencias_ceagesp.bat
```

## Depois testar

```bat
python scripts\run_ceagesp_pescados.py
python scripts\diagnosticar_v2_plano.py
streamlit run app.py
```
