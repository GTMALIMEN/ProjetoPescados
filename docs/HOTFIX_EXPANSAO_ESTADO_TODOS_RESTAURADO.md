# Hotfix — Restaurar opção Todos na Análise de Expansão

## Ajuste

A opção **Todos** foi restaurada no seletor:

```text
Estado base
```

na aba:

```text
🌎 Análise de Expansão
```

## Comportamento

```text
Todos → carrega MG, SP, RJ e ES juntos
MG → somente MG
SP → somente SP
RJ → somente RJ
ES → somente ES
```

## Mapa

```text
MG → mapa comercial simplificado de MG
Todos/SP/RJ/ES → treemap econômico simplificado por estado/região
```

## Validação

Ao abrir o app, o seletor deve exibir:

```text
Todos
MG
SP
RJ
ES
```

## Caso o ZIP não substitua o app.py local

Rode o hotfix direto:

```bat
.\.venv\Scripts\python.exe scripts\hotfix_expansao_estado_todos.py
```

Depois reinicie o Streamlit.
