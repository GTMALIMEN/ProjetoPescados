# Hotfix — NameError carregar_base_compra_resumo

## Erro

```text
NameError: name 'carregar_base_compra_resumo' is not defined
```

## Causa

A tela **Análise Previsão de Mercado** passou a chamar a função de resumo da base de compra, mas o `app.py` pode não ter importado a função dependendo da versão anterior do arquivo.

## Correção aplicada

Foi adicionado fallback no `app.py`:

```text
carregar_base_compra_resumo()
carregar_previa_vendedores_resumo()
```

Assim, se a base ainda não existir, o app mostra dataframe vazio em vez de quebrar.

## Observação

Esse erro não era causado pela ausência da base.  
Era causado por função não importada/definida.
