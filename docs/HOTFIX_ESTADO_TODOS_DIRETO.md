# Hotfix direto — Estado base = Todos

Este hotfix altera o `app.py` local diretamente e adiciona a opção **Todos** no seletor **Estado base** da aba **Análise de Expansão**.

## Como rodar

```bat
scripts\hotfix_estado_todos_direto.bat
```

Ou manualmente:

```bat
.\.venv\Scripts\python.exe scripts\hotfix_estado_todos_direto.py
```

Depois pare o Streamlit com `CTRL+C` e abra de novo:

```bat
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Resultado esperado

O seletor deve mostrar:

```text
Todos
MG
SP
RJ
ES
```

Quando escolher **Todos**, o app usa:

```text
MG + SP + RJ + ES
```
