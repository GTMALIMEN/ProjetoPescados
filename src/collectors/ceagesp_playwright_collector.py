
from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta
from io import StringIO
from typing import Any

import pandas as pd


class CeagespPlaywrightCollector:
    """Coletor CEAGESP via navegador headless.

    Usado quando requests não retorna a tabela, porque a página depende de
    comportamento de formulário/JS. O import do Playwright é lazy para não
    quebrar o projeto quando a dependência ainda não está instalada.
    """

    base_url = "https://ceagesp.gov.br/cotacoes/"

    def __init__(self, headless: bool = True, timeout_ms: int = 20000):
        self.headless = headless
        self.timeout_ms = timeout_ms

    @staticmethod
    def _to_number(value: Any):
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

    @staticmethod
    def datas_cotacao(dias_busca: int = 60) -> list[date]:
        """Datas candidatas: CEAGESP normalmente divulga segunda, quarta e sexta."""
        today = date.today()
        out = []
        for i in range(1, dias_busca + 1):
            d = today - timedelta(days=i)
            if d.weekday() in (0, 2, 4):
                out.append(d)
        return out

    def _tables_to_records(self, html: str, data_referencia: date, url: str) -> list[dict]:
        try:
            tables = pd.read_html(StringIO(html))
        except Exception:
            return []

        rows = []
        for table in tables:
            if table is None or table.empty:
                continue

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
                continue

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

    def coletar(self, dias_busca: int = 60, max_datas: int = 12) -> tuple[pd.DataFrame, dict]:
        try:
            from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
        except Exception as exc:
            return pd.DataFrame(), {
                "status": "FALTA_DEPENDENCIA",
                "erro": str(exc),
                "observacao": "Instale com: python -m pip install playwright && python -m playwright install chromium",
            }

        metadata = {
            "url": self.base_url,
            "modo": "playwright",
            "headless": self.headless,
            "timeout_ms": self.timeout_ms,
            "data_coleta": datetime.now().isoformat(),
        }

        datas = self.datas_cotacao(dias_busca=dias_busca)[:max_datas]
        erros = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page(locale="pt-BR")
            page.set_default_timeout(self.timeout_ms)

            try:
                page.goto(self.base_url, wait_until="networkidle")

                # Fecha/aceita cookie quando existir, mas não falha se não existir.
                for selector in [
                    "button:has-text('Aceitar')",
                    "button:has-text('SALVAR E ACEITAR')",
                    "text=Aceitar",
                ]:
                    try:
                        page.locator(selector).first.click(timeout=2000)
                        break
                    except Exception:
                        pass

                for d in datas:
                    d_br = d.strftime("%d/%m/%Y")
                    try:
                        page.goto(self.base_url, wait_until="networkidle")

                        # Seleciona categoria PESCADOS.
                        if page.locator("select[name='cot_grupo']").count() > 0:
                            page.select_option("select[name='cot_grupo']", value="PESCADOS")
                        else:
                            # fallback por texto se o select tiver outro nome
                            page.locator("select").last.select_option(label="PESCADOS")

                        # Preenche data.
                        if page.locator("input[name='cot_data']").count() > 0:
                            page.fill("input[name='cot_data']", d_br)
                        else:
                            # fallback: primeiro input parecido com data
                            filled = False
                            for sel in ["input[type='date']", "input[type='text']", "input"]:
                                try:
                                    page.locator(sel).last.fill(d_br, timeout=3000)
                                    filled = True
                                    break
                                except Exception:
                                    pass
                            if not filled:
                                raise RuntimeError("Campo de data não encontrado.")

                        # Submete formulário específico ou botão.
                        submitted = False
                        for sel in [
                            "form:has(select[name='cot_grupo']) button[type='submit']",
                            "form:has(select[name='cot_grupo']) input[type='submit']",
                            "button:has-text('Consultar')",
                            "input[value='Consultar']",
                            "text=Consultar",
                        ]:
                            try:
                                page.locator(sel).first.click(timeout=3000)
                                submitted = True
                                break
                            except Exception:
                                pass

                        if not submitted:
                            page.keyboard.press("Enter")

                        try:
                            page.wait_for_load_state("networkidle", timeout=self.timeout_ms)
                        except PlaywrightTimeoutError:
                            pass

                        # Pequena espera por renderização da tabela.
                        try:
                            page.wait_for_selector("table", timeout=5000)
                        except Exception:
                            pass

                        html = page.content()
                        rows = self._tables_to_records(html, d, page.url)
                        if rows:
                            browser.close()
                            metadata.update({
                                "status": "OK",
                                "data_referencia": str(d),
                                "data_referencia_br": d_br,
                                "qtd_registros": len(rows),
                            })
                            return pd.DataFrame(rows), metadata

                        erros.append({"data": d_br, "erro": "sem tabela compatível"})
                        erros = erros[-5:]

                    except Exception as exc:
                        erros.append({"data": d_br, "erro": str(exc)[:300]})
                        erros = erros[-5:]
                        continue

            finally:
                try:
                    browser.close()
                except Exception:
                    pass

        metadata.update({
            "status": "SEM_DADOS",
            "observacao": "Playwright abriu/submeteu a página, mas nenhuma tabela compatível foi encontrada.",
            "erros": erros,
        })
        return pd.DataFrame(), metadata
