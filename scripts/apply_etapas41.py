from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.database.connection import execute_sql_file

def localizar_sql_etapa41():
    db_dir = ROOT_DIR / "src" / "database"

    candidatos = []
    for path in db_dir.glob("*.sql"):
        txt = path.read_text(encoding="utf-8", errors="ignore")
        nome = path.name.lower()

        if (
            "vw_idc_completo_atual" in txt
            or "fato_mercado_privado" in txt
            or "idc planejado" in txt.lower()
            or "etapa41" in nome
            or "etapas41" in nome
        ):
            candidatos.append(path)

    if not candidatos:
        encontrados = "\n".join(p.name for p in db_dir.glob("*.sql"))
        raise FileNotFoundError(
            "Não encontrei o SQL da Etapa 41. Arquivos SQL encontrados:\n"
            + encontrados
        )

    candidatos = sorted(
        candidatos,
        key=lambda p: (
            0 if "41" in p.name.lower() else 1,
            0 if "vw_idc_completo_atual" in p.read_text(encoding="utf-8", errors="ignore") else 1,
            p.name
        )
    )

    return candidatos[0]

def main():
    sql_path = localizar_sql_etapa41()
    print(f"SQL Etapa 41 usado: {sql_path}")

    execute_sql_file(str(sql_path))

    hotfix = ROOT_DIR / "scripts" / "hotfix_vw_idc_demografia_faixas.py"
    if hotfix.exists():
        import subprocess
        subprocess.run([sys.executable, str(hotfix)], check=True)
    print("✅ Etapa 41 aplicada: importações persistentes, proxies controlados e IDC planejado.")

if __name__ == "__main__":
    main()
