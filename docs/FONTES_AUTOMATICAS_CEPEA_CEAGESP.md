# Fontes automáticas — CEPEA e CEAGESP

## CEPEA oficial

Use:

```powershell
python scripts\run_cepea_oficial.py --renomear-manual-antigo
```

O script coleta a página pública do CEPEA de tilápia:

- produto: Tilápia;
- indicador: `preco_tilapia_cepea_produtor_independente`;
- unidade: R$/kg;
- periodicidade: semanal;
- regiões: conforme tabela CEPEA;
- conceito: preço à vista pago ao produtor independente.

O script grava:

- detalhe bruto auditável em `raw.cepea_tilapia_payload`;
- série analítica em `dw.fato_indicador_setorial` com `fonte = 'CEPEA'` e `subcategoria` iniciando com `oficial_`.

A opção `--renomear-manual-antigo` preserva registros antigos, mas troca planilhas/proxies que estavam como `CEPEA` para `CEPEA_MANUAL_IMPORTADO`. Isso evita misturar valores manuais, camarão ou preços mensais com o indicador CEPEA oficial.

## CEAGESP oficial

Primeira tentativa, sem navegador:

```powershell
python scripts\run_ceagesp_automatico.py --dias-busca 21
```

Fallback, usando navegador headless:

```powershell
python scripts\run_ceagesp_playwright.py --dias-busca 60 --max-datas 12
```

Se o Playwright ainda não estiver instalado:

```powershell
python -m pip install playwright
python -m playwright install chromium
```

A CEAGESP divulga preço de venda no atacado do Entreposto da Capital. As colunas Menor, Comum e Maior são preços em reais, e o preço comum é o valor mais praticado.

## Validação

Depois das cargas:

```powershell
python scripts\validar_cepea_ceagesp_fontes.py
python scripts\validar_dados_completo.py
```

A tela do app agora filtra CEPEA oficial por:

```sql
fonte = 'CEPEA'
AND subcategoria ILIKE 'oficial_%'
```

Assim, `CEPEA_MANUAL_IMPORTADO` não aparece como CEPEA oficial.
