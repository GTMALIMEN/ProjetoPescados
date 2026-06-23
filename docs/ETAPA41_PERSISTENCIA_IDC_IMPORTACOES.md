# Etapa 41 — Persistência correta, importações manuais, APIs e IDC planejado

## Objetivo

Organizar o app para trabalhar de forma correta com dois tipos de dados:

1. **Dados automáticos/API**: IBGE, SIDRA, BCB, CEPEA, CONAB, Comex Stat e demais fontes públicas. Esses dados são gravados no banco em `raw`, `staging`, `dw` e `app`.
2. **Dados manuais/privados**: Scanntech, Key Account, endereços de lojas, curva de mercado, CEAGESP manual, compras, receita/vendas e prévia de vendedores. Esses dados são importados pela interface do Streamlit e gravados no banco.

## Central de Importações Manuais

Nova aba principal:

```text
📤 Importações Manuais
```

Bases aceitas:

- Scanntech / Total Mercado
- Curva de Mercado por Produto/Categoria
- Key Account / Endereços de Lojas
- CEAGESP Pescados
- Base de Compra Manual
- Receita/Vendas Expansão
- Prévia Vendedores

Cada base possui:

- botão para baixar modelo Excel;
- upload de Excel/CSV;
- prévia dos dados;
- validação de colunas obrigatórias;
- botão para importar;
- histórico em `app.importacao_manual_log`.

## Tabelas novas

```text
app.fato_mercado_privado
app.fato_curva_mercado_categoria
app.dim_key_account_loja
app.importacao_manual_log
```

## Dados automáticos e proxies

A Etapa 41 cria a view:

```text
app.vw_idc_completo_atual
```

Essa view preenche todos os campos automáticos possíveis. Quando ainda não existe fonte oficial para renda ou demografia, o app usa proxy, mas deixa isso marcado nas colunas de fonte.

Exemplo:

```text
fonte_renda = Proxy automático: PIB per capita mensal × 0,38 até carga Censo/POF oficial
fonte_demografia = Proxy automático até carga Censo 2022 sexo/faixa etária oficial
```

## Fórmula IDC planejada

O IDC principal passa a seguir a fórmula planejada:

```text
IDC =
30% População
+ 25% PIB
+ 15% Renda
+ 15% PIB per capita
+ 5% Feminino
+ 5% Masculino
+ 5% Pontos de venda
```

A fórmula antiga fica como `idc_macro`:

```text
IDC Macro = (Participação População % + Participação PIB %) / 2
```

## Correlação Mercado x IDC

Quando a Scanntech/mercado privado for importada, o app calcula correlação entre mercado real e:

- população;
- PIB;
- renda;
- PIB per capita;
- percentual feminino;
- percentual masculino;
- pontos de venda;
- IDH;
- fatores do IDC;
- score IDC.

Métricas disponíveis:

```text
valor_mercado
volume_mercado
preco_medio
```

## Como aplicar

```powershell
.\.venv\Scripts\python.exe scripts\apply_etapas41.py
```

Para atualizar somente dados automáticos, sem bases manuais:

```powershell
.\.venv\Scripts\python.exe scripts\run_automaticas_sem_manuais.py
```

Depois rode o app:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```
