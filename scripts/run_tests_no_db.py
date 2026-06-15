from pathlib import Path
import subprocess
import sys
import os

ROOT_DIR = Path(__file__).resolve().parents[1]


def main():
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/test_project_structure.py",
        "tests/test_math_rules.py",
        "tests/test_whatif_rules.py",
        "tests/test_config_files.py",
    ]

    print("Executando testes sem banco:")
    print(" ".join(cmd))

    result = subprocess.run(
        cmd,
        cwd=ROOT_DIR,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
