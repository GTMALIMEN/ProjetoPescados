from pathlib import Path
import sys
import pandas as pd
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.database.connection import get_engine

MODELOS_DIR = ROOT / "modelos_importacao"
MODELOS_DIR.mkdir(exist_ok=True)

TEMPLATES = {
    "scanntech_mercado_privado": {
        "arquivo": "modelo_scanntech_mercado_privado.xlsx",
        "tabela": "app.fato_mercado_privado",
        "obrigatorias": [
            "data_competencia",
            "uf",
            "microrregiao",
            "categoria",
            "valor_mercado",
            "volume_mercado",
        ],
        "opcionais": [
            "cidade",
            "produto",
            "marca",
            "ean",
            "canal",
            "preco_medio",
            "qtd_lojas",
            "fonte",
        ],
        "exemplo": {
            "data_competencia": "2025-01-01",
            "uf": "MG",
            "microrregiao": "Belo Horizonte",
            "categoria": "Tilápia",
            "valor_mercado": 150000.00,
            "volume_mercado": 8500.00,
            "cidade": "Belo Horizonte",
            "produto": "Tilápia Filé",
            "marca": "Marca Exemplo",
            "ean": "7890000000000",
            "canal": "Varejo",
            "preco_medio": 17.65,
            "qtd_lojas": 25,
            "fonte": "Scanntech",
        },
    },
    "curva_mercado_categoria": {
        "arquivo": "modelo_curva_mercado_categoria.xlsx",
        "tabela": "app.fato_curva_mercado_categoria",
        "obrigatorias": [
            "data_competencia",
            "uf",
            "microrregiao",
            "categoria",
            "valor",
            "volume",
        ],
        "opcionais": [
            "cidade",
            "produto",
            "preco_medio",
            "fonte",
        ],
        "exemplo": {
            "data_competencia": "2025-01-01",
            "uf": "MG",
            "microrregiao": "Belo Horizonte",
            "categoria": "Tilápia",
            "valor": 150000.00,
            "volume": 8500.00,
            "cidade": "Belo Horizonte",
            "produto": "Tilápia Filé",
            "preco_medio": 17.65,
            "fonte": "Scanntech",
        },
    },
    "key_account_lojas": {
        "arquivo": "modelo_key_account_lojas.xlsx",
        "tabela": "app.dim_key_account_loja",
        "obrigatorias": [
            "grupo_key_account",
            "loja",
            "cidade",
            "uf",
        ],
        "opcionais": [
            "cliente",
            "cnpj",
            "endereco",
            "numero",
            "bairro",
            "cep",
            "latitude",
            "longitude",
            "canal",
            "status",
        ],
        "exemplo": {
            "grupo_key_account": "Rede Exemplo",
            "loja": "Loja Centro",
            "cidade": "Belo Horizonte",
            "uf": "MG",
            "cliente": "Cliente Exemplo",
            "cnpj": "00.000.000/0001-00",
            "endereco": "Av. Exemplo",
            "numero": "100",
            "bairro": "Centro",
            "cep": "30000-000",
            "latitude": -19.9167,
            "longitude": -43.9345,
            "canal": "Key Account",
            "status": "Ativa",
        },
    },
    "receita_vendas_expansao": {
        "arquivo": "modelo_receita_vendas_expansao.xlsx",
        "tabela": "app.fato_receita_manual_expansao",
        "obrigatorias": [
            "parceiro",
            "cidade",
            "estado",
            "data_competencia",
            "grupo_produto",
            "vlr_total_liquido",
        ],
        "opcionais": [
            "produto",
            "categoria",
            "vendedor",
            "canal",
            "quantidade",
            "preco_medio",
        ],
        "exemplo": {
            "parceiro": "Cliente Exemplo",
            "cidade": "Belo Horizonte",
            "estado": "MG",
            "data_competencia": "2025-01-01",
            "grupo_produto": "Pescados",
            "vlr_total_liquido": 25000.00,
            "produto": "Tilápia",
            "categoria": "Tilápia",
            "vendedor": "Vendedor Exemplo",
            "canal": "Varejo",
            "quantidade": 1200,
            "preco_medio": 20.83,
        },
    },
    "compra_manual": {
        "arquivo": "modelo_compra_manual.xlsx",
        "tabela": "app.fato_compra_manual",
        "obrigatorias": [
            "data_competencia",
            "produto",
            "preco_compra",
        ],
        "opcionais": [
            "fornecedor",
            "marca",
            "categoria",
            "quantidade",
            "valor_total",
            "cidade",
            "uf",
            "unidade",
        ],
        "exemplo": {
            "data_competencia": "2025-01-01",
            "produto": "Tilápia",
            "preco_compra": 18.50,
            "fornecedor": "Fornecedor Exemplo",
            "marca": "Marca Exemplo",
            "categoria": "Tilápia",
            "quantidade": 1000,
            "valor_total": 18500.00,
            "cidade": "Belo Horizonte",
            "uf": "MG",
            "unidade": "KG",
        },
    },
    "ceagesp_pescados": {
        "arquivo": "modelo_ceagesp_pescados.xlsx",
        "tabela": "app.fato_ceagesp_pescados",
        "obrigatorias": [
            "data_cotacao",
            "produto",
            "preco_comum",
        ],
        "opcionais": [
            "classificacao",
            "unidade",
            "preco_min",
            "preco_max",
            "fonte",
        ],
        "exemplo": {
            "data_cotacao": "2025-01-01",
            "produto": "Tilápia",
            "preco_comum": 20.00,
            "classificacao": "Padrão",
            "unidade": "KG",
            "preco_min": 18.00,
            "preco_max": 22.00,
            "fonte": "CEAGESP",
        },
    },
    "previa_vendedores": {
        "arquivo": "modelo_previa_vendedores.xlsx",
        "tabela": "app.fato_previa_vendedores",
        "obrigatorias": [
            "vendedor",
            "produto",
            "preco",
            "quantidade",
            "receita",
        ],
        "opcionais": [
            "data_venda",
            "cliente",
            "cidade",
            "uf",
            "categoria",
            "status",
        ],
        "exemplo": {
            "vendedor": "Vendedor Exemplo",
            "produto": "Tilápia",
            "preco": 22.00,
            "quantidade": 500,
            "receita": 11000.00,
            "data_venda": "2025-01-01",
            "cliente": "Cliente Exemplo",
            "cidade": "Belo Horizonte",
            "uf": "MG",
            "categoria": "Tilápia",
            "status": "Previsto",
        },
    },
}

SQL = """
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.importacao_manual_log (
    id BIGSERIAL PRIMARY KEY,
    tipo_importacao TEXT NOT NULL,
    arquivo TEXT,
    status TEXT NOT NULL,
    registros_lidos INTEGER DEFAULT 0,
    registros_processados INTEGER DEFAULT 0,
    registros_rejeitados INTEGER DEFAULT 0,
    detalhe TEXT,
    usuario TEXT,
    executado_em TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.importacao_manual_rejeicoes (
    id BIGSERIAL PRIMARY KEY,
    tipo_importacao TEXT NOT NULL,
    arquivo TEXT,
    linha INTEGER,
    coluna TEXT,
    valor TEXT,
    motivo TEXT,
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.fato_mercado_privado (
    id BIGSERIAL PRIMARY KEY,
    data_competencia DATE,
    uf TEXT,
    cidade TEXT,
    microrregiao TEXT,
    categoria TEXT,
    produto TEXT,
    marca TEXT,
    ean TEXT,
    canal TEXT,
    valor_mercado NUMERIC,
    volume_mercado NUMERIC,
    preco_medio NUMERIC,
    qtd_lojas NUMERIC,
    fonte TEXT,
    fonte_arquivo TEXT,
    hash_linha TEXT,
    data_importacao TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.fato_curva_mercado_categoria (
    id BIGSERIAL PRIMARY KEY,
    data_competencia DATE,
    uf TEXT,
    cidade TEXT,
    microrregiao TEXT,
    categoria TEXT,
    produto TEXT,
    valor NUMERIC,
    volume NUMERIC,
    preco_medio NUMERIC,
    fonte TEXT,
    fonte_arquivo TEXT,
    hash_linha TEXT,
    data_importacao TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.dim_key_account_loja (
    id BIGSERIAL PRIMARY KEY,
    grupo_key_account TEXT,
    cliente TEXT,
    cnpj TEXT,
    loja TEXT,
    endereco TEXT,
    numero TEXT,
    bairro TEXT,
    cidade TEXT,
    uf TEXT,
    cep TEXT,
    latitude NUMERIC,
    longitude NUMERIC,
    canal TEXT,
    status TEXT,
    fonte_arquivo TEXT,
    hash_linha TEXT,
    data_importacao TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.fato_receita_manual_expansao (
    id BIGSERIAL PRIMARY KEY,
    parceiro TEXT,
    cidade TEXT,
    estado TEXT,
    data_competencia DATE,
    grupo_produto TEXT,
    produto TEXT,
    categoria TEXT,
    vendedor TEXT,
    canal TEXT,
    quantidade NUMERIC,
    preco_medio NUMERIC,
    vlr_total_liquido NUMERIC,
    fonte_arquivo TEXT,
    hash_linha TEXT,
    data_importacao TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.fato_compra_manual (
    id BIGSERIAL PRIMARY KEY,
    data_competencia DATE,
    fornecedor TEXT,
    marca TEXT,
    produto TEXT,
    categoria TEXT,
    preco_compra NUMERIC,
    quantidade NUMERIC,
    valor_total NUMERIC,
    cidade TEXT,
    uf TEXT,
    unidade TEXT,
    fonte_arquivo TEXT,
    hash_linha TEXT,
    data_importacao TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.fato_ceagesp_pescados (
    id BIGSERIAL PRIMARY KEY,
    data_cotacao DATE,
    produto TEXT,
    classificacao TEXT,
    unidade TEXT,
    preco_min NUMERIC,
    preco_comum NUMERIC,
    preco_max NUMERIC,
    fonte TEXT,
    fonte_arquivo TEXT,
    hash_linha TEXT,
    data_importacao TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.fato_previa_vendedores (
    id BIGSERIAL PRIMARY KEY,
    vendedor TEXT,
    produto TEXT,
    preco NUMERIC,
    quantidade NUMERIC,
    receita NUMERIC,
    data_venda DATE,
    cliente TEXT,
    cidade TEXT,
    uf TEXT,
    categoria TEXT,
    status TEXT,
    fonte_arquivo TEXT,
    hash_linha TEXT,
    data_importacao TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fato_mercado_privado_hash
ON app.fato_mercado_privado(hash_linha)
WHERE hash_linha IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_fato_curva_mercado_hash
ON app.fato_curva_mercado_categoria(hash_linha)
WHERE hash_linha IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_key_account_hash
ON app.dim_key_account_loja(hash_linha)
WHERE hash_linha IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_receita_manual_hash
ON app.fato_receita_manual_expansao(hash_linha)
WHERE hash_linha IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_compra_manual_hash
ON app.fato_compra_manual(hash_linha)
WHERE hash_linha IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_ceagesp_hash
ON app.fato_ceagesp_pescados(hash_linha)
WHERE hash_linha IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_previa_hash
ON app.fato_previa_vendedores(hash_linha)
WHERE hash_linha IS NOT NULL;
"""

def gerar_modelos():
    for nome, cfg in TEMPLATES.items():
        colunas = cfg["obrigatorias"] + cfg["opcionais"]
        exemplo = cfg["exemplo"]

        df_modelo = pd.DataFrame([[exemplo.get(c, "") for c in colunas]], columns=colunas)
        df_regras = pd.DataFrame({
            "coluna": colunas,
            "obrigatoria": ["SIM" if c in cfg["obrigatorias"] else "NÃO" for c in colunas],
            "observacao": [
                "Preenchimento obrigatório" if c in cfg["obrigatorias"] else "Opcional / recomendado"
                for c in colunas
            ],
        })

        path = MODELOS_DIR / cfg["arquivo"]

        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            df_modelo.to_excel(writer, index=False, sheet_name="Modelo")
            df_regras.to_excel(writer, index=False, sheet_name="Regras")

            wb = writer.book
            ws = wb["Modelo"]
            ws.freeze_panes = "A2"

            for cell in ws[1]:
                cell.font = cell.font.copy(bold=True)
                cell.fill = cell.fill.copy(fill_type="solid", fgColor="D9EAF7")

            for col in ws.columns:
                max_len = max(len(str(cell.value)) if cell.value is not None else 0 for cell in col)
                ws.column_dimensions[col[0].column_letter].width = min(max(max_len + 2, 14), 35)

        print(f"✅ Modelo gerado: {path}")

def verificar_banco():
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text(SQL))

        print("\\nVerificação das tabelas no Supabase/PostgreSQL:")
        for nome, cfg in TEMPLATES.items():
            schema, tabela = cfg["tabela"].split(".")
            cols = pd.read_sql(
                text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = :schema
                      AND table_name = :tabela
                """),
                conn,
                params={"schema": schema, "tabela": tabela},
            )["column_name"].tolist()

            faltantes = [c for c in cfg["obrigatorias"] if c not in cols]

            if faltantes:
                print(f"⚠️ {cfg['tabela']} faltando obrigatórias: {faltantes}")
            else:
                print(f"✅ {cfg['tabela']} OK")

        log_ok = pd.read_sql(
            text("""
                SELECT COUNT(*) AS qtd
                FROM information_schema.tables
                WHERE table_schema = 'app'
                  AND table_name = 'importacao_manual_log'
            """),
            conn,
        )["qtd"].iloc[0]

        if log_ok:
            print("✅ app.importacao_manual_log OK")
        else:
            print("⚠️ app.importacao_manual_log não encontrada")

def main():
    verificar_banco()
    gerar_modelos()
    print("\\n✅ Estrutura de uploads manuais validada/criada.")
    print(f"✅ Modelos Excel disponíveis em: {MODELOS_DIR}")

if __name__ == "__main__":
    main()
