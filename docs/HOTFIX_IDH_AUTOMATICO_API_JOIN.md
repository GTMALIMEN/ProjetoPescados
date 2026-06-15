
# Hotfix IDH automático — API + join por município/UF

## Problema

O coletor anterior falhava quando:

- a página do PNUD retornava 403;
- o dados.gov.br exigia JavaScript e não trazia tabelas HTML;
- a tabela pública do PNUD não trazia código IBGE, apenas `Município (UF)`.

## Correção

O novo coletor:

1. Tenta a página PNUD com headers de navegador.
2. Tenta a API pública do dados.gov.br para descobrir recursos do Atlas Brasil.
3. Lê HTML, CSV, XLSX, XLS e ZIP.
4. Aceita tabela sem código IBGE.
5. Faz vínculo com `dw.dim_geografia` por:
   - `codigo_ibge`, quando existir;
   - `municipio + uf`, quando não existir.

## Rodar

```bat
python scripts\apply_fontes_automaticas.py
python scripts\run_idh_automatico.py
python scripts\diagnosticar_v2_plano.py
```

## Fallback controlado

Se o portal mudar de novo, rode com URL direta:

```bat
python scripts\run_idh_automatico.py --url "URL_DO_ARQUIVO_CSV_XLSX_ZIP"
```
