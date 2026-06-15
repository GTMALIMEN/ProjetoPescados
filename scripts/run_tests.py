from pathlib import Path
import subprocess
import sys
import os

ROOT_DIR = Path(__file__).resolve().parents[1]


def main():
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    cmd = [sys.executable, "-m", "pytest", "-q"]

    print("Executando testes:")
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
