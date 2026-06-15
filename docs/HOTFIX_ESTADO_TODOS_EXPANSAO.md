# Hotfix — opção Todos na Análise de Expansão

## Ajuste

Foi adicionada a opção:

```text
Todos
```

no seletor **Estado base** da aba:

```text
🌎 Análise de Expansão
```

## Comportamento

```text
Todos → carrega MG, SP, RJ e ES juntos
MG → carrega somente MG
SP → carrega somente SP
RJ → carrega somente RJ
ES → carrega somente ES
```

## Mapa comercial/econômico simplificado

```text
MG → usa o mapa comercial MG
Todos/SP/RJ/ES → usa treemap econômico por estado e região econômica
```

## Arquivo alterado

```text
app.py
```

## Como validar

```bat
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Na aba **🌎 Análise de Expansão**, testar:

```text
Estado base = Todos
Estado base = MG
Estado base = SP
Estado base = RJ
Estado base = ES
```
