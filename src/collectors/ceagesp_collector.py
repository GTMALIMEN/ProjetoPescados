
from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta
from io import StringIO
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup


class CeagespCollector:
    """Coletor automático CEAGESP com limite de tentativas.

    Formulário detectado em 2026:
    method=post, action="#cotacao", fields=["cot_grupo", "cot_data"].

    A página não expõe API pública estável, então o coletor:
    1. tenta tabela direta;
    2. tenta POST com cot_grupo=PESCADOS e cot_data=dd/mm/aaaa;
    3. tenta variações controladas;
    4. encerra rápido sem travar o pipeline.
    """

    base_url = "https://ceagesp.gov.br/cotacoes/"

    def __init__(self, timeout: int = 8, max_tentativas: int = 12):
        self.timeout = timeout
        self.max_tentativas = max_tentativas
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "radar-pescados-ia/2.0",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Referer": self.base_url,
        })

    def _to_number(self, value: Any):
        if value is None:
            return None
        text = str(value).strip().replace("R$", "").replace("\xa0", " ")
        if text in ("", "-", "...", "nan"):
            return None
        if "," in text and "." in text:
            text = text.replace(".", "").replace(",", ".")
        elif "," in text:
            text = text.replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return None

    def _business_dates(self, days_back: int = 14) -> list[date]:
        today = date.today()
        dates = []
        for i in range(0, days_back + 1):
            d = today - timedelta(days=i)
            if d.weekday() < 5:
                dates.append(d)
        return dates

    def _read_tables(self, html: str) -> list[pd.DataFrame]:
        try:
            return pd.read_html(StringIO(html))
        except Exception:
            return []

    def _table_to_records(self, table: pd.DataFrame, data_referencia: date, url: str) -> list[dict]:
        if table is None or table.empty:
            return []

        df = table.copy()
        df.columns = [str(c).strip().lower() for c in df.columns]

        def col_like(*terms):
            for col in df.columns:
                c = str(col).lower()
                if all(t in c for t in terms):
                    return col
            return None

        produto_col = col_like("produto") or col_like("mercadoria") or col_like("nome") or df.columns[0]
        unidade_col = col_like("unid") or col_like("embal")
        minimo_col = col_like("menor") or col_like("mín") or col_like("min")
        comum_col = col_like("comum")
        maximo_col = col_like("maior") or col_like("máx") or col_like("max")
        classificacao_col = col_like("class")

        if not (minimo_col or comum_col or maximo_col):
            return []

        rows = []
        for _, row in df.iterrows():
            produto = str(row.get(produto_col) or "").strip()
            if not produto or produto.lower() in ("nan", "produto", "mercadoria", "nome"):
                continue

            classificacao = str(row.get(classificacao_col) or "").strip() if classificacao_col else ""
            unidade = str(row.get(unidade_col) or "").strip() if unidade_col else ""
            chave_base = "|".join([str(data_referencia), produto, classificacao, unidade])
            chave = hashlib.sha256(chave_base.encode("utf-8")).hexdigest()

            rows.append({
                "chave_registro": chave,
                "data_coleta": datetime.now(),
                "data_referencia": data_referencia,
                "categoria": "Pescados",
                "produto": produto,
                "classificacao": classificacao or None,
                "unidade": unidade or None,
                "preco_minimo": self._to_number(row.get(minimo_col)) if minimo_col else None,
                "preco_comum": self._to_number(row.get(comum_col)) if comum_col else None,
                "preco_maximo": self._to_number(row.get(maximo_col)) if maximo_col else None,
                "fonte": "CEAGESP",
                "url_fonte": url,
                "hash_carga": chave,
            })
        return rows

    def _discover_candidates(self, html: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        options = []
        for opt in soup.find_all("option"):
            label = opt.get_text(" ", strip=True)
            value = opt.get("value")
            joined = f"{label} {value}".lower()
            if "pesc" in joined or any(x in joined for x in ["tilapia", "salm", "camarao", "pescada"]):
                options.append({"label": label, "value": value})

        forms = []
        for form in soup.find_all("form"):
            forms.append({
                "action": form.get("action") or self.base_url,
                "method": (form.get("method") or "get").lower(),
                "fields": [i.get("name") for i in form.find_all(["input", "select"]) if i.get("name")],
            })

        return {"options": options[:10], "forms": forms[:5]}

    def _try_request(self, payload: dict, method: str, data_ref: date) -> tuple[list[dict], str | None, str | None]:
        clean_payload = {k: v for k, v in payload.items() if not k.startswith("_")}
        try:
            if method == "post":
                resp = self.session.post(self.base_url, data=clean_payload, timeout=self.timeout)
            else:
                resp = self.session.get(self.base_url, params=clean_payload, timeout=self.timeout)

            tables = self._read_tables(resp.text)
            rows = []
            for table in tables:
                rows.extend(self._table_to_records(table, data_ref, resp.url))
            return rows, resp.url, resp.text[:500]
        except requests.RequestException as exc:
            return [], None, str(exc)
        except Exception as exc:
            return [], None, str(exc)

    def coletar_pescados_automatico(self, dias_busca: int = 14) -> tuple[pd.DataFrame, dict]:
        meta = {
            "url": self.base_url,
            "data_coleta": datetime.now().isoformat(),
            "timeout": self.timeout,
            "max_tentativas": self.max_tentativas,
            "dias_busca_solicitado": dias_busca,
        }

        try:
            home = self.session.get(self.base_url, timeout=self.timeout)
            home.raise_for_status()
        except Exception as exc:
            meta.update({"status": "FALHA", "erro": str(exc)})
            return pd.DataFrame(), meta

        direct_rows = []
        for table in self._read_tables(home.text):
            direct_rows.extend(self._table_to_records(table, date.today(), home.url))
        if direct_rows:
            meta.update({"status": "OK", "estrategia": "tabela_direta_home"})
            return pd.DataFrame(direct_rows), meta

        discovered = self._discover_candidates(home.text)
        meta["forms_detectados"] = discovered.get("forms", [])
        meta["opcoes_detectadas"] = discovered.get("options", [])

        product_values = [x.get("value") for x in discovered.get("options", []) if x.get("value")]
        if not product_values:
            product_values = ["PESCADOS"]

        dates = self._business_dates(min(dias_busca, 60))

        payloads = []
        for d in dates:
            for group in product_values[:3]:
                d_br = d.strftime("%d/%m/%Y")
                d_iso = d.strftime("%Y-%m-%d")

                # Formulário real detectado.
                payloads.append(("post", {"cot_grupo": group, "cot_data": d_br}, d, "post_cot_grupo_cot_data_br"))
                payloads.append(("post", {"cot_grupo": group, "cot_data": d_iso}, d, "post_cot_grupo_cot_data_iso"))

                # Variações defensivas.
                payloads.append(("get", {"cot_grupo": group, "cot_data": d_br}, d, "get_cot_grupo_cot_data_br"))
                payloads.append(("post", {"grupo": group, "data": d_br}, d, "post_grupo_data"))
                payloads.append(("post", {"categoria": group, "data": d_br}, d, "post_categoria_data"))

        tentativas = 0
        ultimos_erros = []

        for method, payload, dref, estrategia in payloads:
            if tentativas >= self.max_tentativas:
                break

            tentativas += 1
            rows, used_url, preview_or_error = self._try_request(payload, method=method, data_ref=dref)

            if rows:
                meta.update({
                    "status": "OK",
                    "estrategia": estrategia,
                    "tentativas": tentativas,
                    "url_usada": used_url,
                    "data_referencia": str(dref),
                    "payload_usado": payload,
                })
                return pd.DataFrame(rows), meta

            if preview_or_error:
                ultimos_erros.append({
                    "estrategia": estrategia,
                    "payload": payload,
                    "retorno_ou_erro": str(preview_or_error)[:300],
                })
                ultimos_erros = ultimos_erros[-5:]

        meta.update({
            "status": "SEM_DADOS",
            "tentativas": tentativas,
            "ultimas_tentativas": ultimos_erros,
            "observacao": (
                "CEAGESP não retornou tabela de preços com o formulário atual. "
                "A carga foi encerrada por limite seguro para não travar o pipeline."
            ),
        })
        return pd.DataFrame(), meta
