from pathlib import Path
import sys
import json

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.services.whatif_service import WhatIfParams, simular_regiao


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Simular cenário What-if")
    parser.add_argument("--uf", default="MG")
    parser.add_argument("--regiao", required=True)
    parser.add_argument("--nome", default="Simulação CLI")
    parser.add_argument("--salvar", action="store_true")

    parser.add_argument("--dolar", type=float, default=0)
    parser.add_argument("--tilapia", type=float, default=0)
    parser.add_argument("--frango", type=float, default=0)
    parser.add_argument("--bovino", type=float, default=0)
    parser.add_argument("--suino", type=float, default=0)
    parser.add_argument("--graos", type=float, default=0)

    parser.add_argument("--campanha", action="store_true")
    parser.add_argument("--vendedor", action="store_true")
    parser.add_argument("--promotor", action="store_true")
    parser.add_argument("--cobertura", type=float, default=0)
    parser.add_argument("--mix-premium", type=float, default=0)

    args = parser.parse_args()

    params = WhatIfParams(
        variacao_dolar_pct=args.dolar,
        variacao_tilapia_pct=args.tilapia,
        variacao_frango_pct=args.frango,
        variacao_bovino_pct=args.bovino,
        variacao_suino_pct=args.suino,
        variacao_graos_pct=args.graos,
        campanha_marketing=args.campanha,
        adicionar_vendedor=args.vendedor,
        adicionar_promotor=args.promotor,
        melhorar_cobertura_pct=args.cobertura,
        aumentar_mix_premium_pct=args.mix_premium,
    )

    resultado = simular_regiao(
        uf=args.uf,
        regiao_comercial=args.regiao,
        params=params,
        salvar=args.salvar,
        nome_cenario=args.nome,
    )

    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
