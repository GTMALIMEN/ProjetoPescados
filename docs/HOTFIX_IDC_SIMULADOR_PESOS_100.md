# Hotfix — Simulador IDC com pesos somando 100%

## Objetivo

Ajustar o simulador de critérios IDC para que todos os fatores entrem na conta e os pesos sempre fechem 100%.

## Antes

Os sliders eram independentes:

```text
Peso população = 30
Peso PIB = 25
Peso gênero masculino = 5
Peso gênero feminino = 5
Peso PIB per capita = 15
Peso renda / POF = 15
Peso pontos de venda = 5
```

Mesmo que o usuário alterasse um peso, os outros não se ajustavam visualmente.

## Agora

Ao alterar qualquer peso, os demais são redistribuídos proporcionalmente para que o total continue 100%.

Exemplo:

```text
Se pontos de venda aumentar,
os outros pesos caem proporcionalmente.

Se PIB diminuir,
os outros pesos sobem proporcionalmente.
```

## Fórmula do IDC base

O IDC base continua igual:

```text
IDC base = (Participação População % + Participação PIB %) / 2
```

## Fórmula do IDC simulado

O IDC simulado usa todos os fatores:

```text
IDC simulado =
    fator_populacao × peso_populacao
  + fator_pib × peso_pib
  + fator_masculino × peso_masculino
  + fator_feminino × peso_feminino
  + fator_pib_per_capita × peso_faixa_etaria
  + fator_renda × peso_renda
  + fator_pdv × peso_pdv
```

Como os pesos somam 100%, a interpretação é direta:

```text
IDC simulado = soma(fator × peso) / 100
```

## Fatores usados

```text
fator_populacao = participação da população no recorte
fator_pib = participação do PIB no recorte
fator_masculino = percentual masculino normalizado para 0-100
fator_feminino = percentual feminino normalizado para 0-100
fator_pib_per_capita = 15-29 + 30-44 + 50% de 45-59, normalizado para 0-100
fator_renda = renda média normalizada para 0-100
fator_pdv = supermercados + restaurantes + peixarias + outros_pdv, normalizado para 0-100
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

Na aba **Análise de Expansão**, alterar qualquer slider do simulador. O total deve permanecer 100%.
