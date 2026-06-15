
# Hotfix IDH automático — Atlas rawData XLSX

## Problema

O PNUD retornou 403 e a API do dados.gov.br retornou 401.

## Correção

O coletor agora tenta primeiro o arquivo bruto clássico do Atlas Brasil:

```text
http://atlasbrasil.org.br/2013/data/rawData/atlas2013_dadosbrutos_pt.xlsx
```

Esse arquivo tem a aba:

```text
MUN 91-00-10
```

E as colunas esperadas:

```text
ANO
UF
Codmun7
Município
IDHM
IDHM_E
IDHM_L
IDHM_R
```

O script filtra `ANO = 2010`.

## Rodar

```bat
python scripts\apply_fontes_automaticas.py
python scripts\run_idh_automatico.py
python scripts\diagnosticar_v2_plano.py
```

## Fallback

```bat
python scripts\run_idh_automatico.py --url "http://atlasbrasil.org.br/2013/data/rawData/atlas2013_dadosbrutos_pt.xlsx"
```
