
# Hotfix IDH automático — Jina Reader

## Problema

Na rede local:

- `atlasbrasil.org.br` não resolve DNS;
- `www.undp.org` responde 403;
- API do dados.gov.br responde 401.

## Correção

O coletor agora tenta primeiro:

```text
https://r.jina.ai/https://www.undp.org/pt/brazil/idhm-municipios-2010
```

O Jina Reader converte a página pública do PNUD/UNDP em texto/Markdown. O script lê as linhas da tabela e extrai:

```text
ranking
município
UF
IDHM
IDHM Renda
IDHM Longevidade
IDHM Educação
```

Depois cruza com `dw.dim_geografia` por município + UF.

## Rodar

```bat
python scripts\apply_fontes_automaticas.py
python scripts\run_idh_automatico.py
python scripts\diagnosticar_v2_plano.py
```

## Esperado

```text
expansao_idh_atlas_brasil | 1668 | 1668 | OK
```

Se ainda falhar, é bloqueio de internet/proxy também no domínio `r.jina.ai`.
