# Modo manual controlado — CEPEA, CEAGESP e bases manuais

## Decisão

CEPEA e CEAGESP não usam mais proxy, scraper, Playwright ou coleta automática no app.

O app deve usar somente as bases novas importadas pela aba **📤 Importações Manuais**.

## Regra operacional

Sempre que for trocar a base completa, use o modo:

```text
Limpar base antiga e carregar somente este arquivo
```

Isso evita mistura com:

- CEPEA proxy antigo;
- CEPEA automático/scraper;
- CEAGESP automático/Playwright;
- bases antigas em `dw.fato_indicador_setorial`;
- versões antigas dos modelos manuais.

## CEPEA Manual

Tabela principal:

```text
app.fato_cepea_tilapia_manual
```

View usada no app:

```text
app.vw_cepea_tilapia_manual_historico
```

Campo usado no gráfico:

```text
PREÇO AJUSTADO -> preco_ajustado -> valor
```

O app não lê mais CEPEA automático nem CEPEA proxy.

## CEAGESP Manual

Tabela principal:

```text
app.fato_ceagesp_pescados
```

O app exibe somente registros que vieram da base manual nova, identificados por:

```text
fonte ILIKE '%manual%'
ou fonte_arquivo preenchido
ou hash_linha preenchido
```

## Prévia Vendedores

O fallback antigo para vendas internas foi removido. Agora a aba de prévia usa somente:

```text
app.fato_previa_vendedores
```

## Limpeza de legado

Para remover registros antigos de CEPEA/CEAGESP do banco, rode:

```powershell
python scripts\limpar_bases_antigas_cepea_ceagesp.py
```

Depois importe novamente os arquivos novos pela aba **Importações Manuais**.

## Validação

```powershell
python scripts\validar_cepea_ceagesp_fontes.py
pytest -q
```
