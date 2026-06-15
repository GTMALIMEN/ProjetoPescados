# Hotfix — Colormap dos mapas Folium

## Problema

O mapa do Brasil falhava com:

```text
'_LinearColormaps' object has no attribute 'Viridis_09'
```

## Causa

A versão instalada do `branca` usa `cm.linear.viridis`, enquanto o código chamava `cm.linear.Viridis_09`.

## Correção

Foi criado um helper compatível:

```python
_linear_colormap("viridis", vmin, vmax)
_linear_colormap("ylgnbu", vmin, vmax)
```

Ele tenta nomes diferentes e, se necessário, usa um fallback manual.

## Rodar

```bat
pip install -r requirements.txt
streamlit run app.py
```

Não precisa baixar novamente as malhas se o diagnóstico já mostrou:

```text
Brasil: 27 features
MG: 853 features
```
