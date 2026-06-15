# Hotfix IDH Jina Reader — Parser flexível

## Problema

O domínio `r.jina.ai` respondeu HTTP 200, mas o parser anterior não reconheceu a tabela.

## Correção

O parser agora aceita:

```text
ranking com ou sem º
linhas com ou sem pipe |
números com vírgula ou ponto decimal
município no formato Cidade (UF)
texto extra antes/depois da linha
```

Quando não conseguir parsear, salva:

```text
data/cache/idh_jina_reader_raw.txt
```

## Rodar

```bat
python scripts\apply_fontes_automaticas.py
python scripts\run_idh_automatico.py
python scripts\diagnosticar_v2_plano.py
```

## Diagnóstico do texto bruto

```bat
python scripts\debug_idh_jina.py
```
