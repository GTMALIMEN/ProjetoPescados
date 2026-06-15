from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


ROOT_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT_DIR / "outputs" / "relatorios"


def br_money(value) -> str:
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def br_num(value, casas: int = 2) -> str:
    try:
        return f"{float(value):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00"


def safe_float(value, default=0.0):
    if value is None or pd.isna(value):
        return default
    return float(value)


def clean_date_or_none(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    s = str(value).strip()
    if s.lower() in {"", "none", "nan", "nat", "null"}:
        return None

    # mantém YYYY-MM-DD quando vier timestamp
    return s[:10]


def _read_df(sql: str, params: dict | None = None) -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def carregar_dados_relatorio(uf: str = "MG") -> dict:
    dados = {}

    # Vendas
    dados["vendas_resumo"] = _read_df("""
        SELECT
            COUNT(*) AS qtd_linhas,
            COALESCE(SUM(valor_venda), 0) AS faturamento,
            COALESCE(SUM(volume_kg), 0) AS volume_kg,
            COUNT(DISTINCT id_cliente) AS clientes,
            COUNT(DISTINCT id_produto) AS produtos,
            MIN(data) AS primeira_data,
            MAX(data) AS ultima_data
        FROM dw.fato_vendas
        WHERE uf = :uf
    """, {"uf": uf})

    dados["top_regioes_faturamento"] = _read_df("""
        SELECT
            COALESCE(regiao_comercial, 'Sem região') AS regiao_comercial,
            COALESCE(SUM(valor_venda), 0) AS faturamento,
            COALESCE(SUM(volume_kg), 0) AS volume_kg,
            COUNT(DISTINCT id_cliente) AS clientes
        FROM dw.fato_vendas
        WHERE uf = :uf
        GROUP BY COALESCE(regiao_comercial, 'Sem região')
        ORDER BY faturamento DESC
        LIMIT 10
    """, {"uf": uf})

    # Scores
    dados["scores"] = _read_df("""
        SELECT
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
            confianca
        FROM app.mv_score_regional_atual
        WHERE uf = :uf
        ORDER BY score_final DESC
    """, {"uf": uf})

    dados["top_oportunidades"] = _read_df("""
        SELECT
            regiao_comercial,
            score_final,
            score_oportunidade,
            COALESCE(score_potencial, 0) AS score_potencial,
            cenario_1_10,
            confianca
        FROM app.mv_score_regional_atual
        WHERE uf = :uf
        ORDER BY score_potencial DESC, score_oportunidade DESC
        LIMIT 10
    """, {"uf": uf})

    dados["top_riscos"] = _read_df("""
        SELECT
            regiao_comercial,
            score_risco,
            COALESCE(score_setorial, 0) AS score_setorial,
            COALESCE(score_pressao_custo_setorial, 0) AS score_pressao_custo_setorial,
            COALESCE(score_risco_substituicao_setorial, 0) AS score_risco_substituicao_setorial,
            cenario_1_10,
            confianca
        FROM app.mv_score_regional_atual
        WHERE uf = :uf
        ORDER BY score_risco DESC, score_setorial DESC
        LIMIT 10
    """, {"uf": uf})

    # Recomendações
    dados["recomendacoes"] = _read_df("""
        SELECT
            regiao_comercial,
            tipo_recomendacao,
            motor_decisao,
            acao_sugerida,
            cenario_1_10,
            confianca,
            COALESCE(score_potencial, 0) AS score_potencial,
            COALESCE(score_setorial, 0) AS score_setorial
        FROM app.mv_recomendacao_atual
        WHERE uf = :uf
        ORDER BY cenario_1_10 DESC, score_potencial DESC, confianca DESC
    """, {"uf": uf})

    # Alertas
    dados["alertas"] = _read_df("""
        SELECT
            id,
            data_referencia,
            regiao_comercial,
            area_responsavel,
            tipo_alerta,
            severidade,
            status,
            titulo,
            mensagem,
            score_relacionado,
            recomendacao_sugerida
        FROM app.fato_alerta_ativo
        WHERE uf = :uf
          AND status IN ('ativo', 'em_analise')
        ORDER BY
            CASE severidade
                WHEN 'critico' THEN 1
                WHEN 'alto' THEN 2
                WHEN 'medio' THEN 3
                ELSE 4
            END,
            data_atualizacao DESC
    """, {"uf": uf})

    dados["alertas_area"] = _read_df("""
        SELECT *
        FROM app.vw_alertas_resumo_area
    """)

    # Setorial
    dados["indices_setoriais"] = _read_df("""
        SELECT
            indice,
            score,
            cenario_1_10,
            confianca,
            metodo,
            data_calculo
        FROM app.mv_indice_setorial_atual
        WHERE uf = :uf
        ORDER BY indice
    """, {"uf": uf})

    # What-if
    dados["whatif"] = _read_df("""
        SELECT
            data_simulacao,
            regiao_comercial,
            nome_cenario,
            score_atual,
            score_simulado,
            delta_score,
            cenario_atual,
            cenario_simulado,
            recomendacao_simulada,
            motor_decisao_simulado
        FROM app.vw_whatif_ultimas_simulacoes
        WHERE uf = :uf
        LIMIT 10
    """, {"uf": uf})

    # Fontes reais
    dados["fontes_reais"] = _read_df("""
        SELECT *
        FROM app.vw_fontes_reais_setoriais
        ORDER BY fonte
    """)

    return dados


def montar_resumo_executivo(dados: dict, uf: str = "MG") -> str:
    vendas = dados["vendas_resumo"].iloc[0] if not dados["vendas_resumo"].empty else {}

    scores = dados["scores"]
    alertas = dados["alertas"]
    recs = dados["recomendacoes"]
    indices = dados["indices_setoriais"]

    faturamento = safe_float(vendas.get("faturamento", 0)) if hasattr(vendas, "get") else 0
    volume = safe_float(vendas.get("volume_kg", 0)) if hasattr(vendas, "get") else 0
    clientes = int(vendas.get("clientes", 0)) if hasattr(vendas, "get") else 0

    score_medio = safe_float(scores["score_final"].mean()) if not scores.empty else 0
    potencial_medio = safe_float(scores["score_potencial"].mean()) if not scores.empty else 0
    risco_medio = safe_float(scores["score_risco"].mean()) if not scores.empty else 0

    qtd_alertas = len(alertas)
    qtd_criticos = len(alertas[alertas["severidade"] == "critico"]) if not alertas.empty else 0
    qtd_altos = len(alertas[alertas["severidade"] == "alto"]) if not alertas.empty else 0

    top_oportunidade = "N/A"
    if not dados["top_oportunidades"].empty:
        top_oportunidade = dados["top_oportunidades"].iloc[0]["regiao_comercial"]

    maior_risco = "N/A"
    if not dados["top_riscos"].empty:
        maior_risco = dados["top_riscos"].iloc[0]["regiao_comercial"]

    principal_rec = "N/A"
    if not recs.empty:
        principal_rec = recs.iloc[0]["tipo_recomendacao"]

    competitividade = None
    pressao = None
    substituicao = None
    if not indices.empty:
        for _, row in indices.iterrows():
            if row["indice"] == "competitividade_pescado":
                competitividade = safe_float(row["score"])
            elif row["indice"] == "pressao_custo_racao":
                pressao = safe_float(row["score"])
            elif row["indice"] == "risco_substituicao_proteinas":
                substituicao = safe_float(row["score"])

    texto = f"""
Resumo executivo — Radar Pescados IA ({uf})

No período analisado, a base possui faturamento de {br_money(faturamento)}, volume de {br_num(volume)} kg e {clientes} clientes distintos.

O score médio regional está em {br_num(score_medio)}, com potencial médio de {br_num(potencial_medio)} e risco médio de {br_num(risco_medio)}.

A principal região de oportunidade é {top_oportunidade}. A região com maior risco é {maior_risco}.

Os alertas ativos somam {qtd_alertas}, sendo {qtd_criticos} críticos e {qtd_altos} altos.

A recomendação dominante no topo do ranking é {principal_rec}.

Indicadores setoriais:
- Competitividade do pescado: {br_num(competitividade) if competitividade is not None else 'N/A'}
- Pressão de custo/racao: {br_num(pressao) if pressao is not None else 'N/A'}
- Risco de substituição: {br_num(substituicao) if substituicao is not None else 'N/A'}

Leitura geral: o relatório deve ser usado como apoio à decisão. Os scores e alertas são probabilísticos e dependem da qualidade das fontes internas e externas.
""".strip()

    return texto


def montar_mensagem_whatsapp(dados: dict, uf: str = "MG") -> str:
    scores = dados["scores"]
    alertas = dados["alertas"]
    top_opp = dados["top_oportunidades"]
    top_risk = dados["top_riscos"]
    recs = dados["recomendacoes"]
    indices = dados["indices_setoriais"]

    score_medio = safe_float(scores["score_final"].mean()) if not scores.empty else 0
    pot_medio = safe_float(scores["score_potencial"].mean()) if not scores.empty else 0
    qtd_alertas = len(alertas)
    qtd_altos = len(alertas[alertas["severidade"].isin(["critico", "alto"])]) if not alertas.empty else 0

    opp = top_opp.iloc[0]["regiao_comercial"] if not top_opp.empty else "N/A"
    risk = top_risk.iloc[0]["regiao_comercial"] if not top_risk.empty else "N/A"

    lines = []
    lines.append(f"🐟 *Radar Pescados IA — Resumo Executivo ({uf})*")
    lines.append("")
    lines.append(f"📊 Score médio: *{br_num(score_medio)}*")
    lines.append(f"🌎 Potencial médio: *{br_num(pot_medio)}*")
    lines.append(f"🚨 Alertas ativos: *{qtd_alertas}* | críticos/altos: *{qtd_altos}*")
    lines.append("")
    lines.append(f"✅ Maior oportunidade: *{opp}*")
    lines.append(f"⚠️ Maior risco: *{risk}*")

    if not indices.empty:
        lines.append("")
        lines.append("🥩 *Setorial*")
        for _, row in indices.iterrows():
            lines.append(f"- {row['indice']}: *{br_num(row['score'])}*")

    if not recs.empty:
        lines.append("")
        lines.append("🎯 *Top recomendações*")
        for _, row in recs.head(5).iterrows():
            lines.append(f"- {row['regiao_comercial']}: {row['tipo_recomendacao']} | motor={row['motor_decisao']}")

    if not alertas.empty:
        lines.append("")
        lines.append("🚨 *Alertas principais*")
        for _, row in alertas.head(5).iterrows():
            lines.append(f"- {row['severidade'].upper()} | {row['area_responsavel']} | {row['regiao_comercial']}: {row['tipo_alerta']}")

    lines.append("")
    lines.append("_Leitura probabilística. Usar como apoio à decisão._")

    return "\n".join(lines)


def df_to_html_table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df.empty:
        return "<p><em>Sem dados.</em></p>"
    return df.head(max_rows).to_html(index=False, border=0, classes="table")


def montar_html_relatorio(dados: dict, resumo: str, whatsapp: str, uf: str = "MG") -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Radar Pescados IA — Relatório Executivo</title>
<style>
body {{
    font-family: Arial, sans-serif;
    margin: 32px;
    color: #222;
}}
h1, h2 {{
    color: #0f172a;
}}
.card {{
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 18px;
    background: #fafafa;
}}
pre {{
    white-space: pre-wrap;
    background: #111827;
    color: #f9fafb;
    padding: 16px;
    border-radius: 10px;
}}
.table {{
    border-collapse: collapse;
    width: 100%;
    font-size: 13px;
}}
.table th {{
    background: #1f2937;
    color: white;
    padding: 8px;
    text-align: left;
}}
.table td {{
    border-bottom: 1px solid #ddd;
    padding: 8px;
}}
.badge {{
    display: inline-block;
    padding: 4px 8px;
    border-radius: 8px;
    background: #e5e7eb;
}}
</style>
</head>
<body>
<h1>🐟 Radar Pescados IA — Relatório Executivo</h1>
<p><span class="badge">UF: {uf}</span> <span class="badge">Gerado em: {now}</span></p>

<div class="card">
<h2>Resumo Executivo</h2>
<pre>{resumo}</pre>
</div>

<div class="card">
<h2>Mensagem pronta para WhatsApp</h2>
<pre>{whatsapp}</pre>
</div>

<div class="card">
<h2>Top oportunidades</h2>
{df_to_html_table(dados['top_oportunidades'])}
</div>

<div class="card">
<h2>Top riscos</h2>
{df_to_html_table(dados['top_riscos'])}
</div>

<div class="card">
<h2>Recomendações</h2>
{df_to_html_table(dados['recomendacoes'])}
</div>

<div class="card">
<h2>Alertas ativos</h2>
{df_to_html_table(dados['alertas'])}
</div>

<div class="card">
<h2>Índices setoriais</h2>
{df_to_html_table(dados['indices_setoriais'])}
</div>

<div class="card">
<h2>What-if recentes</h2>
{df_to_html_table(dados['whatif'])}
</div>

<div class="card">
<h2>Fontes reais</h2>
{df_to_html_table(dados['fontes_reais'])}
</div>

</body>
</html>
"""
    return html


def exportar_excel(dados: dict, path: Path, resumo: str, whatsapp: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame({"Resumo Executivo": [resumo]}).to_excel(writer, sheet_name="Resumo", index=False)
        pd.DataFrame({"WhatsApp": [whatsapp]}).to_excel(writer, sheet_name="WhatsApp", index=False)

        for sheet, df in [
            ("Vendas_Resumo", dados["vendas_resumo"]),
            ("Top_Oportunidades", dados["top_oportunidades"]),
            ("Top_Riscos", dados["top_riscos"]),
            ("Scores", dados["scores"]),
            ("Recomendacoes", dados["recomendacoes"]),
            ("Alertas", dados["alertas"]),
            ("Alertas_Area", dados["alertas_area"]),
            ("Setorial", dados["indices_setoriais"]),
            ("WhatIf", dados["whatif"]),
            ("Fontes_Reais", dados["fontes_reais"]),
        ]:
            safe_sheet = sheet[:31]
            df.to_excel(writer, sheet_name=safe_sheet, index=False)


def salvar_relatorio_banco(
    uf: str,
    titulo: str,
    resumo: str,
    whatsapp: str,
    html: str,
    caminho_excel: str,
    caminho_html: str,
    parametros: dict,
    indicadores: dict,
    usuario: str | None = None,
) -> int:
    engine = get_engine()

    with engine.begin() as conn:
        inserted_id = conn.execute(text("""
            INSERT INTO app.fato_relatorio_executivo (
                periodo_inicio,
                periodo_fim,
                uf,
                tipo_relatorio,
                titulo,
                resumo_executivo,
                mensagem_whatsapp,
                html_relatorio,
                caminho_excel,
                caminho_html,
                parametros,
                indicadores,
                usuario
            )
            VALUES (
                :periodo_inicio,
                :periodo_fim,
                :uf,
                'executivo',
                :titulo,
                :resumo_executivo,
                :mensagem_whatsapp,
                :html_relatorio,
                :caminho_excel,
                :caminho_html,
                CAST(:parametros AS JSONB),
                CAST(:indicadores AS JSONB),
                :usuario
            )
            RETURNING id
        """), {
            "periodo_inicio": clean_date_or_none(parametros.get("periodo_inicio")),
            "periodo_fim": clean_date_or_none(parametros.get("periodo_fim")),
            "uf": uf,
            "titulo": titulo,
            "resumo_executivo": resumo,
            "mensagem_whatsapp": whatsapp,
            "html_relatorio": html,
            "caminho_excel": caminho_excel,
            "caminho_html": caminho_html,
            "parametros": json.dumps(parametros, ensure_ascii=False),
            "indicadores": json.dumps(indicadores, ensure_ascii=False),
            "usuario": usuario,
        }).scalar()

    return int(inserted_id)


def gerar_relatorio_executivo(
    uf: str = "MG",
    salvar_banco: bool = True,
    usuario: str | None = None,
) -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    dados = carregar_dados_relatorio(uf=uf)
    resumo = montar_resumo_executivo(dados, uf=uf)
    whatsapp = montar_mensagem_whatsapp(dados, uf=uf)
    html = montar_html_relatorio(dados, resumo, whatsapp, uf=uf)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"relatorio_executivo_{uf}_{timestamp}".lower()

    excel_path = OUTPUT_DIR / f"{base_name}.xlsx"
    html_path = OUTPUT_DIR / f"{base_name}.html"

    exportar_excel(dados, excel_path, resumo, whatsapp)
    html_path.write_text(html, encoding="utf-8")

    scores = dados["scores"]
    alertas = dados["alertas"]

    indicadores = {
        "score_medio": safe_float(scores["score_final"].mean()) if not scores.empty else 0,
        "potencial_medio": safe_float(scores["score_potencial"].mean()) if not scores.empty else 0,
        "risco_medio": safe_float(scores["score_risco"].mean()) if not scores.empty else 0,
        "qtd_alertas": len(alertas),
        "qtd_alertas_criticos": len(alertas[alertas["severidade"] == "critico"]) if not alertas.empty else 0,
        "qtd_alertas_altos": len(alertas[alertas["severidade"] == "alto"]) if not alertas.empty else 0,
    }

    vendas = dados["vendas_resumo"].iloc[0] if not dados["vendas_resumo"].empty else {}
    parametros = {
        "uf": uf,
        "periodo_inicio": clean_date_or_none(vendas.get("primeira_data") if hasattr(vendas, "get") else None),
        "periodo_fim": clean_date_or_none(vendas.get("ultima_data") if hasattr(vendas, "get") else None),
        "gerado_em": datetime.now().isoformat(),
    }

    titulo = f"Relatório Executivo Radar Pescados IA — {uf}"

    relatorio_id = None
    if salvar_banco:
        relatorio_id = salvar_relatorio_banco(
            uf=uf,
            titulo=titulo,
            resumo=resumo,
            whatsapp=whatsapp,
            html=html,
            caminho_excel=str(excel_path),
            caminho_html=str(html_path),
            parametros=parametros,
            indicadores=indicadores,
            usuario=usuario,
        )

    return {
        "id": relatorio_id,
        "titulo": titulo,
        "uf": uf,
        "resumo": resumo,
        "whatsapp": whatsapp,
        "html": html,
        "excel_path": str(excel_path),
        "html_path": str(html_path),
        "indicadores": indicadores,
        "parametros": parametros,
    }


def carregar_relatorios_recentes(limit: int = 20) -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            id,
            data_geracao,
            periodo_inicio,
            periodo_fim,
            uf,
            tipo_relatorio,
            titulo,
            status,
            usuario,
            caminho_excel,
            caminho_html
        FROM app.vw_relatorios_executivos_recentes
        LIMIT :limit
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"limit": limit})
