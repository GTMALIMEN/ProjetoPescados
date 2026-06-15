
from __future__ import annotations

from pathlib import Path
import sys
import json
import time
import tempfile
from datetime import date

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.etl.load_fontes_reais import carregar_comex_pescados


def _load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_temp_config(base_cfg: dict, group_name: str, group_cfg: dict) -> Path:
    cfg = {
        "flow": base_cfg.get("flow", "import"),
        "month_detail": base_cfg.get("month_detail", True),
        "currency": base_cfg.get("currency", "USD"),
        "groups": {group_name: group_cfg},
    }
    tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(cfg, tmp, ensure_ascii=False, indent=2)
    tmp.close()
    return Path(tmp.name)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Etapa 26 — Comex Stat refinado por ano/grupo, com backoff e logs separados")
    parser.add_argument("--ano-inicio", type=int, default=2020)
    parser.add_argument("--ano-fim", type=int, default=date.today().year)
    parser.add_argument("--config", default="config/comex_pescados_ncm.json")
    parser.add_argument("--delay", type=int, default=12)
    parser.add_argument("--max-tentativas", type=int, default=2)
    args = parser.parse_args()

    config_path = ROOT_DIR / args.config
    base_cfg = _load_config(config_path)
    grupos = list(base_cfg.get("groups", {}).items())

    ano_fim = min(int(args.ano_fim), date.today().year)
    anos = list(range(int(args.ano_inicio), ano_fim + 1))

    print("Comex Stat refinado")
    print(f"- anos: {anos}")
    print(f"- grupos: {[g for g, _ in grupos]}")
    print("- consulta é separada por ano/grupo para reduzir erro e melhorar log.")

    total_ok = 0
    total_falha = 0

    for ano in anos:
        for group_name, group_cfg in grupos:
            tentativa = 0
            ok = False
            while tentativa < args.max_tentativas and not ok:
                tentativa += 1
                tmp_cfg = _write_temp_config(base_cfg, group_name, group_cfg)
                try:
                    print(f"\n🔎 Ano={ano} | Grupo={group_name} | tentativa={tentativa}/{args.max_tentativas}")
                    carregar_comex_pescados(
                        ano_inicio=ano,
                        ano_fim=ano,
                        config_path=str(tmp_cfg),
                        delay_entre_grupos=0,
                    )
                    ok = True
                    total_ok += 1
                except Exception as exc:
                    total_falha += 1 if tentativa == args.max_tentativas else 0
                    msg = str(exc)
                    print(f"⚠️ Falha Comex | ano={ano} | grupo={group_name} | tentativa={tentativa}: {msg[:500]}")
                    wait = args.delay * tentativa
                    if "429" in msg or "limite" in msg.lower() or "rate" in msg.lower():
                        wait = max(wait, 20)
                    if tentativa < args.max_tentativas:
                        print(f"⏳ Aguardando {wait}s antes da nova tentativa...")
                        time.sleep(wait)
                finally:
                    try:
                        tmp_cfg.unlink(missing_ok=True)
                    except Exception:
                        pass

            if args.delay > 0:
                time.sleep(args.delay)

    print("\nResumo Comex refinado")
    print(f"- execuções com sucesso: {total_ok}")
    print(f"- execuções com falha final: {total_falha}")
    print("Veja o status atual em app.vw_comex_stat_status_atual e os logs separados em:")
    print("- app.vw_fontes_reais_cargas_sucesso")
    print("- app.vw_fontes_reais_cargas_erro")


if __name__ == "__main__":
    main()
