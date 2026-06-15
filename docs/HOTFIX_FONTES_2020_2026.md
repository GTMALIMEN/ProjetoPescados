# Hotfix — Fontes setoriais 2020–2026 e regiões MG

## Problemas encontrados

1. A aba **Região Comercial MG** indicava:

```text
Nenhuma região comercial de MG encontrada.
```

Causa: faltou rodar:

```bash
python scripts\apply_regioes_mg.py
```

2. O período setorial aparecia somente de **2024 até 2026**.

Causa: os arquivos de exemplo `cepea_tilapia.xlsx` e `conab_precos_milho_soja.xlsx` tinham dados somente de 2024–2026.

3. A comparação tinha poucos itens.

Causa: os arquivos de entrada tinham apenas:

```text
Tilápia, Frango
Milho, Soja
```

## Correção aplicada

Os arquivos foram expandidos para 2020–2026:

```text
data/input/cepea_tilapia.xlsx
data/input/conab_precos_milho_soja.xlsx
```

Produtos de proteína:

```text
Tilápia
Frango
Suíno
Bovino
Ovos
Salmão importado
Bacalhau importado
Camarão
```

Grãos/insumos:

```text
Milho
Soja
Farelo de soja
Farinha de peixe
Óleo de soja
Ração aquícola
```

## Rodar correção

```bash
scripts\recarregar_fontes_2020_2026.bat
```

Ou manualmente:

```bash
python scripts\apply_regioes_mg.py
python scripts\run_comex_pescados.py --ano-inicio 2020 --ano-fim 2026 --delay 60
python scripts\load_cepea_file.py --arquivo "data\input\cepea_tilapia.xlsx" --categoria proteina --produto-default Tilápia --uf-default MG
python scripts\load_conab_file.py --arquivo "data\input\conab_precos_milho_soja.xlsx" --categoria graos_racao --produto-default Milho --uf-default MG
python scripts\calculate_indices_setoriais.py --uf MG --salvar
python scripts\calculate_potencial.py --uf MG --salvar
python scripts\calculate_scores.py --uf MG --salvar
python scripts\generate_recommendations.py --uf MG --salvar
python scripts\generate_active_alerts.py --uf MG --salvar
```

## Diagnóstico

```bash
python scripts\diagnosticar_fontes_setoriais.py
```
