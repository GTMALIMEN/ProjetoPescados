# Hotfix — IDC Simulado com PIB per capita

## Ajuste solicitado

Substituir o critério:

```text
Peso faixa etária
```

por:

```text
Peso PIB per capita
```

## Pesos padrão atualizados

```text
30% População
25% PIB
15% Renda / POF
15% PIB per capita
5% Gênero masculino
5% Gênero feminino
5% Pontos de venda
```

Total:

```text
100%
```

## Fórmula do IDC base

O IDC base permanece igual:

```text
IDC base = (Participação População % + Participação PIB %) / 2
```

## Fórmula do IDC simulado

O IDC simulado passa a usar:

```text
IDC simulado =
    fator_populacao × 30%
  + fator_pib × 25%
  + fator_renda × 15%
  + fator_pib_per_capita × 15%
  + fator_masculino × 5%
  + fator_feminino × 5%
  + fator_pdv × 5%
```

Como os pesos sempre somam 100%, a fórmula pode ser lida como:

```text
IDC simulado = soma(fator × peso) / 100
```

## O que é PIB per capita no simulador

```text
PIB per capita = PIB / População
```

No simulador, ele é normalizado para escala 0-100 dentro do recorte selecionado.

Interpretação:

```text
Regiões com maior PIB por habitante sobem no IDC simulado.
```

## Onde foi alterado

```text
app.py
src/services/expansao_service.py
```

## Como validar

```bat
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Na aba **Análise de Expansão**, o simulador deve mostrar:

```text
Peso população
Peso PIB
Peso renda / POF
Peso PIB per capita
Peso gênero masculino
Peso gênero feminino
Peso pontos de venda
```
