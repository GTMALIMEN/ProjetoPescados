from pathlib import Path
import py_compile
import shutil

path = Path("scripts/carga_ibge_classes_renda_pof_6977.py")
backup = path.with_suffix(".py.bak_salvar_split")
shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")

start = txt.find("def salvar(pivot):")
end = txt.find("\ndef main():", start)

if start == -1 or end == -1:
    raise RuntimeError("Não encontrei a função salvar(pivot) para substituir.")

nova_funcao = r'''
def salvar(pivot):
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS app"))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS app.fato_classe_renda_oficial_regiao (
                id BIGSERIAL PRIMARY KEY,
                codigo_regiao TEXT,
                regiao_ibge TEXT,
                ano TEXT,
                classe_a_pct NUMERIC,
                classe_b_pct NUMERIC,
                classe_c_pct NUMERIC,
                classe_d_pct NUMERIC,
                classe_e_pct NUMERIC,
                salario_minimo_ref NUMERIC,
                fonte_classe_renda TEXT,
                nivel_fonte_classe_renda TEXT,
                metodo_classe_renda TEXT,
                data_carga TIMESTAMP DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            ALTER TABLE app.fato_classe_renda_oficial_regiao
                ADD COLUMN IF NOT EXISTS codigo_regiao TEXT,
                ADD COLUMN IF NOT EXISTS regiao_ibge TEXT,
                ADD COLUMN IF NOT EXISTS ano TEXT,
                ADD COLUMN IF NOT EXISTS classe_a_pct NUMERIC,
                ADD COLUMN IF NOT EXISTS classe_b_pct NUMERIC,
                ADD COLUMN IF NOT EXISTS classe_c_pct NUMERIC,
                ADD COLUMN IF NOT EXISTS classe_d_pct NUMERIC,
                ADD COLUMN IF NOT EXISTS classe_e_pct NUMERIC,
                ADD COLUMN IF NOT EXISTS salario_minimo_ref NUMERIC,
                ADD COLUMN IF NOT EXISTS fonte_classe_renda TEXT,
                ADD COLUMN IF NOT EXISTS nivel_fonte_classe_renda TEXT,
                ADD COLUMN IF NOT EXISTS metodo_classe_renda TEXT,
                ADD COLUMN IF NOT EXISTS data_carga TIMESTAMP DEFAULT NOW()
        """))

        conn.execute(
            text("""
                DELETE FROM app.fato_classe_renda_oficial_regiao
                WHERE fonte_classe_renda = :fonte
            """),
            {"fonte": FONTE}
        )

        for _, row in pivot.iterrows():
            conn.execute(text("""
                INSERT INTO app.fato_classe_renda_oficial_regiao (
                    codigo_regiao,
                    regiao_ibge,
                    ano,
                    classe_a_pct,
                    classe_b_pct,
                    classe_c_pct,
                    classe_d_pct,
                    classe_e_pct,
                    salario_minimo_ref,
                    fonte_classe_renda,
                    nivel_fonte_classe_renda,
                    metodo_classe_renda
                )
                VALUES (
                    :codigo_regiao,
                    :regiao_ibge,
                    :ano,
                    :classe_a_pct,
                    :classe_b_pct,
                    :classe_c_pct,
                    :classe_d_pct,
                    :classe_e_pct,
                    :salario_minimo_ref,
                    :fonte,
                    :nivel,
                    :metodo
                )
            """), {
                "codigo_regiao": str(row["codigo_regiao"]),
                "regiao_ibge": str(row["regiao_ibge"]),
                "ano": str(row["ano"]),
                "classe_a_pct": float(row["classe_a_pct"]),
                "classe_b_pct": float(row["classe_b_pct"]),
                "classe_c_pct": float(row["classe_c_pct"]),
                "classe_d_pct": float(row["classe_d_pct"]),
                "classe_e_pct": float(row["classe_e_pct"]),
                "salario_minimo_ref": float(row["salario_minimo_ref"]),
                "fonte": row["fonte_classe_renda"],
                "nivel": row["nivel_fonte_classe_renda"],
                "metodo": row["metodo_classe_renda"],
            })

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS app.auditoria_fonte_dados (
                id BIGSERIAL PRIMARY KEY,
                nome_fonte TEXT NOT NULL,
                tabela_destino TEXT,
                status TEXT NOT NULL,
                registros INTEGER DEFAULT 0,
                registros_distintos INTEGER DEFAULT 0,
                duplicatas INTEGER DEFAULT 0,
                nulos_criticos INTEGER DEFAULT 0,
                data_min DATE,
                data_max DATE,
                detalhe TEXT,
                executado_em TIMESTAMP DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            INSERT INTO app.auditoria_fonte_dados (
                nome_fonte,
                tabela_destino,
                status,
                registros,
                registros_distintos,
                duplicatas,
                nulos_criticos,
                detalhe
            )
            VALUES (
                :fonte,
                'app.fato_classe_renda_oficial_regiao',
                'OK',
                :registros,
                :distintos,
                0,
                0,
                :detalhe
            )
        """), {
            "fonte": FONTE,
            "registros": int(len(pivot)),
            "distintos": int(pivot["codigo_regiao"].nunique()),
            "detalhe": "Carga POF 2017-2018 N2 Sudeste com distribuição Classe A-E por rateio de faixas."
        })
'''

txt = txt[:start] + nova_funcao + txt[end:]

path.write_text(txt, encoding="utf-8")
py_compile.compile(str(path), doraise=True)

print("✅ Função salvar(pivot) corrigida.")
print("✅ SQL separado em comandos individuais.")
print("✅ Script compilando corretamente.")
print("Backup criado em:", backup)
