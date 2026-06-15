
# Rodar tudo — Etapa 23

## Comando principal

```bat
scripts\rodar_tudo_etapa23.bat
```

Esse script faz:

```text
1. verifica/recria .venv com Python 3.12
2. instala requirements
3. valida estrutura da Etapa 23
4. inicializa banco
5. aplica fontes automáticas
6. aplica CEAGESP manual
7. aplica Expansão V2 pública
8. aplica Regiões MG
9. carrega IBGE Localidades
10. carrega IBGE População
11. carrega Expansão Sudeste
12. carrega IDH automático
13. preenche IDH faltante via fallback IBGE/PNUD
14. cria template CEAGESP manual
15. carrega arquivos manuais se existirem
16. roda diagnóstico final
17. abre Streamlit
```

## Comando para abrir app depois de tudo pronto

```bat
scripts\abrir_app_etapa23.bat
```

## Arquivos manuais opcionais

```text
data/input/ceagesp_manual.csv
data/input/base_compra_manual.csv
data/input/previa_vendedores.csv
data/input/cepea_tilapia.xlsx
data/input/conab_precos_milho_soja.xlsx
```

Se não existirem, o script pula e continua.

## Importante

Se `data/input/ceagesp_manual.csv` estiver apenas com os exemplos do template, edite antes de usar em produção.
