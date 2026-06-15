
# Etapa 23 — Análise de Expansão por estado/região + documentação de fórmulas

## Objetivo

A aba **🌎 Análise de Expansão** passa a funcionar de forma parecida com **🧭 Região Comercial MG**:

```text
Usuário seleciona o estado
→ app mostra regiões econômicas/comerciais
→ usuário seleciona uma região
→ app mostra municípios da região
→ indicadores de população, PIB, IDH, IDC e score continuam alinhados ao plano
```

## Regra atual de regiões

```text
MG:
    usa regiao_comercial

SP, RJ, ES:
    usa mesorregiao IBGE como região econômica inicial

Fallback:
    se mesorregião estiver vazia, usa microrregião
```

## Por que essa regra

O plano pede expansão por estado, microrregião, IDC e potencial regional.
MG já possui regra comercial manualizada.
Para os demais estados do Sudeste, a mesorregião IBGE é usada como primeira aproximação econômica até a empresa definir recortes comerciais próprios.

## Arquivos alterados

```text
app.py
src/services/expansao_service.py
docs/FORMULAS_E_ONDE_SAO_APLICADAS.md
docs/ETAPA23_EXPANSAO_REGIOES_E_FORMULAS.md
```

## Como validar

```bat
.\.venv\Scripts\python.exe scripts\diagnosticar_v2_plano.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Na aba:

```text
🌎 Análise de Expansão
```

testar:

```text
Estado base = MG
Estado base = SP
Estado base = RJ
Estado base = ES
```

E conferir se aparecem:

```text
Regiões econômicas/comerciais do estado
Municípios da região selecionada
Resumo por estado
Microrregião, demografia, receita e IDC
Simulador de critérios IDC
Exportação das bases
```
