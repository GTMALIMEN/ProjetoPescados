# Documentação — Fórmulas e onde são aplicadas  
## Radar Pescados IA

Este documento explica somente as fórmulas do APP, onde elas aparecem e quais arquivos/funções as aplicam.

---

# 1. Região econômica/comercial

## Fórmula/regra

```text
Se UF = MG:
    regiao_economica = regiao_comercial

Se UF = SP, RJ ou ES:
    regiao_economica = mesorregiao IBGE

Se mesorregiao estiver vazia:
    regiao_economica = microrregiao

Se tudo estiver vazio:
    regiao_economica = "Sem região econômica"
```

## Onde é aplicada

```text
Aba principal: 🌎 Análise de Expansão
Subaba: 🌎 Análise de Expansão
Bloco: Regiões econômicas/comerciais
Bloco: Municípios da região selecionada
```

## Funções

```text
_with_regiao_economica()
carregar_regioes_economicas_expansao()
carregar_municipios_regiao_economica_expansao()
```

## Arquivo

```text
src/services/expansao_service.py
```

---

# 2. População total

## Fórmula

```text
População total = soma da população dos municípios do recorte
```

## Onde é aplicada

```text
Resumo por estado
Regiões econômicas/comerciais
Microrregiões
IDC / Margin Pool
Simulador IDC
```

## Funções

```text
carregar_resumo_estado_expansao()
carregar_regioes_economicas_expansao()
carregar_microrregiao_expansao()
calcular_idc_expansao()
simular_idc_expansao()
```

---

# 3. PIB total

## Fórmula

```text
PIB total = soma do PIB dos municípios do recorte
```

## Onde é aplicada

```text
Resumo por estado
Regiões econômicas/comerciais
Microrregiões
IDC / Margin Pool
```

## Funções

```text
carregar_resumo_estado_expansao()
carregar_regioes_economicas_expansao()
carregar_microrregiao_expansao()
calcular_idc_expansao()
```

---

# 4. PIB per capita

## Fórmula

```text
PIB per capita = PIB / População
```

## Onde é aplicada

```text
Resumo por estado
Regiões econômicas/comerciais
Municípios da região selecionada
Microrregiões
Renda proxy
```

## Funções

```text
_base_expansao_municipal()
carregar_regioes_economicas_expansao()
carregar_microrregiao_expansao()
run_censo_demografico_2022.py
```

---

# 5. IDH/IDHM médio

## Fórmula

```text
IDH médio = média simples do IDH dos municípios do recorte
```

## Onde é aplicada

```text
Resumo por estado
Regiões econômicas/comerciais
Microrregiões
IDC / leitura de qualidade regional
```

## Funções

```text
carregar_resumo_estado_expansao()
carregar_regioes_economicas_expansao()
carregar_microrregiao_expansao()
```

---

# 6. Percentual masculino

## Fórmula

```text
% Masculino = População masculina / População total × 100
```

## Onde é aplicada

```text
Perfil demográfico
Simulador IDC
```

## Situação atual

Na versão atual, esse campo pode ser preenchido por proxy controlado até carga SIDRA municipal fina.

## Script atual

```text
scripts/run_censo_demografico_2022.py
```

---

# 7. Percentual feminino

## Fórmula

```text
% Feminino = População feminina / População total × 100
```

## Onde é aplicada

```text
Perfil demográfico
Simulador IDC
```

## Script atual

```text
scripts/run_censo_demografico_2022.py
```

---

# 8. Faixa etária

## Fórmulas

```text
% 0 a 14 = População 0 a 14 / População total × 100

% 15 a 29 = População 15 a 29 / População total × 100

% 30 a 44 = População 30 a 44 / População total × 100

% 45 a 59 = População 45 a 59 / População total × 100

% 60+ = População 60+ / População total × 100
```

## Onde é aplicada

```text
Perfil demográfico
Simulador IDC
Score futuro de demanda
```

## Script atual

```text
scripts/run_censo_demografico_2022.py
```

---

# 9. Renda média proxy

## Fórmula atual

```text
renda_media_proxy = (PIB per capita anual / 12) × 0,38
```

Com limite defensivo:

```text
mínimo = 900
máximo = 8500
```

## Onde é aplicada

```text
Perfil demográfico
Regiões econômicas/comerciais
PDV proxy
Simulador IDC
```

## Script

```text
scripts/run_censo_demografico_2022.py
```

## Observação

É uma aproximação operacional, não dado oficial. Deve ser substituída por renda SIDRA/Censo/POF.

---

# 10. Classe de renda proxy

## Fórmula/regra

A partir da renda média estimada, o app cria percentuais aproximados:

```text
renda_classe_a
renda_classe_b
renda_classe_c
renda_classe_de
```

Regra simplificada:

```text
Classe A cresce quando renda média aumenta
Classe B cresce quando renda média aumenta
Classe C fica como faixa intermediária
Classe DE recebe o saldo até 100%
```

## Onde é aplicada

```text
Perfil demográfico
Simulador IDC
Futura segmentação de regiões
```

## Script

```text
scripts/run_censo_demografico_2022.py
```

---

# 11. PDV proxy — supermercados

## Fórmula atual

```text
supermercados = teto((população / 18000) × fator_renda)
```

Com mínimo:

```text
se população > 15000:
    mínimo = 1
senão:
    mínimo = 0
```

## Onde é aplicada

```text
Regiões econômicas/comerciais
Municípios da região selecionada
IDC / Margin Pool
Simulador IDC
```

## Script

```text
scripts/run_pdv_proxy.py
```

---

# 12. PDV proxy — restaurantes

## Fórmula atual

```text
restaurantes = teto((população / 4200) × fator_renda)
```

Com mínimo:

```text
se população > 8000:
    mínimo = 1
senão:
    mínimo = 0
```

## Onde é aplicada

```text
Regiões econômicas/comerciais
Municípios da região selecionada
IDC / Margin Pool
Simulador IDC
```

## Script

```text
scripts/run_pdv_proxy.py
```

---

# 13. PDV proxy — peixarias

## Fórmula atual

```text
peixarias = teto((população / 65000) × fator_renda)
```

## Onde é aplicada

```text
Regiões econômicas/comerciais
Municípios da região selecionada
IDC / Margin Pool
Simulador IDC
```

## Script

```text
scripts/run_pdv_proxy.py
```

---

# 14. PDV proxy — outros PDV

## Fórmula atual

```text
outros_pdv = teto((população / 12000) × fator_renda)
```

Com mínimo:

```text
se população > 12000:
    mínimo = 1
senão:
    mínimo = 0
```

## Onde é aplicada

```text
Regiões econômicas/comerciais
Municípios da região selecionada
IDC / Margin Pool
Simulador IDC
```

## Script

```text
scripts/run_pdv_proxy.py
```

---

# 15. Fator de renda do PDV proxy

## Fórmula/regra

```text
fator_renda = 1,00

Se renda_media > 3500:
    fator_renda += 0,12

Se renda_media < 1600:
    fator_renda -= 0,08

Se pib_per_capita > 100:
    fator_renda += 0,08
```

## Onde é aplicada

```text
Cálculo de supermercados
Cálculo de restaurantes
Cálculo de peixarias
Cálculo de outros_pdv
```

## Script

```text
scripts/run_pdv_proxy.py
```

---

# 16. Participação da população

## Fórmula

```text
Participação População % =
    População do recorte / População total da seleção × 100
```

## Onde é aplicada

```text
Regiões econômicas/comerciais
IDC / Margin Pool
Simulador IDC
```

## Funções

```text
carregar_regioes_economicas_expansao()
calcular_idc_expansao()
```

---

# 17. Participação do PIB

## Fórmula

```text
Participação PIB % =
    PIB do recorte / PIB total da seleção × 100
```

## Onde é aplicada

```text
Regiões econômicas/comerciais
IDC / Margin Pool
Simulador IDC
```

## Funções

```text
carregar_regioes_economicas_expansao()
calcular_idc_expansao()
```

---

# 18. IDC base

## Fórmula

```text
IDC base =
    (Participação População % + Participação PIB %) / 2
```

## Fórmula de contingência

```text
Se PIB não existir:
    IDC base = Participação População %
```

## Onde é aplicada

```text
IDC / Margin Pool
Regiões econômicas/comerciais
Simulador IDC
```

## Funções

```text
calcular_idc_expansao()
carregar_regioes_economicas_expansao()
simular_idc_expansao()
```

---

# 19. Participação da receita

## Fórmula

```text
Participação Receita % =
    Receita do recorte / Receita total da seleção × 100
```

## Onde é aplicada

```text
Receita por categoria
IDC / Margin Pool
```

## Função

```text
calcular_idc_expansao()
```

---

# 20. Over/under share

## Fórmula

```text
Over/Under Share % =
    Participação Receita % - IDC base
```

## Interpretação

```text
Valor positivo:
    região vende acima do potencial esperado

Valor negativo:
    região vende abaixo do potencial esperado
```

## Onde é aplicada

```text
IDC / Margin Pool
```

## Função

```text
calcular_idc_expansao()
```

---

# 21. Receita esperada pelo IDC

## Fórmula

```text
Receita esperada IDC =
    Receita total × IDC base / 100
```

## Onde é aplicada

```text
IDC / Margin Pool
```

## Função

```text
calcular_idc_expansao()
```

---

# 22. Oportunidade

## Fórmula

```text
Oportunidade =
    Receita esperada IDC - Receita real
```

## Onde é aplicada

```text
IDC / Margin Pool
Ranking de expansão
Relatório executivo futuro
```

## Função

```text
calcular_idc_expansao()
```

---

# 23. Margin Pool %

## Fórmula

```text
Margin Pool % =
    Oportunidade / Receita total × 100
```

## Onde é aplicada

```text
IDC / Margin Pool
```

## Função

```text
calcular_idc_expansao()
```

---

# 24. Score de expansão

## Fórmula base

```text
score_base =
    IDC base - Over/Under Share %
```

## Normalização

```text
score_expansao =
    score_base / maior_score_base_da_seleção × 100
```

## Onde é aplicada

```text
Resumo por estado
Regiões econômicas/comerciais
IDC / Margin Pool
Ranking de oportunidade
```

## Funções

```text
_score_pct()
carregar_resumo_estado_expansao()
carregar_regioes_economicas_expansao()
calcular_idc_expansao()
```

---

# 25. Classificação de prioridade

## Fórmula/regra

```text
Se score >= 75:
    Alta prioridade

Se score >= 55 e score < 75:
    Média prioridade

Se score >= 35 e score < 55:
    Baixa prioridade

Se score < 35:
    Monitorar
```

## Onde é aplicada

```text
Resumo por estado
Regiões econômicas/comerciais
Microrregiões
IDC / Margin Pool
Simulador IDC
```

## Função

```text
_classificar_score()
```

---

# 26. Simulador IDC

## Fórmula

```text
IDC simulado bruto =
    Participação População % × Peso População
  + Participação PIB % × Peso PIB
  + % Masculino × Peso Masculino
  + % Feminino × Peso Feminino
  + Indicador Faixa Etária × Peso Faixa Etária
  + Indicador Renda × Peso Renda
  + Indicador PDV × Peso PDV
```

## Normalização

```text
IDC simulado =
    IDC simulado bruto / soma dos pesos válidos
```

## Score simulado

```text
Score simulado =
    IDC simulado normalizado em escala 0 a 100
```

## Onde é aplicada

```text
What-if / Simulador IDC
```

## Função

```text
simular_idc_expansao()
```

---

# 27. Receita por categoria

## Fórmula

```text
Receita por categoria =
    soma da receita do produto dentro do recorte
```

Categorias previstas:

```text
Tilápia
Salmão
Camarão
Piramutaba
Polaca
Merluza
Panga
```

## Onde é aplicada

```text
Receita por categoria
IDC / Margin Pool
Futura previsão de demanda
```

## Função

```text
carregar_receita_categoria_expansao()
```

---

# 28. CEAGESP manual — chave do histórico

## Fórmula

```text
chave_registro =
    hash(data_referencia + produto + classificação + unidade)
```

## Onde é aplicada

```text
Análise Previsão de Mercado
CEAGESP manual/histórico
```

## Script

```text
scripts/load_ceagesp_manual_file.py
```

## Regra

```text
Se carregar a mesma data/produto/classificação/unidade:
    atualiza registro existente

Se for combinação nova:
    insere novo registro
```

---

# 29. Base de compra manual — valor total

## Fórmula

```text
valor_total =
    preço real de compra × quantidade comprada
```

## Onde é aplicada

```text
Análise Previsão de Mercado
Base de compra manual
Futura previsão de preço
```

## Script

```text
scripts/load_compra_manual_file.py
```

---

# 30. Prévia vendedores — receita total

## Fórmula

```text
receita_total =
    preço × quantidade vendida
```

## Onde é aplicada

```text
Análise Previsão de Mercado
Prévia vendedores
Futura previsão de demanda
```

## Script

```text
scripts/load_previa_vendedores_file.py
```

---

# 31. Comex Stat — preço médio de importação

## Fórmula

```text
Preço médio importação =
    Valor FOB / Peso KG
```

## Onde é aplicada

```text
Fontes Reais
Comex Stat
Análise Previsão de Mercado
Futura previsão de preço
```

## Scripts

```text
scripts/run_comex_refinado.py
scripts/run_comex_pescados.py
```

---

# 32. Diagnóstico V2

## Fórmula/regra

O diagnóstico conta registros preenchidos por tema.

Exemplo:

```text
qtd_preenchida =
    quantidade de municípios/registros com campo preenchido

qtd_total =
    quantidade total esperada
```

## Status

```text
OK
PARCIAL
OK_PROXY_ESTIMADO
OK_COM_DADOS
OK_SEM_DADOS
PENDENTE
PENDENTE_IMPORTACAO
PENDENTE_RENDA
PENDENTE_BASE_PDV
PENDENTE_CENSO_DEMOGRAFIA
```

## Onde é aplicada

```text
Saúde do Sistema
Diagnóstico final dos scripts
Controle de qualidade do projeto
```

## View

```text
app.vw_diagnostico_v2_plano
```

---

# 33. Futuras fórmulas de Machine Learning

Ainda não aplicadas.

## Previsão de preço

```text
Preço futuro = modelo(histórico de compra, CEAGESP, Comex, CEPEA, CONAB, dólar, sazonalidade)
```

## Previsão de demanda

```text
Demanda futura = modelo(vendas históricas, prévia vendedores, preço, região, produto, mês)
```

## Score ML de oportunidade

```text
Probabilidade de oportunidade =
    modelo(população, PIB, IDH, renda, faixa etária, PDV, vendas, preço)
```

## Segmentação

```text
Cluster regional =
    algoritmo de agrupamento(população, PIB, renda, PDV, vendas, IDH)
```

## Anomalias

```text
Anomalia =
    comportamento muito diferente do padrão histórico
```

---

# 34. Observação final

Sempre verificar a fonte antes de interpretar o número.

Campos com proxy devem ser interpretados como estimativa:

```text
fonte_demografia
fonte_renda
fonte_pdv
```

Campos oficiais ou internos devem manter fonte clara:

```text
fonte_populacao
fonte_pib
fonte_idh
fonte_compra
fonte_comex
```


---

# Hotfix IDC simulado com pesos 100%

O simulador do IDC agora usa todos os fatores e força soma de pesos em 100%.

```text
IDC simulado = soma(fator × peso) / 100
```

Fatores:

```text
população
PIB
gênero masculino
gênero feminino
faixa etária
renda / POF
pontos de venda
```

Quando um peso é alterado na tela, os demais são redistribuídos proporcionalmente para manter o total em 100%.
