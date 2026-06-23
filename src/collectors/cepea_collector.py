from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from io import StringIO
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup


class CepeaTilapiaCollector:
    """Coletor oficial da página pública do CEPEA para preços da tilápia.

    Fonte oficial usada:
    https://www.cepea.org.br/br/indicador/tilapia.aspx

    Observações importantes:
    - O CEPEA divulga tilápia por semana e por região.
    - O preço é R$/kg à vista pago ao produtor independente, conforme a
      metodologia CEPEA.
    - Não há indicador oficial de camarão nessa página; camarão deve ser CEAGESP,
      ComexStat, compra interna ou outra fonte, nunca CEPEA sem comprovação.
    """

    base_url = "https://www.cepea.org.br/br/indicador/tilapia.aspx"
    produto = "Tilápia"
    indicador = "preco_tilapia_cepea_produtor_independente"

    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "radar-pescados-ia/2.1 (+auditoria-fontes)",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        })

    @staticmethod
    def _norm_text(value: Any) -> str:
        if value is None or pd.isna(value):
            return ""
        text = str(value).replace("\xa0", " ").strip()
        return re.sub(r"\s+", " ", text)

    @staticmethod
    def _to_number(value: Any) -> float | None:
        text = CepeaTilapiaCollector._norm_text(value)
        if not text or text.lower() in {"nan", "-", "..."}:
            return None
        text = text.replace("R$", "").replace("%", "").replace(" ", "")
        if "," in text and "." in text:
            text = text.replace(".", "").replace(",", ".")
        elif "," in text:
            text = text.replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return None

    @staticmethod
    def _uf_por_regiao(regiao: str) -> str:
        r = CepeaTilapiaCollector._norm_text(regiao).lower()
        if "morada nova" in r or "triâng" in r or "triang" in r or "alto parana" in r:
            return "MG"
        if "paraná" in r or "parana" in r:
            return "PR"
        if "grandes lagos" in r:
            return "SP/MS"
        return "BR"

    @staticmethod
    def _parse_periodo(periodo: Any) -> tuple[date | None, date | None, str]:
        """Converte períodos CEPEA em data inicial/final.

        Exemplos esperados:
        - 15 - 19/06/2026
        - 08 - 12/06/2026
        - 29/06 - 03/07/2026
        - 30/12/2025 - 03/01/2026
        - 19/06/2026
        """
        text = CepeaTilapiaCollector._norm_text(periodo)
        text = text.replace("–", "-").replace("—", "-")
        text = re.sub(r"\s+-\s+", " - ", text)

        # dd/mm/yyyy - dd/mm/yyyy
        m = re.search(
            r"(?P<d1>\d{1,2})/(?P<m1>\d{1,2})/(?P<y1>\d{4})\s*-\s*"
            r"(?P<d2>\d{1,2})/(?P<m2>\d{1,2})/(?P<y2>\d{4})",
            text,
        )
        if m:
            try:
                ini = date(int(m.group("y1")), int(m.group("m1")), int(m.group("d1")))
                fim = date(int(m.group("y2")), int(m.group("m2")), int(m.group("d2")))
                return ini, fim, text
            except ValueError:
                return None, None, text

        # dd/mm - dd/mm/yyyy
        m = re.search(
            r"(?P<d1>\d{1,2})/(?P<m1>\d{1,2})\s*-\s*"
            r"(?P<d2>\d{1,2})/(?P<m2>\d{1,2})/(?P<y2>\d{4})",
            text,
        )
        if m:
            try:
                y2 = int(m.group("y2"))
                m1 = int(m.group("m1"))
                m2 = int(m.group("m2"))
                y1 = y2 - 1 if m1 > m2 else y2
                ini = date(y1, m1, int(m.group("d1")))
                fim = date(y2, m2, int(m.group("d2")))
                return ini, fim, text
            except ValueError:
                return None, None, text

        # dd - dd/mm/yyyy
        m = re.search(
            r"(?P<d1>\d{1,2})\s*-\s*(?P<d2>\d{1,2})/(?P<m2>\d{1,2})/(?P<y2>\d{4})",
            text,
        )
        if m:
            try:
                y2 = int(m.group("y2"))
                m2 = int(m.group("m2"))
                ini = date(y2, m2, int(m.group("d1")))
                fim = date(y2, m2, int(m.group("d2")))
                return ini, fim, text
            except ValueError:
                return None, None, text

        # dd/mm/yyyy
        m = re.search(r"(?P<d>\d{1,2})/(?P<m>\d{1,2})/(?P<y>\d{4})", text)
        if m:
            try:
                d = date(int(m.group("y")), int(m.group("m")), int(m.group("d")))
                return d, d, text
            except ValueError:
                return None, None, text

        return None, None, text

    @staticmethod
    def _find_column(df: pd.DataFrame, *terms: str) -> str | None:
        for col in df.columns:
            c = str(col).lower()
            if all(t.lower() in c for t in terms):
                return col
        return None

    def _parse_table(self, table: pd.DataFrame, url: str) -> list[dict]:
        if table is None or table.empty:
            return []

        df = table.copy()
        df.columns = [self._norm_text(c).lower() for c in df.columns]

        regiao_col = self._find_column(df, "regi") or self._find_column(df, "região")
        valor_col = self._find_column(df, "valor") or self._find_column(df, "r$/kg") or self._find_column(df, "r$")
        var_col = self._find_column(df, "var")

        # A coluna do período costuma vir sem nome/unnamed ou como primeira coluna.
        periodo_col = None
        for col in df.columns:
            if "unnamed" in str(col).lower() or str(col).strip() in {"", "data", "período", "periodo"}:
                periodo_col = col
                break
        if periodo_col is None and len(df.columns) >= 1:
            periodo_col = df.columns[0]

        if regiao_col is None or valor_col is None or periodo_col is None:
            return []

        rows: list[dict] = []
        for _, row in df.iterrows():
            regiao = self._norm_text(row.get(regiao_col))
            valor = self._to_number(row.get(valor_col))
            periodo_txt = self._norm_text(row.get(periodo_col))
            data_inicio, data_fim, periodo_original = self._parse_periodo(periodo_txt)

            if not regiao or not data_fim or valor is None:
                continue
            if regiao.lower() in {"região", "regiao", "nan"}:
                continue

            variacao = self._to_number(row.get(var_col)) if var_col else None
            uf = self._uf_por_regiao(regiao)
            chave_base = "|".join([
                "CEPEA",
                self.indicador,
                str(data_fim),
                regiao,
                self.produto,
                "R$/kg",
            ])
            chave = hashlib.sha256(chave_base.encode("utf-8")).hexdigest()

            rows.append({
                "data": data_fim,
                "fonte": "CEPEA",
                "indicador": self.indicador,
                "categoria": "proteina",
                "subcategoria": "oficial_site_produtor_independente",
                "produto": self.produto,
                "uf": uf,
                "regiao": regiao,
                "valor": valor,
                "unidade": "R$/kg",
                "periodicidade": "semanal",
                "data_inicio_periodo": data_inicio,
                "data_fim_periodo": data_fim,
                "periodo_original": periodo_original,
                "variacao_semana_pct": variacao,
                "url_fonte": url,
                "hash_fonte": chave,
            })
        return rows

    def coletar(self, limite_linhas: int | None = None) -> tuple[pd.DataFrame, dict]:
        meta = {
            "fonte": "CEPEA",
            "produto": self.produto,
            "url": self.base_url,
            "data_coleta": datetime.now().isoformat(),
            "metodo": "scraping_html_tabela_publica",
            "observacao": "Preço da tilápia CEPEA: R$/kg à vista pago ao produtor independente; divulgação semanal por região.",
        }

        try:
            resp = self.session.get(self.base_url, timeout=self.timeout)
            resp.raise_for_status()
        except Exception as exc:
            meta.update({"status": "FALHA_HTTP", "erro": str(exc)})
            return pd.DataFrame(), meta

        # Mantém uma extração de texto curta para auditoria sem gravar HTML inteiro.
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.find("title")
        meta["titulo_pagina"] = title.get_text(" ", strip=True) if title else ""
        meta["status_http"] = resp.status_code
        meta["url_final"] = resp.url

        try:
            tables = pd.read_html(StringIO(resp.text))
        except Exception as exc:
            meta.update({"status": "SEM_TABELA", "erro": str(exc)})
            return pd.DataFrame(), meta

        all_rows: list[dict] = []
        for table in tables:
            rows = self._parse_table(table, resp.url)
            all_rows.extend(rows)

        if limite_linhas is not None and limite_linhas > 0:
            all_rows = all_rows[:limite_linhas]

        df = pd.DataFrame(all_rows)
        if df.empty:
            meta.update({"status": "SEM_DADOS_COMPATIVEIS", "qtd_tabelas": len(tables)})
            return df, meta

        # Remove duplicidade defensiva.
        df = df.drop_duplicates(subset=["hash_fonte"]).sort_values(["data", "regiao"], ascending=[False, True])
        meta.update({
            "status": "OK",
            "qtd_tabelas": len(tables),
            "qtd_registros": len(df),
            "primeira_data": str(df["data"].min()),
            "ultima_data": str(df["data"].max()),
            "regioes": sorted(df["regiao"].dropna().unique().tolist()),
        })
        return df, meta
