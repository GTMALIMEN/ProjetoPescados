from __future__ import annotations

import argparse
import json
import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


def clamp(value: float, min_value: float = 0, max_value: float = 100) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return float(max(min_value, min(max_value, value)))


def safe_float(value, default=0.0):
    if value is None or pd.isna(value):
        return default
    return float(value)


def carregar_scores(uf: str = "MG") -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            id,
            data_referencia,
            pais,
            uf,
            regiao_comercial,
            municipio,
            produto,
            proteina,
            score_oportunidade,
            score_risco,
            score_pressao_custo,
            score_potencial,
            score_setorial,
            score_competitividade_setorial,
            score_pressao_custo_setorial,
            score_risco_substituicao_setorial,
            score_final,
            cenario_1_10,
            confianca
        FROM app.mv_score_regional_atual
        WHERE uf = :uf
        ORDER BY score_final DESC
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"uf": uf})


def carregar_vendas_regiao(uf: str = "MG") -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            uf,
            COALESCE(regiao_comercial, 'Sem região') AS regiao_comercial,
            COUNT(*) AS linhas_vendas,
            COALESCE(SUM(valor_venda), 0) AS valor_venda,
            COALESCE(SUM(volume_kg), 0) AS volume_kg,
            COUNT(DISTINCT id_cliente) AS qtd_clientes,
            COUNT(DISTINCT id_produto) AS qtd_produtos,
            COUNT(DISTINCT id_vendedor) AS qtd_vendedores
        FROM dw.fato_vendas
        WHERE uf = :uf
        GROUP BY uf, COALESCE(regiao_comercial, 'Sem região')
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"uf": uf})


def carregar_roi_config() -> dict:
    engine = get_engine()
    sql = """
        SELECT tipo_recomendacao, custo_mensal_estimado, ganho_multiplo_estimado
        FROM app.config_roi_acao
        WHERE ativo = TRUE
    """
    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn)
    return {
        row["tipo_recomendacao"]: {
            "custo": float(row["custo_mensal_estimado"] or 0),
            "multiplo": float(row["ganho_multiplo_estimado"] or 0),
        }
        for _, row in df.iterrows()
    }


def calcular_roi(tipo: str, impacto: float | None, cfg: dict) -> float | None:
    custo = cfg.get(tipo, {}).get("custo", 0)
    if custo <= 0 or impacto is None:
        return None
    return ((float(impacto) - custo) / custo) * 100


def montar_recomendacao(score: pd.Series, venda: pd.Series | None, cfg: dict) -> dict:
    oportunidade = safe_float(score.get("score_oportunidade"))
    risco = safe_float(score.get("score_risco"))
    potencial = safe_float(score.get("score_potencial"), 50)
    final = safe_float(score.get("score_final"))
    confianca = safe_float(score.get("confianca"))
    cenario = int(score.get("cenario_1_10") or 1)

    score_setorial = safe_float(score.get("score_setorial"), 50)
    competitividade = safe_float(score.get("score_competitividade_setorial"), 50)
    pressao_custo = safe_float(score.get("score_pressao_custo_setorial"), 50)
    risco_substituicao = safe_float(score.get("score_risco_substituicao_setorial"), 50)

    valor = volume = 0.0
    clientes = produtos = vendedores = 0
    if venda is not None:
        valor = safe_float(venda.get("valor_venda"))
        volume = safe_float(venda.get("volume_kg"))
        clientes = int(venda.get("qtd_clientes") or 0)
        produtos = int(venda.get("qtd_produtos") or 0)
        vendedores = int(venda.get("qtd_vendedores") or 0)

    tem_vendas = valor > 0 or volume > 0 or clientes > 0

    score_vendedor = clamp(
        0.30 * oportunidade +
        0.18 * potencial +
        0.12 * competitividade +
        0.15 * (100 - min(vendedores * 25, 100)) +
        0.15 * min(clientes * 5, 100) +
        0.10 * final
    )

    score_promotor = clamp(
        0.25 * oportunidade +
        0.22 * potencial +
        0.13 * competitividade +
        0.18 * min(clientes * 6, 100) +
        0.12 * min(produtos * 8, 100) +
        0.10 * final
    )

    score_campanha = clamp(
        0.25 * potencial +
        0.20 * oportunidade +
        0.20 * (100 - competitividade) +
        0.15 * risco_substituicao +
        0.10 * (100 - confianca) +
        0.10 * min(produtos * 10, 100)
    )

    tipo = "monitorar"
    acao = "Monitorar região e acompanhar indicadores"
    justificativa = (
        "A região não apresenta sinal forte o suficiente para ação agressiva. "
        "Acompanhe novas cargas, potencial, competitividade e evolução do score."
    )
    motor_decisao = "monitoramento"
    impacto = None

    if pressao_custo >= 70:
        tipo = "corrigir_mix_preco"
        acao = "Revisar preço, margem, compras e mix por pressão de custo"
        justificativa = (
            "A pressão de custo setorial está elevada. Antes de expandir venda, revise preço, margem, compras, estoque e mix. "
            "O alerta vem de grãos, farinha de peixe, dólar ou insumos relacionados ao custo de pescado."
        )
        motor_decisao = "pressao_custo_setorial"

    elif competitividade <= 35 and risco_substituicao >= 50:
        tipo = "campanha_marketing"
        acao = "Criar ação defensiva de competitividade contra proteínas concorrentes"
        justificativa = (
            "O pescado está com baixa competitividade relativa e há risco de substituição por proteínas concorrentes. "
            "A recomendação é defender mix, comunicação de valor, promoções controladas e posicionamento por ocasião de consumo."
        )
        motor_decisao = "competitividade_substituicao"

    elif not tem_vendas or confianca < 45:
        tipo = "aguardar_dados_reais"
        acao = "Aguardar base real de vendas / monitorar região"
        justificativa = (
            "A região possui potencial e leitura setorial, mas a confiança ainda é limitada por falta de vendas reais suficientes. "
            "Carregue vendas reais e recalcule potencial, scores e recomendações antes de investir pesado."
        )
        motor_decisao = "dados_insuficientes"

    elif risco >= 75:
        tipo = "corrigir_mix_preco"
        acao = "Corrigir mix, preço ou execução comercial"
        justificativa = (
            "O risco regional está alto. Antes de expandir, revise mix, preço, frequência e comportamento dos clientes."
        )
        motor_decisao = "risco_regional"

    elif potencial >= 75 and score_campanha >= 55:
        tipo = "campanha_marketing"
        acao = "Ativar campanha para explorar potencial regional"
        justificativa = (
            "A região apresenta alto potencial não explorado. Como há leitura setorial suficiente, a ação sugerida é uma campanha controlada "
            "para testar resposta antes de aumentar estrutura fixa."
        )
        impacto = max(valor * 0.08, cfg.get(tipo, {}).get("custo", 0) * cfg.get(tipo, {}).get("multiplo", 0))
        motor_decisao = "potencial_regional"

    elif potencial >= 70 and score_promotor >= 55:
        tipo = "adicionar_promotor"
        acao = "Avaliar promotor para capturar potencial regional"
        justificativa = (
            "A região tem potencial relevante e base mínima de vendas. Promotor pode ajudar na execução em loja, exposição e mix."
        )
        impacto = max(valor * 0.08, cfg.get(tipo, {}).get("custo", 0) * cfg.get(tipo, {}).get("multiplo", 0))
        motor_decisao = "potencial_execucao"

    elif score_vendedor >= score_campanha and score_vendedor >= 65:
        tipo = "adicionar_vendedor"
        acao = "Avaliar reforço de vendedor ou carteira dedicada"
        justificativa = (
            "Há oportunidade comercial e possível espaço de expansão de cobertura. "
            "O reforço de vendedor deve ser avaliado contra carteira, rota e clientes potenciais."
        )
        impacto = max(valor * 0.10, cfg.get(tipo, {}).get("custo", 0) * cfg.get(tipo, {}).get("multiplo", 0))
        motor_decisao = "expansao_comercial"

    elif score_campanha >= 60:
        tipo = "campanha_marketing"
        acao = "Planejar campanha comercial regional"
        justificativa = (
            "A região possui oportunidade, mas a melhor ação inicial parece ser campanha comercial para testar elasticidade e resposta."
        )
        impacto = max(valor * 0.06, cfg.get(tipo, {}).get("custo", 0) * cfg.get(tipo, {}).get("multiplo", 0))
        motor_decisao = "campanha_teste"

    fatores = [
        {"fator": "score_oportunidade", "descricao": "Oportunidade regional", "peso": 0.20, "direcao": "positiva", "impacto": oportunidade, "unidade": "score", "confianca": confianca},
        {"fator": "score_potencial", "descricao": "Potencial regional por população, venda per capita e cobertura", "peso": 0.20, "direcao": "positiva", "impacto": potencial, "unidade": "score", "confianca": confianca},
        {"fator": "competitividade_pescado", "descricao": "Competitividade do pescado contra proteínas concorrentes", "peso": 0.20, "direcao": "positiva", "impacto": competitividade, "unidade": "score", "confianca": confianca},
        {"fator": "pressao_custo_racao", "descricao": "Pressão de custo por grãos, farinha de peixe e dólar", "peso": 0.15, "direcao": "negativa", "impacto": pressao_custo, "unidade": "score", "confianca": confianca},
        {"fator": "risco_substituicao_proteinas", "descricao": "Risco de substituição entre pescado e proteínas concorrentes", "peso": 0.15, "direcao": "negativa", "impacto": risco_substituicao, "unidade": "score", "confianca": confianca},
        {"fator": "base_vendas", "descricao": "Presença e profundidade da base real de vendas", "peso": 0.10, "direcao": "positiva", "impacto": valor, "unidade": "R$", "confianca": confianca},
    ]

    return {
        "id_score": int(score["id"]),
        "data_referencia": score["data_referencia"],
        "pais": score.get("pais") or "Brasil",
        "uf": score.get("uf") or "",
        "regiao_comercial": score.get("regiao_comercial") or "",
        "municipio": score.get("municipio") or "",
        "produto": score.get("produto") or "",
        "proteina": score.get("proteina") or "",
        "cenario_1_10": cenario,
        "tipo_recomendacao": tipo,
        "acao_sugerida": acao,
        "justificativa": justificativa,
        "confianca": confianca,
        "impacto_estimado": impacto,
        "roi_estimado": calcular_roi(tipo, impacto, cfg),
        "score_vendedor": score_vendedor,
        "score_promotor": score_promotor,
        "score_campanha": score_campanha,
        "score_potencial": potencial,
        "score_setorial": score_setorial,
        "score_competitividade_setorial": competitividade,
        "score_pressao_custo_setorial": pressao_custo,
        "score_risco_substituicao_setorial": risco_substituicao,
        "motor_decisao": motor_decisao,
        "status": "pendente",
        "principais_fatores": json.dumps(fatores, ensure_ascii=False),
    }


def gerar_recomendacoes(uf: str = "MG") -> pd.DataFrame:
    scores = carregar_scores(uf)
    if scores.empty:
        raise ValueError("Nenhum score encontrado. Rode: python scripts/calculate_scores.py --uf MG --salvar")

    vendas = carregar_vendas_regiao(uf)
    cfg = carregar_roi_config()

    venda_map = {
        (row["uf"], row["regiao_comercial"]): row
        for _, row in vendas.iterrows()
    } if not vendas.empty else {}

    recs = []
    for _, score in scores.iterrows():
        venda = venda_map.get((score["uf"], score["regiao_comercial"]))
        recs.append(montar_recomendacao(score, venda, cfg))

    return pd.DataFrame(recs)


def salvar_recomendacoes(df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    records = df.to_dict(orient="records")
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.fato_recomendacao (
                id_score, data_referencia, pais, uf, regiao_comercial, municipio,
                produto, proteina, cenario_1_10, tipo_recomendacao, acao_sugerida,
                justificativa, confianca, impacto_estimado, roi_estimado,
                score_vendedor, score_promotor, score_campanha, score_potencial,
                score_setorial, score_competitividade_setorial, score_pressao_custo_setorial,
                score_risco_substituicao_setorial, motor_decisao, status, principais_fatores
            )
            VALUES (
                :id_score, :data_referencia, :pais, :uf, :regiao_comercial, :municipio,
                :produto, :proteina, :cenario_1_10, :tipo_recomendacao, :acao_sugerida,
                :justificativa, :confianca, :impacto_estimado, :roi_estimado,
                :score_vendedor, :score_promotor, :score_campanha, :score_potencial,
                :score_setorial, :score_competitividade_setorial, :score_pressao_custo_setorial,
                :score_risco_substituicao_setorial, :motor_decisao, :status,
                CAST(:principais_fatores AS JSONB)
            )
            ON CONFLICT (
                data_referencia, pais, uf, regiao_comercial, municipio, produto, proteina, tipo_recomendacao
            )
            DO UPDATE SET
                id_score = EXCLUDED.id_score,
                cenario_1_10 = EXCLUDED.cenario_1_10,
                acao_sugerida = EXCLUDED.acao_sugerida,
                justificativa = EXCLUDED.justificativa,
                confianca = EXCLUDED.confianca,
                impacto_estimado = EXCLUDED.impacto_estimado,
                roi_estimado = EXCLUDED.roi_estimado,
                score_vendedor = EXCLUDED.score_vendedor,
                score_promotor = EXCLUDED.score_promotor,
                score_campanha = EXCLUDED.score_campanha,
                score_potencial = EXCLUDED.score_potencial,
                score_setorial = EXCLUDED.score_setorial,
                score_competitividade_setorial = EXCLUDED.score_competitividade_setorial,
                score_pressao_custo_setorial = EXCLUDED.score_pressao_custo_setorial,
                score_risco_substituicao_setorial = EXCLUDED.score_risco_substituicao_setorial,
                motor_decisao = EXCLUDED.motor_decisao,
                status = EXCLUDED.status,
                principais_fatores = EXCLUDED.principais_fatores,
                data_criacao = NOW();
        """), records)
        conn.execute(text("REFRESH MATERIALIZED VIEW app.mv_recomendacao_atual"))

    return len(records)


def main():
    parser = argparse.ArgumentParser(description="Gerar recomendações comerciais com potencial e indicadores setoriais")
    parser.add_argument("--uf", default="MG")
    parser.add_argument("--salvar", action="store_true")
    args = parser.parse_args()

    df = gerar_recomendacoes(args.uf)

    print("\nRecomendações geradas:")
    print(df[[
        "uf", "regiao_comercial", "cenario_1_10", "tipo_recomendacao",
        "motor_decisao", "score_potencial", "score_setorial",
        "score_competitividade_setorial", "score_pressao_custo_setorial",
        "score_risco_substituicao_setorial", "confianca",
        "score_vendedor", "score_promotor", "score_campanha", "roi_estimado"
    ]].to_string(index=False))

    if args.salvar:
        qtd = salvar_recomendacoes(df)
        print(f"\n✅ Recomendações salvas/atualizadas: {qtd}")


if __name__ == "__main__":
    main()
