from pathlib import Path
import py_compile
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]

REQUIRED = [
    "app.py",
    "requirements.txt",
    ".env.example",
    "src/config/settings.py",
    "src/database/connection.py",
    "scripts/testar_conexao.py",
]

def main():
    print("Validando estrutura do projeto...")
    ok = True

    for rel in REQUIRED:
        p = ROOT_DIR / rel
        if p.exists():
            print(f"OK   {rel}")
        else:
            print(f"ERRO {rel}")
            ok = False

    print("\nValidando sintaxe Python...")
    for py in ROOT_DIR.rglob("*.py"):
        if ".venv" in py.parts or "__pycache__" in py.parts:
            continue
        try:
            py_compile.compile(str(py), doraise=True)
        except Exception as e:
            print(f"ERRO {py.relative_to(ROOT_DIR)}: {e}")
            ok = False

    if not ok:
        print("\n❌ Projeto com erro.")
        return 1

    print("\n✅ Projeto pronto para rodar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
