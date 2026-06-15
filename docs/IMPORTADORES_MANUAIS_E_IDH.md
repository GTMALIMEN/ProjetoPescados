# Importadores manuais e fonte de IDH/IDHM

## Criar templates

```bat
python scripts\criar_templates_importacao.py
```

Os templates serão criados em `data/templates`:

- `ceagesp_manual.csv`
- `base_compra_manual.csv`
- `previa_vendedores.csv`
- `idh_municipal.csv`

## Cargas

```bat
python scripts\load_ceagesp_manual_file.py --arquivo "data\input\ceagesp_manual.csv"
python scripts\load_compra_manual_file.py --arquivo "data\input\base_compra.csv"
python scripts\load_previa_vendedores_file.py --arquivo "data\input\previa_vendedores.csv"
python scripts\load_idh_file.py --arquivo "data\input\idh_municipal.csv"
```

## IDH/IDHM

Fonte recomendada: Atlas do Desenvolvimento Humano no Brasil, parceria IPEA/PNUD/Fundação João Pinheiro.

Use preferencialmente as colunas:

```text
codigo_ibge
uf
municipio
idhm
ano
fonte
```

O importador atualiza:

```text
app.fato_expansao_municipio.idh
app.fato_expansao_municipio.fonte_idh
```

## Próximas fontes

- Demografia por sexo/faixa etária: Censo 2022/SIDRA, tabela 9514.
- PDV: base interna, CNPJ/CNAE, OpenStreetMap ou Google Places.
- Renda por classe: POF/Censo quando houver recorte confiável.
