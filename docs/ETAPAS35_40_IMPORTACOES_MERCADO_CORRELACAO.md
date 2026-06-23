
# Etapas 35-40 — Importações Manuais, Mercado Real e Correlação IDC

## Etapa 35 — Central de Importações Manuais

Nova aba no Streamlit: `📤 Importações Manuais`.

Permite ao usuário subir arquivos Excel/CSV sem código para:

- Scanntech / Total Mercado Privado
- Key Account / Endereços de Lojas
- Curva de Mercado por Produto/Categoria
- CEAGESP Pescados manual
- Base de Compra Manual
- Receita/Vendas Expansão
- Prévia Vendedores

Cada tela possui:

- download de modelo Excel;
- upload do arquivo;
- prévia normalizada;
- validação de colunas obrigatórias;
- opção `Adicionar dados` ou `Substituir período do arquivo`;
- registro no histórico de importações.

## Etapa 36 — Mercado Privado / Scanntech

Tabela principal: `app.fato_mercado_privado`.

Colunas principais:

- data_competencia
- uf
- cidade
- microrregiao
- categoria
- produto
- marca
- ean
- canal
- valor_mercado
- volume_mercado
- preco_medio
- ticket_medio
- qtd_lojas
- fonte

## Etapa 37 — Receita Estimada x Mercado Real

A antiga `Receita por Categoria` passa a ser tratada como estimativa/potencial econômico ou venda interna quando houver base importada.

A Scanntech/mercado privado passa a representar o mercado real privado.

A comparação fica:

```text
Gap = Mercado Real Privado - Receita Estimada/Interna
```

## Etapa 38 — Curva de Mercado por Produto/Categoria

Tabela: `app.fato_curva_mercado_categoria`.

Permite acompanhar:

- valor mensal de mercado;
- volume mensal;
- preço médio;
- crescimento por produto/categoria;
- comportamento por microrregião.

## Etapa 39 — Correlação Mercado x IDC

Cruza mercado privado com a base de expansão/IBGE por:

```text
UF + microrregião
```

Variáveis testadas:

- População
- PIB
- Renda média oficial
- Renda média proxy
- PIB per capita
- % Feminino
- % Masculino
- Pontos de venda
- IDH
- IDC base
- Score IDC

Métricas de correlação:

- Pearson
- Spearman
- força da correlação
- direção positiva/negativa

## Etapa 40 — IDC Ajustado por Mercado

A correlação sugere pesos para calibrar o IDC.

O IDC base continua com a regra de negócio definida:

```text
30% População
25% PIB
15% Renda
15% PIB per capita
5% Feminino
5% Masculino
5% Pontos de venda
```

O IDC ajustado por mercado não substitui automaticamente o IDC principal; ele mostra uma sugestão baseada no mercado privado importado.

## Aplicar estrutura no banco

```powershell
.\.venv\Scripts\python.exe scripts\apply_etapas35_40.py
```

## Rodar app

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```
