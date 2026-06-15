from __future__ import annotations

import argparse
import json
from datetime import date

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


SEVERITY_ORDER = {
    "baixo": 1,
    "medio": 2,
    "alto": 3,
    "critico": 4,
}


def safe_float(value, default=0.0) -> float:
    if value is None or pd.isna(value):
        return default
    return float(value)


def severity_by_high(value: float, alert: float, critical: float) -> str | None:
    if value >= critical:
        return "critico"
    if value >= alert:
        return "alto"
    return None


def severity_by_low(value: float, alert: float, critical: float) -> str | None:
    if value <= critical:
        return "critico"
    if value <= alert:
        return "alto"
    return None


def load_current_scores(uf: str = "MG") -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            data_referencia,
            uf,
            regiao_comercial,
            score_final,
            score_oportunidade,
            score_risco,
            COALESCE(score_potencial, 0) AS score_potencial,
            COALESCE(score_setorial, 0) AS score_setorial,
            COALESCE(score_competitividade_setorial, 0) AS score_competitividade_setorial,
            COALESCE(score_pressao_custo_setorial, 0) AS score_pressao_custo_setorial,
            COALESCE(score_risco_substituicao_setorial, 0) AS score_risco_substituicao_setorial,
            cenario_1_10,
            confianca,
            metodo
        FROM app.mv_score_regional_atual
        WHERE uf = :uf
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"uf": uf})


def load_current_recommendations(uf: str = "MG") -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            uf,
            regiao_comercial,
            tipo_recomendacao,
            acao_sugerida,
            motor_decisao,
            cenario_1_10,
            confianca,
            COALESCE(score_potencial, 0) AS score_potencial,
            COALESCE(score_setorial, 0) AS score_setorial
        FROM app.mv_recomendacao_atual
        WHERE uf = :uf
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"uf": uf})


def load_alert_config() -> dict:
    engine = get_engine()
    sql = """
        SELECT
            tipo_alerta,
            nome,
            area_responsavel,
            descricao,
            limite_alerta,
            limite_critico,
            direcao,
            ativo
        FROM app.config_alerta_ativo
        WHERE ativo = TRUE
    """
    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn)

    return {
        row["tipo_alerta"]: row.to_dict()
        for _, row in df.iterrows()
    }


def _base_alert(
    row,
    tipo_alerta: str,
    config: dict,
    severidade: str,
    score_relacionado: float,
    titulo: str,
    mensagem: str,
    recomendacao_sugerida: str,
    origem: str,
    fatores: list[dict],
) -> dict:
    return {
        "data_referencia": row["data_referencia"],
        "uf": row["uf"],
        "regiao_comercial": row["regiao_comercial"],
        "area_responsavel": config[tipo_alerta]["area_responsavel"],
        "tipo_alerta": tipo_alerta,
        "severidade": severidade,
        "status": "ativo",
        "titulo": titulo,
        "mensagem": mensagem,
        "score_relacionado": score_relacionado,
        "recomendacao_sugerida": recomendacao_sugerida,
        "origem": origem,
        "principais_fatores": json.dumps(fatores, ensure_ascii=False),
    }


def gerar_alertas_ativos(uf: str = "MG") -> pd.DataFrame:
    scores = load_current_scores(uf)
    recs = load_current_recommendations(uf)
    cfg = load_alert_config()

    if scores.empty:
        return pd.DataFrame()

    rec_map = {}
    if not recs.empty:
        rec_map = {
            (row["uf"], row["regiao_comercial"]): row.to_dict()
            for _, row in recs.iterrows()
        }

    alertas = []

    for _, row in scores.iterrows():
        regiao = row["regiao_comercial"]
        rec = rec_map.get((row["uf"], regiao), {})

        score_final = safe_float(row["score_final"])
        potencial = safe_float(row["score_potencial"])
        confianca = safe_float(row["confianca"])
        comp = safe_float(row["score_competitividade_setorial"])
        custo = safe_float(row["score_pressao_custo_setorial"])
        subst = safe_float(row["score_risco_substituicao_setorial"])
        risco = safe_float(row["score_risco"])
        setorial = safe_float(row["score_setorial"])

        # Competitividade baixa
        if "competitividade_baixa" in cfg:
            sev = severity_by_low(comp, cfg["competitividade_baixa"]["limite_alerta"], cfg["competitividade_baixa"]["limite_critico"])
            if sev:
                alertas.append(_base_alert(
                    row,
                    "competitividade_baixa",
                    cfg,
                    sev,
                    comp,
                    f"Pescado com baixa competitividade — {regiao}",
                    (
                        f"A competitividade setorial do pescado está em {comp:.2f}. "
                        "Isso indica posição desfavorável contra proteínas concorrentes."
                    ),
                    "Avaliar campanha defensiva, ajuste de mix, comunicação de valor e ações contra substituição.",
                    "mv_score_regional_atual",
                    [
                        {"fator": "competitividade_pescado", "valor": comp, "direcao": "menor_pior"},
                        {"fator": "risco_substituicao", "valor": subst, "direcao": "maior_pior"},
                    ],
                ))

        # Pressão de custo alta
        if "pressao_custo_alta" in cfg:
            sev = severity_by_high(custo, cfg["pressao_custo_alta"]["limite_alerta"], cfg["pressao_custo_alta"]["limite_critico"])
            if sev:
                alertas.append(_base_alert(
                    row,
                    "pressao_custo_alta",
                    cfg,
                    sev,
                    custo,
                    f"Pressão de custo elevada — {regiao}",
                    (
                        f"A pressão de custo setorial está em {custo:.2f}. "
                        "Pode haver impacto em margem, preço e compras."
                    ),
                    "Revisar preço, margem, compras, contratos, estoque e mix.",
                    "mv_score_regional_atual",
                    [
                        {"fator": "pressao_custo_racao", "valor": custo, "direcao": "maior_pior"},
                        {"fator": "score_setorial", "valor": setorial, "direcao": "maior_pior"},
                    ],
                ))

        # Risco de substituição
        if "risco_substituicao_alto" in cfg:
            sev = severity_by_high(subst, cfg["risco_substituicao_alto"]["limite_alerta"], cfg["risco_substituicao_alto"]["limite_critico"])
            if sev:
                alertas.append(_base_alert(
                    row,
                    "risco_substituicao_alto",
                    cfg,
                    sev,
                    subst,
                    f"Risco de substituição entre proteínas — {regiao}",
                    (
                        f"O risco de substituição está em {subst:.2f}. "
                        "Consumidor pode migrar para proteínas concorrentes."
                    ),
                    "Avaliar campanha, promoção controlada, defesa de preço e posicionamento por ocasião de consumo.",
                    "mv_score_regional_atual",
                    [
                        {"fator": "risco_substituicao", "valor": subst, "direcao": "maior_pior"},
                        {"fator": "competitividade_pescado", "valor": comp, "direcao": "menor_pior"},
                    ],
                ))

        # Potencial alto e venda baixa / dados insuficientes
        if "potencial_alto_venda_baixa" in cfg:
            sev = severity_by_high(potencial, cfg["potencial_alto_venda_baixa"]["limite_alerta"], cfg["potencial_alto_venda_baixa"]["limite_critico"])
            if sev and confianca <= 60:
                alertas.append(_base_alert(
                    row,
                    "potencial_alto_venda_baixa",
                    cfg,
                    sev,
                    potencial,
                    f"Potencial alto com baixa base comercial — {regiao}",
                    (
                        f"A região possui potencial {potencial:.2f}, mas confiança {confianca:.2f}. "
                        "Pode existir oportunidade ainda pouco explorada."
                    ),
                    "Priorizar coleta de dados reais, prospecção, validação de carteira e teste comercial controlado.",
                    "mv_score_regional_atual",
                    [
                        {"fator": "score_potencial", "valor": potencial, "direcao": "maior_melhor"},
                        {"fator": "confianca", "valor": confianca, "direcao": "maior_melhor"},
                    ],
                ))

        # Score baixo
        if "score_regional_baixo" in cfg:
            sev = severity_by_low(score_final, cfg["score_regional_baixo"]["limite_alerta"], cfg["score_regional_baixo"]["limite_critico"])
            if sev:
                alertas.append(_base_alert(
                    row,
                    "score_regional_baixo",
                    cfg,
                    sev,
                    score_final,
                    f"Score regional baixo — {regiao}",
                    (
                        f"O score final da região está em {score_final:.2f}. "
                        "É necessário revisar oportunidade, risco, potencial e mercado."
                    ),
                    "Revisar mix, execução comercial, potencial, cobertura e estratégia regional.",
                    "mv_score_regional_atual",
                    [
                        {"fator": "score_final", "valor": score_final, "direcao": "menor_pior"},
                        {"fator": "score_risco", "valor": risco, "direcao": "maior_pior"},
                        {"fator": "score_setorial", "valor": setorial, "direcao": "maior_pior"},
                    ],
                ))

        # Dados insuficientes em região promissora
        if "dados_insuficientes_potencial" in cfg:
            sev = severity_by_high(potencial, cfg["dados_insuficientes_potencial"]["limite_alerta"], cfg["dados_insuficientes_potencial"]["limite_critico"])
            motor = rec.get("motor_decisao")
            if sev and motor == "dados_insuficientes":
                alertas.append(_base_alert(
                    row,
                    "dados_insuficientes_potencial",
                    cfg,
                    "medio" if sev == "alto" else "alto",
                    potencial,
                    f"Dados insuficientes em região promissora — {regiao}",
                    (
                        f"A recomendação atual está travada por dados insuficientes, "
                        f"mas a região possui potencial {potencial:.2f}."
                    ),
                    "Carregar vendas reais, validar clientes ativos e enriquecer carteira da região.",
                    "mv_recomendacao_atual",
                    [
                        {"fator": "score_potencial", "valor": potencial, "direcao": "maior_melhor"},
                        {"fator": "motor_decisao", "valor": motor, "direcao": "informativo"},
                    ],
                ))

        # Recomendação de correção de mix/preço
        if "recomendacao_correcao_mix_preco" in cfg:
            if rec.get("tipo_recomendacao") == "corrigir_mix_preco":
                alertas.append(_base_alert(
                    row,
                    "recomendacao_correcao_mix_preco",
                    cfg,
                    "alto",
                    risco,
                    f"Recomendação de correção de mix/preço — {regiao}",
                    rec.get("acao_sugerida") or "Motor recomendou revisão de mix/preço.",
                    "Acionar Precificação/Comercial para revisar preço, margem, mix e comunicação.",
                    "mv_recomendacao_atual",
                    [
                        {"fator": "tipo_recomendacao", "valor": rec.get("tipo_recomendacao"), "direcao": "informativo"},
                        {"fator": "motor_decisao", "valor": rec.get("motor_decisao"), "direcao": "informativo"},
                    ],
                ))

    if not alertas:
        return pd.DataFrame()

    df = pd.DataFrame(alertas)

    # Dedup por chave natural, mantendo maior severidade.
    df["_sev_rank"] = df["severidade"].map(SEVERITY_ORDER).fillna(0)
    df = (
        df.sort_values("_sev_rank", ascending=False)
        .drop_duplicates(subset=["data_referencia", "uf", "regiao_comercial", "tipo_alerta", "origem"])
        .drop(columns=["_sev_rank"])
        .reset_index(drop=True)
    )

    return df


def salvar_alertas_ativos(df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    records = df.to_dict(orient="records")
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.fato_alerta_ativo (
                data_referencia,
                uf,
                regiao_comercial,
                area_responsavel,
                tipo_alerta,
                severidade,
                status,
                titulo,
                mensagem,
                score_relacionado,
                recomendacao_sugerida,
                origem,
                principais_fatores
            )
            VALUES (
                :data_referencia,
                :uf,
                :regiao_comercial,
                :area_responsavel,
                :tipo_alerta,
                :severidade,
                :status,
                :titulo,
                :mensagem,
                :score_relacionado,
                :recomendacao_sugerida,
                :origem,
                CAST(:principais_fatores AS JSONB)
            )
            ON CONFLICT (
                data_referencia,
                uf,
                regiao_comercial,
                tipo_alerta,
                origem
            )
            DO UPDATE SET
                area_responsavel = EXCLUDED.area_responsavel,
                severidade = EXCLUDED.severidade,
                titulo = EXCLUDED.titulo,
                mensagem = EXCLUDED.mensagem,
                score_relacionado = EXCLUDED.score_relacionado,
                recomendacao_sugerida = EXCLUDED.recomendacao_sugerida,
                principais_fatores = EXCLUDED.principais_fatores,
                data_atualizacao = NOW(),
                status = CASE
                    WHEN app.fato_alerta_ativo.status IN ('resolvido', 'ignorado') THEN app.fato_alerta_ativo.status
                    ELSE EXCLUDED.status
                END;
        """), records)

    return len(records)


def atualizar_status_alerta(id_alerta: int, status_novo: str, comentario: str = "", usuario: str = "") -> None:
    engine = get_engine()

    with engine.begin() as conn:
        row = conn.execute(text("""
            SELECT status
            FROM app.fato_alerta_ativo
            WHERE id = :id
        """), {"id": id_alerta}).mappings().first()

        if not row:
            raise ValueError(f"Alerta não encontrado: {id_alerta}")

        status_anterior = row["status"]

        conn.execute(text("""
            UPDATE app.fato_alerta_ativo
            SET status = :status_novo,
                data_atualizacao = NOW(),
                data_resolucao = CASE
                    WHEN :status_novo IN ('resolvido', 'ignorado') THEN NOW()
                    ELSE data_resolucao
                END
            WHERE id = :id
        """), {"id": id_alerta, "status_novo": status_novo})

        conn.execute(text("""
            INSERT INTO app.historico_alerta_ativo (
                id_alerta,
                status_anterior,
                status_novo,
                comentario,
                usuario
            )
            VALUES (
                :id_alerta,
                :status_anterior,
                :status_novo,
                :comentario,
                :usuario
            )
        """), {
            "id_alerta": id_alerta,
            "status_anterior": status_anterior,
            "status_novo": status_novo,
            "comentario": comentario,
            "usuario": usuario,
        })


def carregar_alertas_ativos(status: str | None = None, area: str | None = None) -> pd.DataFrame:
    engine = get_engine()

    filtros = []
    params = {}

    if status:
        filtros.append("status = :status")
        params["status"] = status

    if area:
        filtros.append("area_responsavel = :area")
        params["area"] = area

    where_clause = ""
    if filtros:
        where_clause = "WHERE " + " AND ".join(filtros)

    sql = f"""
        SELECT
            id,
            data_referencia,
            uf,
            regiao_comercial,
            area_responsavel,
            tipo_alerta,
            severidade,
            status,
            titulo,
            mensagem,
            score_relacionado,
            recomendacao_sugerida,
            origem,
            data_criacao,
            data_atualizacao
        FROM app.fato_alerta_ativo
        {where_clause}
        ORDER BY
            CASE severidade
                WHEN 'critico' THEN 1
                WHEN 'alto' THEN 2
                WHEN 'medio' THEN 3
                ELSE 4
            END,
            data_atualizacao DESC,
            id DESC
    """

    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params=params)


def carregar_resumo_alertas_area() -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT *
        FROM app.vw_alertas_resumo_area
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn)


def carregar_resumo_alertas_tipo() -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT *
        FROM app.vw_alertas_resumo_tipo
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn)


def gerar_e_salvar_alertas(uf: str = "MG") -> tuple[pd.DataFrame, int]:
    df = gerar_alertas_ativos(uf=uf)
    qtd = salvar_alertas_ativos(df)
    return df, qtd


def main():
    parser = argparse.ArgumentParser(description="Gerar alertas ativos")
    parser.add_argument("--uf", default="MG")
    parser.add_argument("--salvar", action="store_true")
    args = parser.parse_args()

    df = gerar_alertas_ativos(args.uf)

    if df.empty:
        print("\nNenhum alerta ativo gerado.")
    else:
        print("\nAlertas gerados:")
        print(df[[
            "uf",
            "regiao_comercial",
            "area_responsavel",
            "tipo_alerta",
            "severidade",
            "score_relacionado",
            "titulo",
        ]].to_string(index=False))

    if args.salvar:
        qtd = salvar_alertas_ativos(df)
        print(f"\n✅ Alertas salvos/atualizados: {qtd}")


if __name__ == "__main__":
    main()
