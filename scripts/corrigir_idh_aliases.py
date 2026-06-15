
from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path
import re
import sys
import unicodedata

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


ALIASES = {
    ("MG", "Barão do Monte Alto"): ["Barão de Monte Alto", "Barao de Monte Alto", "Barao do Monte Alto"],
    ("MG", "Brazópolis"): ["Brasópolis", "Brasopolis", "Brazopolis"],
    ("MG", "Coronel Pacheco"): ["Coronel Pacheco"],
    ("MG", "Dona Euzébia"): ["Dona Eusébia", "Dona Eusebia", "Dona Euzebia"],
    ("MG", "São Tomé das Letras"): ["São Thomé das Letras", "Sao Thome das Letras", "Sao Tome das Letras"],
    ("SP", "Embu das Artes"): ["Embu", "Embu das Artes"],
    ("SP", "Florínea"): ["Florinea", "Florínea"],
    ("SP", "São Luiz do Paraitinga"): ["São Luís do Paraitinga", "Sao Luis do Paraitinga", "Sao Luiz do Paraitinga"],
}


def norm(value: str) -> str:
    value = "" if value is None or pd.isna(value) else str(value)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = value.replace(" d ", " de ")
    value = value.replace(" do ", " de ")
    value = value.replace(" da ", " de ")
    value = value.replace(" das ", " de ")
    value = value.replace(" dos ", " de ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def score(a: str, b: str) -> float:
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def main():
    engine = get_engine()

    with engine.begin() as conn:
        missing = pd.read_sql(text("""
            SELECT uf, municipio, codigo_ibge, microrregiao, regiao_comercial
            FROM app.vw_expansao_municipio
            WHERE uf IN ('MG','SP','RJ','ES')
              AND idh IS NULL
            ORDER BY uf, municipio
        """), conn)

        idh = pd.read_sql(text("""
            SELECT codigo_ibge AS idh_codigo_ibge, municipio AS idh_municipio, uf,
                   ano, idhm, idhm_renda, idhm_longevidade, idhm_educacao, fonte, url_fonte
            FROM app.fato_idhm_municipal
            WHERE uf IN ('MG','SP','RJ','ES')
              AND idhm IS NOT NULL
        """), conn)

    if missing.empty:
        print("✅ Não há municípios sem IDH na expansão.")
        return

    if idh.empty:
        print("❌ app.fato_idhm_municipal está vazia. Rode primeiro:")
        print(r".\.venv\Scripts\python.exe scripts\run_idh_automatico.py")
        return

    idh = idh.copy()
    idh["idh_norm"] = idh["idh_municipio"].map(norm)

    matches = []
    unresolved = []

    for _, m in missing.iterrows():
        uf = m["uf"]
        municipio = m["municipio"]
        candidates = idh[idh["uf"] == uf].copy()

        if candidates.empty:
            unresolved.append({**m.to_dict(), "motivo": "sem candidatos na UF"})
            continue

        alias_list = [municipio] + ALIASES.get((uf, municipio), [])
        alias_norms = {norm(x) for x in alias_list}

        exact = candidates[candidates["idh_norm"].isin(alias_norms)]
        if not exact.empty:
            best = exact.iloc[0].to_dict()
            best_score = 1.0
        else:
            candidates["match_score"] = candidates["idh_municipio"].apply(lambda x: max(score(x, a) for a in alias_list))
            candidates = candidates.sort_values("match_score", ascending=False)
            top = candidates.iloc[0]
            best_score = float(top["match_score"])
            if best_score >= 0.88:
                best = top.to_dict()
            else:
                unresolved.append({
                    **m.to_dict(),
                    "melhor_candidato": top["idh_municipio"],
                    "score": round(best_score, 4),
                    "motivo": "score baixo",
                })
                continue

        matches.append({
            "uf": uf,
            "municipio": municipio,
            "codigo_ibge": m["codigo_ibge"],
            "idh_municipio": best["idh_municipio"],
            "idh_codigo_ibge": best["idh_codigo_ibge"],
            "ano": int(best["ano"] or 2010),
            "idhm": best["idhm"],
            "idhm_renda": best["idhm_renda"],
            "idhm_longevidade": best["idhm_longevidade"],
            "idhm_educacao": best["idhm_educacao"],
            "fonte": best["fonte"],
            "url_fonte": best["url_fonte"],
            "score": best_score,
        })

    if matches:
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE app.fato_expansao_municipio e
                SET idh = :idhm,
                    idhm_ano = :ano,
                    idhm_renda = :idhm_renda,
                    idhm_longevidade = :idhm_longevidade,
                    idhm_educacao = :idhm_educacao,
                    fonte_idh = :fonte || ' (' || :ano || ') - alias/fuzzy: ' || :idh_municipio,
                    data_atualizacao = NOW()
                WHERE e.codigo_ibge = :codigo_ibge
            """), matches)

    print("\nCorreção IDH por alias/fuzzy")
    print(f"- municípios sem IDH antes: {len(missing)}")
    print(f"- corrigidos: {len(matches)}")
    print(f"- não resolvidos: {len(unresolved)}")

    if matches:
        print("\nCorrigidos:")
        print(pd.DataFrame(matches)[[
            "uf", "municipio", "codigo_ibge", "idh_municipio", "idhm", "score"
        ]].to_string(index=False))

    if unresolved:
        print("\nAinda não resolvidos:")
        print(pd.DataFrame(unresolved).to_string(index=False))


if __name__ == "__main__":
    main()
