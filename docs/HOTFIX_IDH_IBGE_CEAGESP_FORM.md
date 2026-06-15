
# Hotfix — IDH fallback IBGE + CEAGESP formulário real

## IDH

O IDHM automático via PNUD/Jina carregou 5.536 municípios, mas 8 municípios do Sudeste ficaram sem IDH.
Eles foram preenchidos com fallback oficial do IBGE Cidades, indicador IDHM 2010, cuja fonte original é PNUD.

Script:

```bat
python scripts\preencher_idh_faltantes_ibge.py
python scripts\diagnosticar_v2_plano.py
```

Municípios:

```text
Barão do Monte Alto — 0,649
Brazópolis — 0,692
Coronel Pacheco — 0,669
Dona Euzébia — 0,701
São Tomé das Letras — 0,667
Embu das Artes — 0,735
Florínea — 0,713
São Luiz do Paraitinga — 0,697
```

## CEAGESP

O HTML detectou formulário:

```text
method=post
fields=cot_grupo, cot_data
```

O coletor agora testa primeiro:

```text
cot_grupo=PESCADOS
cot_data=dd/mm/aaaa
```

e mantém limite seguro de tentativas para não travar.

Script:

```bat
python scripts\run_ceagesp_automatico.py --dias-busca 60 --timeout 8 --max-tentativas 20
```
