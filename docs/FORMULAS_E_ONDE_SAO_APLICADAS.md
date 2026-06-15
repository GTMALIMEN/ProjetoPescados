
# Fórmulas e onde são aplicadas — Radar Pescados IA

Este documento contém apenas as fórmulas do projeto e onde cada uma é aplicada.

---

## 1. Região econômica/comercial

### Fórmula/regra

```text
Se UF = MG:
    região_econômica = regiao_comercial

Se UF ∈ {SP, RJ, ES}:
    região_econômica = mesorregiao IBGE

Se mesorregião estiver vazia:
    região_econômica = microrregiao

Se tudo estiver vazio:
    região_econômica = "Sem região econômica"
```

### Onde é aplicada

```text
Aba: 🌎 Análise de Expansão
Bloco: Regiões econômicas/comerciais do estado
Funções:
- _with_regiao_economica()
- carregar_regioes_economicas_expansao()
- carregar_municipios_regiao_economica_expansao()
Arquivo:
- src/services/expansao_service.py
```

### Objetivo

Permitir que o usuário escolha o estado e visualize regiões econômicas/comerciais, de forma parecida com a aba Região Comercial MG.

---

## 2. População por estado, região ou microrregião

### Fórmula

```text
População total = soma da população dos municípios do recorte
```

### Onde é aplicada

```text
Aba: 🌎 Análise de Expansão
Blocos:
- Resumo por estado
- Regiões econômicas/comerciais do estado
- Microrregiões
- IDC / Margin Pool

Funções:
- carregar_resumo_estado_expansao()
- carregar_regioes_economicas_expansao()
- carregar_microrregiao_expansao()
- calcular_idc_expansao()
```

---

## 3. PIB por estado, região ou microrregião

### Fórmula

```text
PIB total = soma do PIB dos municípios do recorte
```

### Onde é aplicada

```text
Aba: 🌎 Análise de Expansão
Blocos:
- Resumo por estado
- Regiões econômicas/comerciais do estado
- Microrregiões
- IDC / Margin Pool

Funções:
- carregar_resumo_estado_expansao()
- carregar_regioes_economicas_expansao()
- carregar_microrregiao_expansao()
- calcular_idc_expansao()
```

---

## 4. PIB per capita

### Fórmula

```text
PIB per capita = PIB / População
```

### Onde é aplicada

```text
Aba: 🌎 Análise de Expansão
Blocos:
- Resumo por estado
- Regiões econômicas/comerciais
- Microrregiões
- Municípios da região selecionada

Funções:
- _base_expansao_municipal()
- carregar_regioes_economicas_expansao()
- carregar_microrregiao_expansao()
```

---

## 5. IDH/IDHM médio

### Fórmula

```text
IDH médio = média simples do IDH/IDHM dos municípios do recorte
```

### Onde é aplicada

```text
Aba: 🌎 Análise de Expansão
Blocos:
- Resumo por estado
- Regiões econômicas/comerciais
- Microrregiões

Funções:
- carregar_resumo_estado_expansao()
- carregar_regioes_economicas_expansao()
- carregar_microrregiao_expansao()
```

### Observação

O IDH/IDHM está carregado em 100% para o Sudeste após o fallback IBGE/PNUD dos 8 municípios faltantes.

---

## 6. Participação da população

### Fórmula

```text
Participação População % =
    População do recorte / População total do estado ou seleção × 100
```

### Onde é aplicada

```text
Aba: 🌎 Análise de Expansão
Blocos:
- Regiões econômicas/comerciais do estado
- IDC / Margin Pool

Funções:
- carregar_regioes_economicas_expansao()
- calcular_idc_expansao()
```

---

## 7. Participação do PIB

### Fórmula

```text
Participação PIB % =
    PIB do recorte / PIB total do estado ou seleção × 100
```

### Onde é aplicada

```text
Aba: 🌎 Análise de Expansão
Blocos:
- Regiões econômicas/comerciais do estado
- IDC / Margin Pool

Funções:
- carregar_regioes_economicas_expansao()
- calcular_idc_expansao()
```

---

## 8. IDC base

### Fórmula principal

```text
IDC base =
    (Participação População % + Participação PIB %) / 2
```

### Fórmula de contingência

```text
Se PIB estiver ausente:
    IDC base = Participação População %
```

### Onde é aplicada

```text
Aba: 🌎 Análise de Expansão
Blocos:
- IDC / Margin Pool
- Simulador de critérios IDC

Funções:
- calcular_idc_expansao()
- simular_idc_expansao()
```

---

## 9. Participação da receita

### Fórmula

```text
Participação Receita % =
    Receita real do recorte / Receita total da seleção × 100
```

### Onde é aplicada

```text
Aba: 🌎 Análise de Expansão
Blocos:
- Receita por categoria
- IDC / Margin Pool

Função:
- calcular_idc_expansao()
```

---

## 10. Over/under share

### Fórmula

```text
Over/Under Share % =
    Participação Receita % - IDC base
```

### Interpretação

```text
Valor positivo:
    região vende mais do que o potencial estimado pelo IDC.

Valor negativo:
    região vende menos do que o potencial estimado pelo IDC.
```

### Onde é aplicada

```text
Aba: 🌎 Análise de Expansão
Bloco: IDC / Margin Pool
Função: calcular_idc_expansao()
```

---

## 11. Receita esperada pelo IDC

### Fórmula

```text
Receita esperada IDC =
    Receita total da seleção × IDC base / 100
```

### Onde é aplicada

```text
Aba: 🌎 Análise de Expansão
Bloco: IDC / Margin Pool
Função: calcular_idc_expansao()
```

---

## 12. Oportunidade

### Fórmula

```text
Oportunidade =
    Receita esperada IDC - Receita real
```

### Onde é aplicada

```text
Aba: 🌎 Análise de Expansão
Bloco: IDC / Margin Pool
Função: calcular_idc_expansao()
```

---

## 13. Margin Pool %

### Fórmula

```text
Margin Pool % =
    Oportunidade / Receita total da seleção × 100
```

### Onde é aplicada

```text
Aba: 🌎 Análise de Expansão
Bloco: IDC / Margin Pool
Função: calcular_idc_expansao()
```

---

## 14. Score de expansão / score IDC

### Fórmula

```text
Score base =
    IDC base - Over/Under Share %
```

Depois:

```text
Score normalizado =
    Score base / maior Score base da seleção × 100
```

### Onde é aplicada

```text
Aba: 🌎 Análise de Expansão
Blocos:
- Resumo por estado
- Regiões econômicas/comerciais
- IDC / Margin Pool

Funções:
- _score_pct()
- carregar_resumo_estado_expansao()
- carregar_regioes_economicas_expansao()
- calcular_idc_expansao()
```

---

## 15. Classificação da prioridade

### Fórmula/regra

```text
Se score >= 75:
    Alta prioridade

Se score >= 55 e < 75:
    Média prioridade

Se score >= 35 e < 55:
    Baixa prioridade

Se score < 35:
    Monitorar
```

### Onde é aplicada

```text
Aba: 🌎 Análise de Expansão
Blocos:
- Resumo por estado
- Regiões econômicas/comerciais
- Microrregiões
- IDC / Margin Pool
- Simulador IDC

Função:
- _classificar_score()
```

---

## 16. Simulador IDC

### Fórmula

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

Depois:

```text
IDC simulado =
    IDC simulado bruto / soma dos pesos válidos
```

Depois:

```text
Score simulado =
    IDC simulado normalizado em escala 0 a 100
```

### Onde é aplicada

```text
Aba: 🌎 Análise de Expansão
Bloco: Simulador de critérios IDC / What-if Expansão

Função:
- simular_idc_expansao()
```

---

## 17. Receita por categoria

### Fórmula

```text
Receita total da categoria =
    soma da receita do produto/categoria dentro da microrregião e estado
```

Categorias atuais:

```text
Tilápia
Salmão
Camarão
Piramutaba
Polaca
Merluza
Panga
```

### Onde é aplicada

```text
Aba: 🌎 Análise de Expansão
Bloco: Receita por categoria
Função: carregar_receita_categoria_expansao()
```

---

## 18. CEAGESP manual

### Fórmula de chave do histórico

```text
chave_registro =
    hash(data_referencia + produto + classificação + unidade)
```

### Onde é aplicada

```text
Aba: 📈 Análise Previsão de Mercado
Bloco: CEAGESP histórico/manual
Script:
- scripts/load_ceagesp_manual_file.py

Tabela:
- app.fato_ceagesp_pescados
```

### Regra

Se carregar a mesma data/produto/classificação/unidade novamente:

```text
Atualiza o registro existente.
Não duplica.
```

---

## 19. Preço comum CEAGESP

### Fórmula

```text
Preço comum = valor digitado/importado no campo preco_comum
```

### Onde é aplicada

```text
Aba: 📈 Análise Previsão de Mercado
Bloco: CEAGESP histórico/manual
Tabela:
- app.fato_ceagesp_pescados
```

---

## 20. Exportação das bases

### Fórmula/regra

```text
Exportação = junção das tabelas já calculadas em abas separadas do Excel
```

### Onde é aplicada

```text
Aba: 🌎 Análise de Expansão
Botão: Baixar Excel — Análise de Expansão
Função: exportar_bases_expansao_excel()

Aba: 📈 Análise Previsão de Mercado
Botão: Baixar Excel — Análise Previsão de Mercado
Função: exportar_bases_previsao_mercado_excel()
```
