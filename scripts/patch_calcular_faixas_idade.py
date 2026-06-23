from pathlib import Path
import re

path = Path("scripts/run_censo_2022_idade_faixas_fix.py")
txt = path.read_text(encoding="utf-8")

nova_funcao = r'''
def calcular_faixas(df):
    df = df.copy()
    df["sexo_norm"] = df["sexo"].map(normalizar_texto)
    df["idade_norm"] = df["idade"].map(normalizar_texto)

    resultados = []

    for codigo, g in df.groupby("codigo_ibge"):
        municipio = g["municipio"].dropna().astype(str).iloc[0]

        idade_total = g["idade_norm"].eq("total")
        sexo_total = g["sexo_norm"].eq("total")
        sexo_masc = g["sexo_norm"].isin(["homens", "homem", "masculino"])
        sexo_fem = g["sexo_norm"].isin(["mulheres", "mulher", "feminino"])

        # 1) Preferência: usar idade detalhada com sexo Total.
        base_idade = g[sexo_total & ~idade_total].copy()

        # 2) Se não vier sexo Total, soma Homens + Mulheres por idade.
        if base_idade.empty or base_idade["valor"].sum() <= 0:
            base_idade = g[(sexo_masc | sexo_fem) & ~idade_total].copy()

            if not base_idade.empty:
                base_idade = (
                    base_idade
                    .groupby(["idade", "idade_norm"], as_index=False)["valor"]
                    .sum()
                )

        # 3) Último fallback: usa qualquer idade detalhada, mas evita linha Total.
        if base_idade.empty or base_idade["valor"].sum() <= 0:
            base_idade = g[~idade_total].copy()

            if not base_idade.empty:
                base_idade = (
                    base_idade
                    .groupby(["idade", "idade_norm"], as_index=False)["valor"]
                    .max()
                )

        total = g[sexo_total & idade_total]["valor"].sum()

        if total <= 0:
            total = base_idade["valor"].sum()

        if total <= 0 or base_idade.empty:
            continue

        faixas = {
            "pop_0_14": 0.0,
            "pop_15_29": 0.0,
            "pop_30_44": 0.0,
            "pop_45_59": 0.0,
            "pop_60_plus": 0.0,
        }

        for _, row in base_idade.iterrows():
            intervalo = idade_intervalo(row["idade"])

            if intervalo is None:
                continue

            dist = distribuir_faixa(row["valor"], intervalo[0], intervalo[1])

            for k, v in dist.items():
                faixas[k] += v

        soma_faixas = sum(faixas.values())

        if soma_faixas <= 0:
            continue

        resultados.append({
            "codigo_ibge": str(codigo),
            "municipio": municipio,
            "populacao_idade": total,
            "pop_0_14": faixas["pop_0_14"],
            "pop_15_29": faixas["pop_15_29"],
            "pop_30_44": faixas["pop_30_44"],
            "pop_45_59": faixas["pop_45_59"],
            "pop_60_plus": faixas["pop_60_plus"],
            "pct_0_14": faixas["pop_0_14"] / total * 100,
            "pct_15_29": faixas["pop_15_29"] / total * 100,
            "pct_30_44": faixas["pop_30_44"] / total * 100,
            "pct_45_59": faixas["pop_45_59"] / total * 100,
            "pct_60_plus": faixas["pop_60_plus"] / total * 100,
        })

    return pd.DataFrame(resultados)
'''

txt2 = re.sub(
    r"def calcular_faixas\(df\):.*?\n\ndef coletar_idade_municipio",
    nova_funcao + "\n\ndef coletar_idade_municipio",
    txt,
    flags=re.S
)

if txt2 == txt:
    raise RuntimeError("Não consegui substituir a função calcular_faixas. Verifique o arquivo.")

path.write_text(txt2, encoding="utf-8")
print("✅ Função calcular_faixas corrigida para usar Total ou Homens+Mulheres.")
