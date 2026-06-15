from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


def clamp(value: float, min_value: float = 0, max_value: float = 100) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return float(max(min_value, min(max_value, value)))


def scenario_1_10(score: float) -> int:
    if score is None or pd.isna(score):
        return 1
    return max(1, min(10, math.ceil(float(score) / 10.0)))


def safe_float(value, default=0.0) -> float:
    if value is None or pd.isna(value):
        return default
    return float(value)


@dataclass
class WhatIfParams:
    variacao_dolar_pct: float = 0.0
    variacao_tilapia_pct: float = 0.0
    variacao_frango_pct: float = 0.0
    variacao_bovino_pct: float = 0.0
    variacao_suino_pct: float = 0.0
    variacao_graos_pct: float = 0.0
    campanha_marketing: bool = False
    adicionar_vendedor: bool = False
    adicionar_promotor: bool = False
    melhorar_cobertura_pct: float = 0.0
    aumentar_mix_premium_pct: float = 0.0


def carregar_regioes_scores(uf: str = "MG") -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            uf,
            regiao_comercial,
            score_final,
            score_oportunidade,
            score_risco,
            COALESCE(score_potencial, 50) AS score_potencial,
            COALESCE(score_setorial, 50) AS score_setorial,
            COALESCE(score_competitividade_setorial, 50) AS score_competitividade_setorial,
            COALESCE(score_pressao_custo_setorial, 50) AS score_pressao_custo_setorial,
            COALESCE(score_risco_substituicao_setorial, 50) AS score_risco_substituicao_setorial,
            cenario_1_10,
            confianca,
            metodo
        FROM app.mv_score_regional_atual
        WHERE uf = :uf
        ORDER BY score_final DESC
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"uf": uf})


def carregar_recomendacao_atual(uf: str, regiao_comercial: str) -> dict:
    engine = get_engine()
    sql = """
        SELECT
            tipo_recomendacao,
            acao_sugerida,
            motor_decisao
        FROM app.mv_recomendacao_atual
        WHERE uf = :uf
          AND regiao_comercial = :regiao_comercial
        LIMIT 1
    """
    with engine.begin() as conn:
        row = conn.execute(text(sql), {"uf": uf, "regiao_comercial": regiao_comercial}).mappings().first()
    return dict(row or {})


def calcular_competitividad_simulada(
    competitividade_atual: float,
    variacao_tilapia_pct: float,
    variacao_frango_pct: float,
    variacao_bovino_pct: float,
    variacao_suino_pct: float,
) -> float:
    """
    Heurística:
    - Se tilápia sobe, competitividade do pescado piora.
    - Se proteínas concorrentes caem, competitividade do pescado piora.
    - Se proteínas concorrentes sobem, competitividade melhora.
    """
    concorrentes_media = (variacao_frango_pct + variacao_bovino_pct + variacao_suino_pct) / 3.0

    impacto_tilapia = -1.20 * variacao_tilapia_pct
    impacto_concorrentes = 0.85 * concorrentes_media

    return clamp(competitividade_atual + impacto_tilapia + impacto_concorrentes)


def calcular_pressao_custo_simulada(
    pressao_atual: float,
    variacao_dolar_pct: float,
    variacao_graos_pct: float,
) -> float:
    impacto = (0.45 * max(variacao_dolar_pct, -20)) + (0.75 * max(variacao_graos_pct, -20))
    return clamp(pressao_atual + impacto)


def calcular_risco_substituicao_simulado(
    risco_atual: float,
    variacao_tilapia_pct: float,
    variacao_frango_pct: float,
    variacao_bovino_pct: float,
    variacao_suino_pct: float,
) -> float:
    # Pior cenário: pescado sobe e concorrentes caem.
    queda_concorrentes = max(-variacao_frango_pct, 0) * 1.20 + max(-variacao_bovino_pct, 0) * 0.55 + max(-variacao_suino_pct, 0) * 0.75
    alta_pescado = max(variacao_tilapia_pct, 0) * 1.10
    melhora_relativa = max(-variacao_tilapia_pct, 0) * 0.50 + max(variacao_frango_pct, 0) * 0.40

    return clamp(risco_atual + alta_pescado + queda_concorrentes - melhora_relativa)


def simular_regiao(
    uf: str,
    regiao_comercial: str,
    params: WhatIfParams | dict,
    salvar: bool = False,
    nome_cenario: str | None = None,
    usuario: str | None = None,
) -> dict:
    if isinstance(params, dict):
        params = WhatIfParams(**params)

    scores = carregar_regioes_scores(uf=uf)
    if scores.empty:
        raise ValueError("Nenhum score encontrado. Rode calculate_scores.py antes de simular.")

    row_df = scores[scores["regiao_comercial"] == regiao_comercial]
    if row_df.empty:
        raise ValueError(f"Região não encontrada: {regiao_comercial}")

    row = row_df.iloc[0]

    score_atual = safe_float(row["score_final"])
    oportunidade_atual = safe_float(row["score_oportunidade"])
    risco_atual = safe_float(row["score_risco"])
    potencial_atual = safe_float(row["score_potencial"], 50)
    setorial_atual = safe_float(row["score_setorial"], 50)
    competitividade_atual = safe_float(row["score_competitividade_setorial"], 50)
    pressao_custo_atual = safe_float(row["score_pressao_custo_setorial"], 50)
    substituicao_atual = safe_float(row["score_risco_substituicao_setorial"], 50)
    confianca = safe_float(row["confianca"], 50)

    competitividade_sim = calcular_competitividad_simulada(
        competitividade_atual,
        params.variacao_tilapia_pct,
        params.variacao_frango_pct,
        params.variacao_bovino_pct,
        params.variacao_suino_pct,
    )

    pressao_custo_sim = calcular_pressao_custo_simulada(
        pressao_custo_atual,
        params.variacao_dolar_pct,
        params.variacao_graos_pct,
    )

    substituicao_sim = calcular_risco_substituicao_simulado(
        substituicao_atual,
        params.variacao_tilapia_pct,
        params.variacao_frango_pct,
        params.variacao_bovino_pct,
        params.variacao_suino_pct,
    )

    setorial_sim = clamp(
        0.40 * (100 - competitividade_sim) +
        0.35 * pressao_custo_sim +
        0.25 * substituicao_sim
    )

    risco_sim = clamp(
        0.70 * risco_atual +
        0.30 * setorial_sim
    )

    oportunidade_bonus = 0.0
    if params.campanha_marketing:
        oportunidade_bonus += 4.0
    if params.adicionar_vendedor:
        oportunidade_bonus += 7.0
    if params.adicionar_promotor:
        oportunidade_bonus += 5.5

    oportunidade_bonus += clamp(params.melhorar_cobertura_pct, 0, 50) * 0.15
    oportunidade_bonus += clamp(params.aumentar_mix_premium_pct, 0, 50) * 0.10

    # Se competitividade piora demais, reduz parte da oportunidade.
    penalidade_competitividade = max(competitividade_atual - competitividade_sim, 0) * 0.12
    oportunidade_sim = clamp(oportunidade_atual + oportunidade_bonus - penalidade_competitividade)

    # Potencial melhora com cobertura/estrutura, mas pouco, pois potencial é estrutural.
    potencial_sim = clamp(
        potencial_atual +
        (5.0 if params.adicionar_vendedor else 0.0) +
        (3.0 if params.adicionar_promotor else 0.0) +
        clamp(params.melhorar_cobertura_pct, 0, 50) * 0.10
    )

    score_sim = clamp(
        0.50 * oportunidade_sim +
        0.25 * (100 - risco_sim) +
        0.15 * potencial_sim +
        0.10 * competitividade_sim
    )

    cenario_atual = int(row["cenario_1_10"] or scenario_1_10(score_atual))
    cenario_sim = scenario_1_10(score_sim)

    recomendacao_atual_data = carregar_recomendacao_atual(uf, regiao_comercial)
    recomendacao_atual = recomendacao_atual_data.get("tipo_recomendacao") or "N/A"

    recomendacao_simulada = "monitorar"
    motor_decisao = "monitoramento"
    acao_simulada = "Monitorar região e acompanhar indicadores."

    if pressao_custo_sim >= 70:
        recomendacao_simulada = "corrigir_mix_preco"
        motor_decisao = "pressao_custo_setorial"
        acao_simulada = "Revisar preço, margem, compras e mix por pressão de custo."
    elif competitividade_sim <= 35 and substituicao_sim >= 50:
        recomendacao_simulada = "campanha_marketing"
        motor_decisao = "competitividade_substituicao"
        acao_simulada = "Criar ação defensiva contra proteínas concorrentes."
    elif potencial_sim >= 75 and params.campanha_marketing:
        recomendacao_simulada = "campanha_marketing"
        motor_decisao = "potencial_regional"
        acao_simulada = "Executar campanha controlada para capturar potencial regional."
    elif potencial_sim >= 70 and params.adicionar_promotor:
        recomendacao_simulada = "adicionar_promotor"
        motor_decisao = "potencial_execucao"
        acao_simulada = "Avaliar promotor para melhorar execução e exposição."
    elif oportunidade_sim >= 65 and params.adicionar_vendedor:
        recomendacao_simulada = "adicionar_vendedor"
        motor_decisao = "expansao_comercial"
        acao_simulada = "Avaliar reforço de vendedor ou carteira dedicada."
    elif score_sim < score_atual - 5:
        recomendacao_simulada = "corrigir_mix_preco"
        motor_decisao = "queda_score_simulado"
        acao_simulada = "Simulação indica perda relevante de score; revisar preço, mix e campanha."
    elif score_sim > score_atual + 5:
        recomendacao_simulada = "campanha_marketing"
        motor_decisao = "ganho_score_simulado"
        acao_simulada = "Simulação indica melhora relevante; considerar teste comercial controlado."

    resultado = {
        "uf": uf,
        "regiao_comercial": regiao_comercial,
        "nome_cenario": nome_cenario or "Simulação What-if",
        "parametros": asdict(params),
        "score_atual": round(score_atual, 4),
        "score_simulado": round(score_sim, 4),
        "delta_score": round(score_sim - score_atual, 4),
        "cenario_atual": cenario_atual,
        "cenario_simulado": cenario_sim,
        "oportunidade_atual": round(oportunidade_atual, 4),
        "oportunidade_simulada": round(oportunidade_sim, 4),
        "risco_atual": round(risco_atual, 4),
        "risco_simulado": round(risco_sim, 4),
        "potencial_atual": round(potencial_atual, 4),
        "potencial_simulado": round(potencial_sim, 4),
        "setorial_atual": round(setorial_atual, 4),
        "setorial_simulado": round(setorial_sim, 4),
        "competitividade_atual": round(competitividade_atual, 4),
        "competitividade_simulada": round(competitividade_sim, 4),
        "pressao_custo_atual": round(pressao_custo_atual, 4),
        "pressao_custo_simulada": round(pressao_custo_sim, 4),
        "substituicao_atual": round(substituicao_atual, 4),
        "substituicao_simulada": round(substituicao_sim, 4),
        "confianca": round(confianca, 4),
        "recomendacao_atual": recomendacao_atual,
        "recomendacao_simulada": recomendacao_simulada,
        "motor_decisao_simulado": motor_decisao,
        "acao_simulada": acao_simulada,
        "observacao": "Simulação probabilística/heurística. Não representa certeza; serve para planejamento e comparação de cenários.",
    }

    if salvar:
        salvar_simulacao(resultado, usuario=usuario)

    return resultado


def salvar_simulacao(resultado: dict, usuario: str | None = None) -> int:
    engine = get_engine()

    with engine.begin() as conn:
        inserted_id = conn.execute(text("""
            INSERT INTO app.fato_simulacao_whatif (
                uf,
                regiao_comercial,
                nome_cenario,
                usuario,
                parametros,
                resultado,
                score_atual,
                score_simulado,
                delta_score,
                cenario_atual,
                cenario_simulado,
                recomendacao_atual,
                recomendacao_simulada,
                motor_decisao_simulado
            )
            VALUES (
                :uf,
                :regiao_comercial,
                :nome_cenario,
                :usuario,
                CAST(:parametros AS JSONB),
                CAST(:resultado AS JSONB),
                :score_atual,
                :score_simulado,
                :delta_score,
                :cenario_atual,
                :cenario_simulado,
                :recomendacao_atual,
                :recomendacao_simulada,
                :motor_decisao_simulado
            )
            RETURNING id
        """), {
            "uf": resultado["uf"],
            "regiao_comercial": resultado["regiao_comercial"],
            "nome_cenario": resultado["nome_cenario"],
            "usuario": usuario,
            "parametros": json.dumps(resultado["parametros"], ensure_ascii=False),
            "resultado": json.dumps(resultado, ensure_ascii=False),
            "score_atual": resultado["score_atual"],
            "score_simulado": resultado["score_simulado"],
            "delta_score": resultado["delta_score"],
            "cenario_atual": resultado["cenario_atual"],
            "cenario_simulado": resultado["cenario_simulado"],
            "recomendacao_atual": resultado["recomendacao_atual"],
            "recomendacao_simulada": resultado["recomendacao_simulada"],
            "motor_decisao_simulado": resultado["motor_decisao_simulado"],
        }).scalar()

    return int(inserted_id)


def carregar_ultimas_simulacoes(limit: int = 50) -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            id,
            data_simulacao,
            uf,
            regiao_comercial,
            nome_cenario,
            score_atual,
            score_simulado,
            delta_score,
            cenario_atual,
            cenario_simulado,
            recomendacao_atual,
            recomendacao_simulada,
            motor_decisao_simulado
        FROM app.vw_whatif_ultimas_simulacoes
        LIMIT :limit
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"limit": limit})


def comparar_cenarios_padrao(uf: str, regiao_comercial: str) -> pd.DataFrame:
    cenarios = [
        ("Base", WhatIfParams()),
        ("Dólar +10%", WhatIfParams(variacao_dolar_pct=10)),
        ("Frango -8%", WhatIfParams(variacao_frango_pct=-8)),
        ("Tilápia +5%", WhatIfParams(variacao_tilapia_pct=5)),
        ("Grãos +12%", WhatIfParams(variacao_graos_pct=12)),
        ("Campanha", WhatIfParams(campanha_marketing=True)),
        ("Adicionar vendedor", WhatIfParams(adicionar_vendedor=True)),
        ("Adicionar promotor", WhatIfParams(adicionar_promotor=True)),
        ("Cobertura +20%", WhatIfParams(melhorar_cobertura_pct=20)),
        ("Mix premium +15%", WhatIfParams(aumentar_mix_premium_pct=15)),
    ]

    resultados = []
    for nome, params in cenarios:
        r = simular_regiao(uf, regiao_comercial, params, salvar=False, nome_cenario=nome)
        resultados.append({
            "cenario": nome,
            "score_simulado": r["score_simulado"],
            "delta_score": r["delta_score"],
            "cenario_1_10": r["cenario_simulado"],
            "recomendacao": r["recomendacao_simulada"],
            "motor": r["motor_decisao_simulado"],
        })

    return pd.DataFrame(resultados)
