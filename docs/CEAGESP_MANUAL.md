
# CEAGESP Manual

## Decisão

A CEAGESP passa a ser **manual/controlada** no projeto.

Motivo: a página pública exige interação com formulário e não retornou a tabela de forma estável via `requests` nem via navegador automatizado no ambiente local.

## Fluxo

1. Aplicar estrutura:

```bat
python scripts\apply_ceagesp_manual.py
```

2. Criar template:

```bat
python scripts\criar_template_ceagesp_manual.py
```

3. Editar:

```text
data/input/ceagesp_manual.csv
```

4. Carregar:

```bat
python scripts\load_ceagesp_manual_file.py --arquivo "data\input\ceagesp_manual.csv"
```

5. Validar:

```bat
python scripts\diagnosticar_v2_plano.py
```

## Colunas aceitas

Obrigatórias:

```text
data_referencia
produto
preco_comum
```

Recomendadas:

```text
classificacao
unidade
preco_minimo
preco_maximo
fonte
url_fonte
observacao
```

## Exemplo

```csv
data_referencia;produto;classificacao;unidade;preco_minimo;preco_comum;preco_maximo;fonte;url_fonte;observacao
10/06/2026;Tilápia;Inteira;kg;12,00;14,50;17,00;CEAGESP Manual;https://ceagesp.gov.br/cotacoes/;cotação digitada manualmente
```

## Observação

A tabela mantém histórico. Se carregar o mesmo produto/data/classificação/unidade novamente, ela atualiza o registro em vez de duplicar.
