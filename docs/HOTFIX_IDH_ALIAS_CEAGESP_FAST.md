
# Hotfix — IDH aliases + CEAGESP rápido

## IDH

O IDHM automático carregou 5.536 municípios e atualizou 1.660 dos 1.668 municípios do Sudeste.
Faltaram 8 por diferença de nome entre bases.

Foi criado:

```bat
python scripts\corrigir_idh_aliases.py
```

Ele resolve por aliases e fuzzy matching:

```text
Barão do Monte Alto ↔ Barão de Monte Alto
Brazópolis ↔ Brasópolis
Dona Euzébia ↔ Dona Eusébia
São Tomé das Letras ↔ São Thomé das Letras
Embu das Artes ↔ Embu
São Luiz do Paraitinga ↔ São Luís do Paraitinga
```

## CEAGESP

O coletor anterior podia ficar muito tempo tentando requisições.
Agora o coletor tem:

```text
timeout curto
limite de tentativas
tratamento de RequestException
registro em raw.fonte_automatica_payload
sem travar o pipeline
```

## Rodar

```bat
python scripts\corrigir_idh_aliases.py
python scripts\diagnosticar_v2_plano.py

python scripts\run_ceagesp_automatico.py --dias-busca 60 --timeout 8 --max-tentativas 12
python scripts\diagnosticar_v2_plano.py
```
