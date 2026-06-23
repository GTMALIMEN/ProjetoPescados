from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.config.settings import settings
from src.database.connection import get_engine
from src.utils.logs import get_logger


logger = get_logger(__name__)
ROOT_DIR = Path(__file__).resolve().parents[2]


@dataclass
class PipelineStep:
    ordem: int
    nome: str
    command: list[str]
    obrigatoria: bool = True
    enabled: bool = True


def _script(name: str) -> str:
    return str(ROOT_DIR / "scripts" / name)


def build_pipeline_steps(
    uf: str = "MG",
    usuario: str = "",
    init_db: bool = False,
    carregar_bcb: bool = True,
    carregar_ibge_localidades: bool = False,
    carregar_ibge_populacao: bool = False,
    carregar_comex: bool = False,
    comex_ano_inicio: int = 2020,
    comex_ano_fim: int = 2026,
    comex_delay: int = 15,
    conab_file: str | None = None,
    cepea_file: str | None = None,
    vendas_file: str | None = None,
    gerar_relatorio: bool = True,
    check_final: bool = True,
) -> list[PipelineStep]:
    py = sys.executable

    steps: list[PipelineStep] = []

    def add(nome: str, command: list[str], obrigatoria: bool = True, enabled: bool = True):
        steps.append(PipelineStep(len(steps) + 1, nome, command, obrigatoria, enabled))

    add("Aplicar Etapa 16 / estrutura pipeline", [py, _script("apply_etapa16.py")], True, True)

    add("Inicializar banco completo", [py, _script("init_db.py")], True, init_db)

    add("Carregar Banco Central", [py, _script("run_bcb_load.py")], False, carregar_bcb)

    add("Carregar IBGE Localidades", [py, _script("run_ibge_localidades.py")], False, carregar_ibge_localidades and (ROOT_DIR / "scripts/run_ibge_localidades.py").exists())

    add("Baixar malhas geográficas IBGE", [py, _script("baixar_malhas_ibge.py")], False, (ROOT_DIR / "scripts/baixar_malhas_ibge.py").exists())

    add("Carregar IBGE População", [py, _script("run_ibge_populacao.py")], False, carregar_ibge_populacao and (ROOT_DIR / "scripts/run_ibge_populacao.py").exists())
    add("Aplicar Regiões Comerciais MG", [py, _script("apply_regioes_mg.py")], False, (ROOT_DIR / "scripts/apply_regioes_mg.py").exists())


    add(
        "Carregar Comex Stat pescados",
        [py, _script("run_comex_pescados.py"), "--ano-inicio", str(comex_ano_inicio), "--ano-fim", str(comex_ano_fim), "--delay", str(comex_delay)],
        False,
        carregar_comex and (ROOT_DIR / "scripts/run_comex_pescados.py").exists(),
    )

    add(
        "Carregar CONAB arquivo",
        [py, _script("load_conab_file.py"), "--arquivo", conab_file or "", "--categoria", "graos_racao", "--produto-default", "Milho", "--uf-default", uf],
        False,
        bool(conab_file) and (ROOT_DIR / "scripts/load_conab_file.py").exists(),
    )

    add(
        "Carregar CEPEA manual oficial",
        [py, _script("load_cepea_manual_file.py"), "--criar-estrutura", "--substituir-tudo", "--arquivo", cepea_file or ""],
        False,
        bool(cepea_file) and (ROOT_DIR / "scripts/load_cepea_manual_file.py").exists(),
    )

    add(
        "Carregar vendas internas",
        [py, _script("load_vendas_file.py"), "--arquivo", vendas_file or ""],
        False,
        bool(vendas_file) and (ROOT_DIR / "scripts/load_vendas_file.py").exists(),
    )

    add("Calcular índices setoriais", [py, _script("calculate_indices_setoriais.py"), "--uf", uf, "--salvar"], True, True)

    add("Calcular potencial regional", [py, _script("calculate_potencial.py"), "--uf", uf, "--salvar"], True, (ROOT_DIR / "scripts/calculate_potencial.py").exists())

    add("Aplicar Etapa 9", [py, _script("apply_etapa9.py")], False, (ROOT_DIR / "scripts/apply_etapa9.py").exists())

    add("Aplicar Etapa 12", [py, _script("apply_etapa12.py")], False, (ROOT_DIR / "scripts/apply_etapa12.py").exists())

    add("Calcular scores", [py, _script("calculate_scores.py"), "--uf", uf, "--salvar"], True, True)

    add("Gerar recomendações", [py, _script("generate_recommendations.py"), "--uf", uf, "--salvar"], True, True)

    add("Aplicar Etapa 14", [py, _script("apply_etapa14.py")], False, (ROOT_DIR / "scripts/apply_etapa14.py").exists())

    add("Gerar alertas ativos", [py, _script("generate_active_alerts.py"), "--uf", uf, "--salvar"], True, (ROOT_DIR / "scripts/generate_active_alerts.py").exists())

    add("Aplicar Etapa 15", [py, _script("apply_etapa15.py")], False, (ROOT_DIR / "scripts/apply_etapa15.py").exists())

    add(
        "Gerar relatório executivo",
        [py, _script("generate_executive_report.py"), "--uf", uf, "--usuario", usuario or "pipeline"],
        False,
        gerar_relatorio and (ROOT_DIR / "scripts/generate_executive_report.py").exists(),
    )

    add("Check final do banco", [py, _script("check_db.py")], False, check_final and (ROOT_DIR / "scripts/check_db.py").exists())

    # Reordena somente steps criados, mantendo IGNORADOS registrados no log.
    return steps


def registrar_pipeline_inicio(
    pipeline_id: str,
    uf: str,
    usuario: str | None,
    parametros: dict,
) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.pipeline_execucao (
                pipeline_id,
                nome_pipeline,
                uf,
                ambiente,
                status,
                usuario,
                parametros,
                mensagem
            )
            VALUES (
                :pipeline_id,
                'pipeline_full',
                :uf,
                :ambiente,
                'INICIADO',
                :usuario,
                CAST(:parametros AS JSONB),
                'Pipeline iniciado'
            )
        """), {
            "pipeline_id": pipeline_id,
            "uf": uf,
            "ambiente": settings.app_env,
            "usuario": usuario,
            "parametros": json.dumps(parametros, ensure_ascii=False),
        })


def registrar_pipeline_fim(
    pipeline_id: str,
    status: str,
    tempo_total: float,
    mensagem: str,
) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE app.pipeline_execucao
            SET status = :status,
                finalizado_em = NOW(),
                tempo_total_segundos = :tempo_total,
                mensagem = :mensagem
            WHERE pipeline_id = :pipeline_id
        """), {
            "pipeline_id": pipeline_id,
            "status": status,
            "tempo_total": tempo_total,
            "mensagem": mensagem,
        })


def registrar_etapa(
    pipeline_id: str,
    step: PipelineStep,
    status: str,
    stdout: str = "",
    stderr: str = "",
    tempo: float | None = None,
    mensagem: str = "",
) -> None:
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app.pipeline_etapa_execucao (
                pipeline_id,
                ordem,
                nome_etapa,
                comando,
                obrigatoria,
                status,
                iniciado_em,
                finalizado_em,
                tempo_segundos,
                stdout,
                stderr,
                mensagem
            )
            VALUES (
                :pipeline_id,
                :ordem,
                :nome_etapa,
                :comando,
                :obrigatoria,
                :status,
                CASE WHEN :status IN ('INICIADO', 'SUCESSO', 'ERRO') THEN NOW() ELSE NULL END,
                CASE WHEN :status IN ('SUCESSO', 'ERRO', 'IGNORADO') THEN NOW() ELSE NULL END,
                :tempo_segundos,
                :stdout,
                :stderr,
                :mensagem
            )
        """), {
            "pipeline_id": pipeline_id,
            "ordem": step.ordem,
            "nome_etapa": step.nome,
            "comando": " ".join(step.command),
            "obrigatoria": step.obrigatoria,
            "status": status,
            "tempo_segundos": tempo,
            "stdout": stdout[-12000:] if stdout else "",
            "stderr": stderr[-12000:] if stderr else "",
            "mensagem": mensagem,
        })


def executar_comando(step: PipelineStep, timeout: int = 1800) -> tuple[str, str, float, int]:
    """
    Executa etapa do pipeline com encoding seguro no Windows.

    Sem isso, subprocessos que imprimem emojis ou acentos podem quebrar com:
    UnicodeEncodeError: 'charmap' codec can't encode character ...

    A correção força UTF-8 nos scripts filhos e também lê stdout/stderr
    com errors='replace' para impedir quebra por caractere inválido.
    """
    start = time.perf_counter()

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    proc = subprocess.run(
        step.command,
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    elapsed = time.perf_counter() - start
    return proc.stdout or "", proc.stderr or "", elapsed, proc.returncode


def run_pipeline(
    uf: str = "MG",
    usuario: str = "",
    init_db: bool = False,
    carregar_bcb: bool = True,
    carregar_ibge_localidades: bool = False,
    carregar_ibge_populacao: bool = False,
    carregar_comex: bool = False,
    comex_ano_inicio: int = 2020,
    comex_ano_fim: int = 2026,
    comex_delay: int = 15,
    conab_file: str | None = None,
    cepea_file: str | None = None,
    vendas_file: str | None = None,
    gerar_relatorio: bool = True,
    check_final: bool = True,
    parar_no_erro: bool = True,
) -> dict:
    pipeline_id = str(uuid.uuid4())
    start_total = time.perf_counter()

    parametros = {
        "uf": uf,
        "usuario": usuario,
        "init_db": init_db,
        "carregar_bcb": carregar_bcb,
        "carregar_ibge_localidades": carregar_ibge_localidades,
        "carregar_ibge_populacao": carregar_ibge_populacao,
        "carregar_comex": carregar_comex,
        "comex_ano_inicio": comex_ano_inicio,
        "comex_ano_fim": comex_ano_fim,
        "comex_delay": comex_delay,
        "conab_file": conab_file,
        "cepea_file": cepea_file,
        "vendas_file": vendas_file,
        "gerar_relatorio": gerar_relatorio,
        "check_final": check_final,
        "parar_no_erro": parar_no_erro,
    }

    # Garante tabela da etapa 16 se ainda não existir.
    apply_sql = ROOT_DIR / "src/database/etapa16_pipeline.sql"
    if apply_sql.exists():
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text(apply_sql.read_text(encoding="utf-8")))

    registrar_pipeline_inicio(pipeline_id, uf, usuario, parametros)

    steps = build_pipeline_steps(
        uf=uf,
        usuario=usuario,
        init_db=init_db,
        carregar_bcb=carregar_bcb,
        carregar_ibge_localidades=carregar_ibge_localidades,
        carregar_ibge_populacao=carregar_ibge_populacao,
        carregar_comex=carregar_comex,
        comex_ano_inicio=comex_ano_inicio,
        comex_ano_fim=comex_ano_fim,
        comex_delay=comex_delay,
        conab_file=conab_file,
        cepea_file=cepea_file,
        vendas_file=vendas_file,
        gerar_relatorio=gerar_relatorio,
        check_final=check_final,
    )

    resultados = []
    has_error = False
    mandatory_error = False

    print(f"\n🚀 Pipeline iniciado | id={pipeline_id}")
    print(f"UF={uf} | usuário={usuario or 'N/A'}")

    for step in steps:
        if not step.enabled:
            print(f"⏭️  [{step.ordem}] {step.nome} | IGNORADO")
            registrar_etapa(pipeline_id, step, "IGNORADO", mensagem="Etapa desabilitada ou script não encontrado.")
            resultados.append({"ordem": step.ordem, "nome": step.nome, "status": "IGNORADO"})
            continue

        print(f"\n▶️  [{step.ordem}] {step.nome}")
        print("   " + " ".join(step.command))

        try:
            stdout, stderr, elapsed, code = executar_comando(step)

            if code == 0:
                print(f"✅ [{step.ordem}] {step.nome} | {elapsed:.2f}s")
                if stdout.strip():
                    print(stdout[-2000:])
                registrar_etapa(pipeline_id, step, "SUCESSO", stdout, stderr, elapsed, "Etapa concluída.")
                resultados.append({"ordem": step.ordem, "nome": step.nome, "status": "SUCESSO", "tempo": elapsed})
            else:
                has_error = True
                if step.obrigatoria:
                    mandatory_error = True

                print(f"❌ [{step.ordem}] {step.nome} | código={code} | {elapsed:.2f}s")
                if stderr.strip():
                    print(stderr[-3000:])
                registrar_etapa(
                    pipeline_id,
                    step,
                    "ERRO",
                    stdout,
                    stderr,
                    elapsed,
                    f"Etapa falhou com código {code}.",
                )
                resultados.append({"ordem": step.ordem, "nome": step.nome, "status": "ERRO", "tempo": elapsed, "code": code})

                if parar_no_erro and step.obrigatoria:
                    print("🛑 Pipeline interrompido por erro em etapa obrigatória.")
                    break

        except subprocess.TimeoutExpired as exc:
            has_error = True
            if step.obrigatoria:
                mandatory_error = True

            msg = f"Timeout na etapa após {exc.timeout}s."
            print(f"⏱️ [{step.ordem}] {step.nome} | {msg}")
            registrar_etapa(pipeline_id, step, "ERRO", exc.stdout or "", exc.stderr or "", exc.timeout, msg)
            resultados.append({"ordem": step.ordem, "nome": step.nome, "status": "ERRO", "erro": msg})

            if parar_no_erro and step.obrigatoria:
                break

        except Exception as exc:
            has_error = True
            if step.obrigatoria:
                mandatory_error = True

            msg = f"Erro inesperado: {exc}"
            print(f"❌ [{step.ordem}] {step.nome} | {msg}")
            registrar_etapa(pipeline_id, step, "ERRO", "", str(exc), None, msg)
            resultados.append({"ordem": step.ordem, "nome": step.nome, "status": "ERRO", "erro": msg})

            if parar_no_erro and step.obrigatoria:
                break

    tempo_total = time.perf_counter() - start_total

    if mandatory_error:
        status_final = "ERRO"
        mensagem = "Pipeline finalizado com erro em etapa obrigatória."
    elif has_error:
        status_final = "PARCIAL"
        mensagem = "Pipeline finalizado com erro em etapa opcional."
    else:
        status_final = "SUCESSO"
        mensagem = "Pipeline finalizado com sucesso."

    registrar_pipeline_fim(pipeline_id, status_final, tempo_total, mensagem)

    print(f"\n🏁 Pipeline finalizado | status={status_final} | tempo={tempo_total:.2f}s | id={pipeline_id}")

    return {
        "pipeline_id": pipeline_id,
        "status": status_final,
        "mensagem": mensagem,
        "tempo_total_segundos": tempo_total,
        "resultados": resultados,
    }


def carregar_pipeline_execucoes(limit: int = 30) -> pd.DataFrame:
    engine = get_engine()
    sql = """
        SELECT
            id,
            pipeline_id,
            nome_pipeline,
            uf,
            ambiente,
            status,
            iniciado_em,
            finalizado_em,
            tempo_total_segundos,
            usuario,
            mensagem
        FROM app.vw_pipeline_ultimas_execucoes
        LIMIT :limit
    """
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params={"limit": limit})


def carregar_pipeline_etapas(pipeline_id: str | None = None, limit: int = 200) -> pd.DataFrame:
    engine = get_engine()

    if pipeline_id:
        sql = """
            SELECT
                pipeline_id,
                nome_pipeline,
                status_pipeline,
                ordem,
                nome_etapa,
                obrigatoria,
                status,
                tempo_segundos,
                mensagem,
                iniciado_em,
                finalizado_em
            FROM app.vw_pipeline_etapas_recentes
            WHERE pipeline_id = :pipeline_id
            ORDER BY ordem
        """
        params = {"pipeline_id": pipeline_id}
    else:
        sql = """
            SELECT
                pipeline_id,
                nome_pipeline,
                status_pipeline,
                ordem,
                nome_etapa,
                obrigatoria,
                status,
                tempo_segundos,
                mensagem,
                iniciado_em,
                finalizado_em
            FROM app.vw_pipeline_etapas_recentes
            LIMIT :limit
        """
        params = {"limit": limit}

    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params=params)


def carregar_pipeline_saude() -> dict:
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(text("SELECT * FROM app.vw_pipeline_saude")).mappings().first()
    return dict(row or {})


def main():
    parser = argparse.ArgumentParser(description="Executar Pipeline Mestre do Radar Pescados IA")
    parser.add_argument("--uf", default="MG")
    parser.add_argument("--usuario", default="pipeline")
    parser.add_argument("--init-db", action="store_true")
    parser.add_argument("--sem-bcb", action="store_true")
    parser.add_argument("--ibge-localidades", action="store_true")
    parser.add_argument("--ibge-populacao", action="store_true")
    parser.add_argument("--comex", action="store_true")
    parser.add_argument("--comex-ano-inicio", type=int, default=2020)
    parser.add_argument("--comex-ano-fim", type=int, default=2026)
    parser.add_argument("--comex-delay", type=int, default=15)
    parser.add_argument("--conab-file", default=None)
    parser.add_argument("--cepea-file", default=None)
    parser.add_argument("--vendas-file", default=None)
    parser.add_argument("--sem-relatorio", action="store_true")
    parser.add_argument("--sem-check", action="store_true")
    parser.add_argument("--continuar-no-erro", action="store_true")

    args = parser.parse_args()

    run_pipeline(
        uf=args.uf,
        usuario=args.usuario,
        init_db=args.init_db,
        carregar_bcb=not args.sem_bcb,
        carregar_ibge_localidades=args.ibge_localidades,
        carregar_ibge_populacao=args.ibge_populacao,
        carregar_comex=args.comex,
        comex_ano_inicio=args.comex_ano_inicio,
        comex_ano_fim=args.comex_ano_fim,
        comex_delay=args.comex_delay,
        conab_file=args.conab_file,
        cepea_file=args.cepea_file,
        vendas_file=args.vendas_file,
        gerar_relatorio=not args.sem_relatorio,
        check_final=not args.sem_check,
        parar_no_erro=not args.continuar_no_erro,
    )


if __name__ == "__main__":
    main()
