
import re
import unicodedata


def slug_texto(valor: object) -> str:
    texto = str(valor or "").strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


ALIAS_PRODUTOS = {
    "TILAPIA": [
        "tilapia",
        "TILAPIA",
        "tilápia",
        "TILÁPIA",
        "til?pia",
        "TIL?PIA",
        "file tilapia",
        "FILE TILAPIA",
        "file de tilapia",
        "FILE DE TILAPIA",
        "filé tilápia",
        "FILÉ TILÁPIA",
        "fil? til?pia",
        "FIL? TIL?PIA",
        "filé de tilápia",
        "FILÉ DE TILÁPIA",
        "fil? de til?pia",
        "FIL? DE TIL?PIA",
        "tilapia inteira",
        "TILAPIA INTEIRA",
        "tilápia inteira",
        "TILÁPIA INTEIRA",
        "til?pia inteira",
        "TIL?PIA INTEIRA",
    ],

    "SALMAO": [
        "salmao",
        "SALMAO",
        "salmão",
        "SALMÃO",
        "salm?o",
        "SALM?O",
        "file salmao",
        "FILE SALMAO",
        "file de salmao",
        "FILE DE SALMAO",
        "filé salmão",
        "FILÉ SALMÃO",
        "fil? salm?o",
        "FIL? SALM?O",
        "filé de salmão",
        "FILÉ DE SALMÃO",
        "fil? de salm?o",
        "FIL? DE SALM?O",
    ],

    "CAMARAO": [
        "camarao",
        "CAMARAO",
        "camarão",
        "CAMARÃO",
        "camar?o",
        "CAMAR?O",
        "camarao cativeiro",
        "CAMARAO CATIVEIRO",
        "camarão cativeiro",
        "CAMARÃO CATIVEIRO",
        "camar?o cativeiro",
        "CAMAR?O CATIVEIRO",
        "camarao rosa",
        "CAMARAO ROSA",
        "camarao cinza",
        "CAMARAO CINZA",
        "camarao sete barbas",
        "CAMARAO SETE BARBAS",
        "camarao 7 barbas",
        "CAMARAO 7 BARBAS",
        "camarao inteiro",
        "CAMARAO INTEIRO",
        "camarao descascado",
        "CAMARAO DESCASCADO",
    ],

    "PIRAMUTABA": [
        "piramutaba",
        "PIRAMUTABA",
        "pira mutaba",
        "PIRA MUTABA",
    ],

    "POLACA": [
        "polaca",
        "POLACA",
        "polaca do alasca",
        "POLACA DO ALASCA",
        "polaca alasca",
        "POLACA ALASCA",
    ],

    "MERLUZA": [
        "merluza",
        "MERLUZA",
        "file merluza",
        "FILE MERLUZA",
        "file de merluza",
        "FILE DE MERLUZA",
        "filé merluza",
        "FILÉ MERLUZA",
        "fil? merluza",
        "FIL? MERLUZA",
        "filé de merluza",
        "FILÉ DE MERLUZA",
        "fil? de merluza",
        "FIL? DE MERLUZA",
    ],

    "PANGA": [
        "panga",
        "PANGA",
        "pangasius",
        "PANGASIUS",
        "peixe panga",
        "PEIXE PANGA",
        "file panga",
        "FILE PANGA",
        "file de panga",
        "FILE DE PANGA",
        "filé panga",
        "FILÉ PANGA",
        "fil? panga",
        "FIL? PANGA",
        "filé de panga",
        "FILÉ DE PANGA",
        "fil? de panga",
        "FIL? DE PANGA",
    ],

    "OUTROS PEIXES": [
        "peixes para",
        "PEIXES PARA",
        "peixe para",
        "PEIXE PARA",
        "outros peixes",
        "OUTROS PEIXES",
        "outros pescados",
        "OUTROS PESCADOS",
        "pescados diversos",
        "PESCADOS DIVERSOS",
    ],
}

_ALIAS_INDEX = {}

for produto_padrao, aliases in ALIAS_PRODUTOS.items():
    _ALIAS_INDEX[slug_texto(produto_padrao)] = produto_padrao
    for alias in aliases:
        _ALIAS_INDEX[slug_texto(alias)] = produto_padrao


def normalizar_produto(valor: object) -> str:
    slug = slug_texto(valor)

    if not slug:
        return "N/A"

    if slug in _ALIAS_INDEX:
        return _ALIAS_INDEX[slug]

    for alias_slug, produto_padrao in _ALIAS_INDEX.items():
        if alias_slug and alias_slug in slug:
            return produto_padrao

    return str(valor or "").strip().title()


def normalizar_coluna_produto(df, origem="grupo_produto", destino="categoria_pescado"):
    df = df.copy()

    if origem in df.columns:
        df[destino] = df[origem].apply(normalizar_produto)
    elif destino in df.columns:
        df[destino] = df[destino].apply(normalizar_produto)

    return df
