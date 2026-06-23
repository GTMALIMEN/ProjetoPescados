# Importações Manuais — Projeto Pescados

Este documento define o padrão oficial para upload manual de bases no app.

Toda base manual deve seguir três regras:

1. Ter colunas obrigatórias padronizadas.
2. Ser validada antes de entrar no banco.
3. Ser salva no Supabase/PostgreSQL com histórico de importação.

Nenhuma base manual deve ficar apenas carregada no Streamlit. Subiu, validou e confirmou, precisa persistir no banco.

---

## Fluxo padrão de importação

1. Usuário baixa o modelo Excel na aba de importações.
2. Usuário preenche a planilha respeitando as colunas obrigatórias.
3. Usuário sobe o arquivo no app.
4. O app valida:
   - colunas obrigatórias;
   - datas;
   - valores numéricos;
   - UF;
   - linhas vazias;
   - duplicidades.
5. O app mostra prévia da importação.
6. O usuário confirma.
7. O app grava no Supabase/PostgreSQL.
8. O app registra histórico em `app.importacao_manual_log`.
9. Linhas inválidas são registradas em `app.importacao_manual_rejeicoes`.

---

## Tabelas de controle

### app.importacao_manual_log

Registra o histórico de cada importação manual.

Colunas principais:

- `tipo_importacao`
- `arquivo`
- `status`
- `registros_lidos`
- `registros_processados`
- `registros_rejeitados`
- `detalhe`
- `usuario`
- `executado_em`

### app.importacao_manual_rejeicoes

Registra linhas rejeitadas.

Colunas principais:

- `tipo_importacao`
- `arquivo`
- `linha`
- `coluna`
- `valor`
- `motivo`
- `criado_em`

---

# Bases manuais oficiais

## 1. Scanntech / Mercado Privado

Tabela destino:

`app.fato_mercado_privado`

Modelo:

`modelos_importacao/modelo_scanntech_mercado_privado.xlsx`

### Colunas obrigatórias

- `data_competencia`
- `uf`
- `microrregiao`
- `categoria`
- `valor_mercado`
- `volume_mercado`

### Colunas opcionais

- `cidade`
- `produto`
- `marca`
- `ean`
- `canal`
- `preco_medio`
- `qtd_lojas`
- `fonte`

### Regra de cálculo

Se `preco_medio` vier vazio:

`preco_medio = valor_mercado / volume_mercado`

### Uso no app

- Total de mercado privado.
- Curva de mercado.
- Correlação Mercado x IDC.
- Comparação potencial x venda real.

---

## 2. Curva de Mercado por Categoria

Tabela destino:

`app.fato_curva_mercado_categoria`

Modelo:

`modelos_importacao/modelo_curva_mercado_categoria.xlsx`

### Colunas obrigatórias

- `data_competencia`
- `uf`
- `microrregiao`
- `categoria`
- `valor`
- `volume`

### Colunas opcionais

- `cidade`
- `produto`
- `preco_medio`
- `fonte`

### Regra de cálculo

Se `preco_medio` vier vazio:

`preco_medio = valor / volume`

### Uso no app

- Evolução por categoria.
- Curva de mercado.
- Análise por microrregião.
- Análise por produto/categoria.

---

## 3. Key Account / Lojas

Tabela destino:

`app.dim_key_account_loja`

Modelo:

`modelos_importacao/modelo_key_account_lojas.xlsx`

### Colunas obrigatórias

- `grupo_key_account`
- `loja`
- `cidade`
- `uf`

### Colunas opcionais

- `cliente`
- `cnpj`
- `endereco`
- `numero`
- `bairro`
- `cep`
- `latitude`
- `longitude`
- `canal`
- `status`

### Uso no app

- Lojas Key Account.
- Mapa comercial.
- Cobertura por cidade/UF.
- Cruzamento com IBGE.
- Densidade de lojas por população.

### Observação

Se latitude e longitude não forem informadas, o cruzamento inicial será feito por:

`cidade + uf`

---

## 4. Receita / Vendas Expansão

Tabela destino:

`app.fato_receita_manual_expansao`

Modelo:

`modelos_importacao/modelo_receita_vendas_expansao.xlsx`

### Colunas obrigatórias

- `parceiro`
- `cidade`
- `estado`
- `data_competencia`
- `grupo_produto`
- `vlr_total_liquido`

### Colunas opcionais

- `produto`
- `categoria`
- `vendedor`
- `canal`
- `quantidade`
- `preco_medio`

### Uso no app

- Receita por categoria.
- Receita média últimos 12 meses.
- Última venda por região.
- Status de receita.
- Comparação IDC x receita real.

### Regra de status

Se a região não tiver venda nos últimos 12 meses:

`Sem venda nos últimos 12 meses`

---

## 5. Compra Manual

Tabela destino:

`app.fato_compra_manual`

Modelo:

`modelos_importacao/modelo_compra_manual.xlsx`

### Colunas obrigatórias

- `data_competencia`
- `produto`
- `preco_compra`

### Colunas opcionais

- `fornecedor`
- `marca`
- `categoria`
- `quantidade`
- `valor_total`
- `cidade`
- `uf`
- `unidade`

### Regra de cálculo

Se `valor_total` vier vazio e existir quantidade:

`valor_total = quantidade * preco_compra`

### Uso no app

- Preço real de compra.
- Comparativo com CEPEA.
- Comparativo com CEAGESP.
- Análise de margem e custo.

---

## 6. CEAGESP Manual

Tabela destino:

`app.fato_ceagesp_pescados`

Modelo:

`modelos_importacao/modelo_ceagesp_pescados.xlsx`

### Colunas obrigatórias

- `data_cotacao`
- `produto`
- `preco_comum`

### Colunas opcionais

- `classificacao`
- `unidade`
- `preco_min`
- `preco_max`
- `fonte`

### Uso no app

- Cotação CEAGESP.
- Comparação CEPEA x CEAGESP.
- Histórico de preço de pescado.
- Referência de mercado.

---

## 7. Prévia Vendedores

Tabela destino:

`app.fato_previa_vendedores`

Modelo:

`modelos_importacao/modelo_previa_vendedores.xlsx`

### Colunas obrigatórias

- `vendedor`
- `produto`
- `preco`
- `quantidade`
- `receita`

### Colunas opcionais

- `data_venda`
- `cliente`
- `cidade`
- `uf`
- `categoria`
- `status`

### Regra de cálculo

Se `receita` vier vazia:

`receita = preço * quantidade`

### Uso no app

- Pipeline comercial.
- Projeção de vendas.
- Prévia por vendedor.
- Comparação com potencial IDC.

---

# Modos de importação

## Adicionar

Mantém os dados antigos e adiciona novos registros.

Regras:

- Não apaga histórico.
- Ignora duplicados pelo `hash_linha`.
- Ideal para cargas incrementais.

## Substituir período

Apaga os dados do período contido no arquivo e insere novamente.

Regras:

- Usa a menor e maior data do arquivo.
- Remove dados daquele intervalo.
- Insere a nova versão.
- Ideal para corrigir bases já carregadas.

---

# Regras técnicas obrigatórias

Toda importação deve:

1. Normalizar nomes de colunas.
2. Validar colunas obrigatórias.
3. Converter datas.
4. Converter números.
5. Padronizar UF em maiúsculo.
6. Gerar `hash_linha`.
7. Salvar na tabela destino.
8. Registrar log em `app.importacao_manual_log`.
9. Registrar rejeições em `app.importacao_manual_rejeicoes`.
10. Nunca depender somente da sessão do Streamlit.

---

# Modelos Excel

Os modelos ficam na pasta:

`modelos_importacao`

Arquivos disponíveis:

- `modelo_scanntech_mercado_privado.xlsx`
- `modelo_curva_mercado_categoria.xlsx`
- `modelo_key_account_lojas.xlsx`
- `modelo_receita_vendas_expansao.xlsx`
- `modelo_compra_manual.xlsx`
- `modelo_ceagesp_pescados.xlsx`
- `modelo_previa_vendedores.xlsx`

Esses arquivos devem ser mantidos no GitHub para que o app consiga disponibilizar download ao usuário.

---

# Status atual

Estrutura esperada:

- `app.importacao_manual_log`
- `app.importacao_manual_rejeicoes`
- `app.fato_mercado_privado`
- `app.fato_curva_mercado_categoria`
- `app.dim_key_account_loja`
- `app.fato_receita_manual_expansao`
- `app.fato_compra_manual`
- `app.fato_ceagesp_pescados`
- `app.fato_previa_vendedores`

Todas as bases manuais devem ser tratadas como fonte persistente no Supabase/PostgreSQL.
