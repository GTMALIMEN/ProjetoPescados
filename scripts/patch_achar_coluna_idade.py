from pathlib import Path
import re

path = Path("scripts/run_censo_2022_idade_faixas_fix.py")
txt = path.read_text(encoding="utf-8")

nova_funcao = r'''
def achar_coluna(header, termo, preferir_codigo=False):
    termo_norm = normalizar_texto(termo)

    # Evita falso positivo: "Unidade de Medida" contém "idade"
    ignorar = {
        "nivel territorial",
        "unidade de medida",
        "variavel",
        "ano",
        "valor",
    }

    candidatos = []

    for k, v in header.items():
        nome = normalizar_texto(v)

        if any(x in nome for x in ignorar):
            continue

        if termo_norm == "idade":
            if nome.startswith("idade"):
                candidatos.append((k, nome))
        elif termo_norm == "sexo":
            if nome.startswith("sexo"):
                candidatos.append((k, nome))
        elif termo_norm == "municipio":
            if "municipio" in nome:
                candidatos.append((k, nome))
        else:
            if termo_norm in nome:
                candidatos.append((k, nome))

    if not candidatos:
        return None

    if preferir_codigo:
        for k, nome in candidatos:
            if "codigo" in nome:
                return k
    else:
        for k, nome in candidatos:
            if "codigo" not in nome:
                return k

    return candidatos[0][0]
'''

txt2 = re.sub(
    r"def achar_coluna\(header, termo, preferir_codigo=False\):.*?\n\ndef idade_intervalo",
    nova_funcao + "\n\ndef idade_intervalo",
    txt,
    flags=re.S
)

if txt2 == txt:
    raise RuntimeError("Não consegui substituir a função achar_coluna.")

path.write_text(txt2, encoding="utf-8")
print("✅ Função achar_coluna corrigida: agora não confunde 'Unidade de Medida' com 'Idade'.")
