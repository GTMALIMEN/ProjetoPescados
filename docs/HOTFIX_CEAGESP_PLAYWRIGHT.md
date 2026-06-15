
# Hotfix CEAGESP — Playwright

## Por que

O coletor com `requests` detectou o formulário oficial:

```text
cot_grupo
cot_data
```

mas a página não retornou a tabela em requisições simples. A consulta oficial depende do comportamento da página no navegador.

## Solução

Foi criado um coletor via Playwright/headless browser:

```bat
python scripts\run_ceagesp_playwright.py --dias-busca 60 --max-datas 12
```

## Instalação

```bat
scripts\instalar_playwright_ceagesp.bat
```

Ou manual:

```bat
python -m pip install playwright==1.49.1
python -m playwright install chromium
```

## Depuração visual

```bat
python scripts\run_ceagesp_playwright.py --dias-busca 60 --max-datas 5 --visivel
```

## Fluxo recomendado

```bat
python scripts\run_ceagesp_playwright.py --dias-busca 60 --max-datas 12
python scripts\diagnosticar_v2_plano.py
```
