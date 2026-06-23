# CEPEA Manual Oficial

## Objetivo

Usar uma tabela predefinida para carregar manualmente os preços oficiais da tilápia do CEPEA quando a coleta automática for bloqueada por Cloudflare/anti-bot.

A carga manual **não é proxy**. Ela só deve ser usada quando o valor foi copiado/baixado da página oficial do CEPEA.

## Arquivos

- Template CSV: `data/templates/cepea_manual.csv`
- Arquivo para preencher: `data/input/cepea_manual.csv`
- Modelo Excel: `modelos_importacao/modelo_cepea_manual.xlsx`
- Script de carga: `scripts/load_cepea_manual_file.py`
- Estrutura SQL: `src/database/cepea_manual.sql`

## Colunas obrigatórias

| Coluna | Descrição | Obrigatória |
|---|---|---|
| `data_fim_periodo` | Data final da semana CEPEA | Sim |
| `regiao_cepea` | Região/praça exibida no CEPEA | Sim |
| `preco_ajustado` / `PREÇO AJUSTADO` | Preço que o app usa no gráfico CEPEA | Sim |

## Colunas recomendadas

| Coluna | Descrição |
|---|---|
| `data_inicio_periodo` | Data inicial da semana CEPEA |
| `periodo_original` | Texto original do período, exemplo `15 - 19/06/2026` |
| `produto` | Normalmente `Tilápia` |
| `uf` | UF/região, exemplo `MG`, `PR`, `SP/MS` |
| `preco_rs_kg` | Campo legado opcional; quando vazio, recebe o mesmo valor de `preco_ajustado` |
| `variacao_semana_pct` | Variação semanal, se disponível |
| `unidade` | Normalmente `R$/kg` |
| `url_fonte` | URL da página CEPEA |
| `observacao` | Observação de conferência |

## Como criar o template

```powershell
python scripts\criar_template_cepea_manual.py
```

## Como carregar

```powershell
python scripts\load_cepea_manual_file.py --criar-estrutura --arquivo "data\input\cepea_manual.csv"
```

## Como o dado entra no banco

O app usa `preco_ajustado` como valor oficial publicado no gráfico. A carga grava em duas camadas:

1. `app.fato_cepea_tilapia_manual` — tabela auditável da carga manual.
2. `dw.fato_indicador_setorial` — tabela usada pelos gráficos do app.

No DW, a marcação fica assim:

```text
fonte = CEPEA
subcategoria = oficial_arquivo_manual
indicador = preco_tilapia_cepea_produtor_independente
periodicidade = semanal
unidade = R$/kg
```

## Regras de segurança

- Não preencher camarão como CEPEA.
- Não preencher preço de compra interna como CEPEA.
- Não preencher preço de varejo/filé como CEPEA.
- Não usar planilha proxy antiga com fonte `CEPEA`.
- Se o valor não veio do CEPEA, usar outra fonte: CEAGESP, Compra Manual, ComexStat ou base interna.
