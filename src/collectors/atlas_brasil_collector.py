# Coluna histórica Atlas Brasil: IDHM_R
# Coluna histórica Atlas Brasil: IDHM_L
# Planilha histórica Atlas Brasil: MUN 91-00-10

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from pathlib import Path
import re
import tempfile
import unicodedata
import zipfile

import pandas as pd
import requests


@dataclass
class AtlasBrasilResult:
    df: pd.DataFrame
    metadata: dict


class AtlasBrasilCollector:
    """Coletor automático de IDHM municipal.

    Ordem das tentativas:
    1. Jina Reader em cima da página pública do PNUD/UNDP.
    2. Página PNUD/UNDP direta.
    3. XLSX bruto clássico do Atlas Brasil.
    4. API pública do dados.gov.br.
    5. URL extra passada pelo usuário.
    """

    undp_url = "https://www.undp.org/pt/brazil/idhm-municipios-2010"
    jina_undp_url = "https://r.jina.ai/https://www.undp.org/pt/brazil/idhm-municipios-2010"

    direct_raw_urls = [
        "http://atlasbrasil.org.br/2013/data/rawData/atlas2013_dadosbrutos_pt.xlsx",
        "https://atlasbrasil.org.br/2013/data/rawData/atlas2013_dadosbrutos_pt.xlsx",
        "https://www.atlasbrasil.org.br/2013/data/rawData/atlas2013_dadosbrutos_pt.xlsx",
    ]

    dadosgov_dataset_page = "https://dados.gov.br/dados/conjuntos-dados/atlasbrasil"
    dadosgov_search_url = "https://dados.gov.br/dados/api/publico/conjuntos-dados"

    browser_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
    }

    def __init__(self, cache_dir: str | Path = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(self.browser_headers)

    @staticmethod
    def _normalize_text(value: str) -> str:
        value = "" if value is None else str(value)
        value = unicodedata.normalize("NFKD", value)
        value = "".join(ch for ch in value if not unicodedata.combining(ch))
        value = re.sub(r"[^a-zA-Z0-9]+", " ", value).strip().lower()
        return value

    @staticmethod
    def _normalize_col(col: str) -> str:
        col = AtlasBrasilCollector._normalize_text(col)
        return re.sub(r"\s+", "_", col)

    @staticmethod
    def _clean_number(value):
        if value is None or pd.isna(value):
            return pd.NA
        text = str(value).strip().replace("º", "").replace("%", "")
        if text in ("", "-", "nan", "None"):
            return pd.NA
        if "," in text and "." in text:
            text = text.replace(".", "").replace(",", ".")
        elif "," in text:
            text = text.replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return pd.NA

    @staticmethod
    def _clean_int(value):
        if value is None or pd.isna(value):
            return pd.NA
        m = re.search(r"\d+", str(value))
        if not m:
            return pd.NA
        try:
            return int(m.group(0))
        except Exception:
            return pd.NA

    def _parse_markdown_or_text_idhm(self, text: str) -> pd.DataFrame:
        """Parseia texto/Markdown com linhas da tabela de IDHM.

        O Jina Reader pode devolver a tabela do PNUD em formatos diferentes:
        - Markdown com pipes;
        - texto corrido;
        - ranking com ou sem "º";
        - números com vírgula ou ponto decimal;
        - município no formato "Cidade (UF)".
        """
        records = []

        def number_tokens(value: str) -> list[str]:
            return re.findall(r"\b[01][\.,]\d{3}\b", value)

        def parse_num(value: str):
            return self._clean_number(value)

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            line = line.replace("\\|", "|")
            line = re.sub(r"\s+", " ", line)

            lower = line.lower()
            if ("idhm" in lower and "munic" in lower) or re.fullmatch(r"[-:\s|]+", line):
                continue

            # Caso Markdown table: ranking | município | idhm | renda | longevidade | educação
            if "|" in line:
                parts = [p.strip() for p in line.strip("|").split("|") if p.strip()]
                nums = []
                municipio_part = None
                rank_part = None

                for p in parts:
                    nums.extend(number_tokens(p))
                    if re.search(r"\([A-Z]{2}\)", p):
                        municipio_part = p
                    if rank_part is None and re.search(r"\d+", p) and ("º" in p or p.strip().isdigit()):
                        rank_part = p

                if municipio_part and len(nums) >= 4:
                    rm = re.search(r"^(.*?)\s*\(([A-Z]{2})\)\s*$", municipio_part)
                    if rm:
                        records.append({
                            "ranking": self._clean_int(rank_part),
                            "municipio": rm.group(1).strip(),
                            "uf": rm.group(2),
                            "ano": 2010,
                            "idhm": parse_num(nums[0]),
                            "idhm_renda": parse_num(nums[1]),
                            "idhm_longevidade": parse_num(nums[2]),
                            "idhm_educacao": parse_num(nums[3]),
                            "codigo_ibge": pd.NA,
                        })
                        continue

            # Caso texto corrido. Ranking opcional.
            m = re.search(
                r"(?:^|\s)(?:(\d+)\s*º?\s+)?(.+?)\s*\(([A-Z]{2})\)\s+([01][\.,]\d{3})\s+([01][\.,]\d{3})\s+([01][\.,]\d{3})\s+([01][\.,]\d{3})(?:\s|$)",
                line,
            )
            if m:
                records.append({
                    "ranking": self._clean_int(m.group(1)),
                    "municipio": m.group(2).strip(" -|"),
                    "uf": m.group(3),
                    "ano": 2010,
                    "idhm": parse_num(m.group(4)),
                    "idhm_renda": parse_num(m.group(5)),
                    "idhm_longevidade": parse_num(m.group(6)),
                    "idhm_educacao": parse_num(m.group(7)),
                    "codigo_ibge": pd.NA,
                })
                continue

            # Caso linha contenha município (UF) e os 4 números, mas com texto antes/depois.
            loc = re.search(r"([A-Za-zÀ-ÿ0-9 .'\-]+?)\s*\(([A-Z]{2})\)", line)
            nums = number_tokens(line)
            if loc and len(nums) >= 4:
                before = line[:loc.start()]
                rank = self._clean_int(before)
                records.append({
                    "ranking": rank,
                    "municipio": loc.group(1).strip(),
                    "uf": loc.group(2),
                    "ano": 2010,
                    "idhm": parse_num(nums[0]),
                    "idhm_renda": parse_num(nums[1]),
                    "idhm_longevidade": parse_num(nums[2]),
                    "idhm_educacao": parse_num(nums[3]),
                    "codigo_ibge": pd.NA,
                })

        df = pd.DataFrame(records)
        if not df.empty:
            df = df.dropna(subset=["idhm"]).drop_duplicates(subset=["municipio", "uf"], keep="first")
        return df

    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame()

        work = df.copy()
        work.columns = [self._normalize_col(c) for c in work.columns]
        cols = list(work.columns)

        ano_cols = [c for c in cols if c in ("ano", "year")]
        if ano_cols:
            anos = pd.to_numeric(work[ano_cols[0]], errors="coerce")
            if (anos == 2010).any():
                work = work[anos == 2010].copy()

        cols = list(work.columns)

        idhm_cols = [c for c in cols if c in ("idhm_2010", "idhm2010", "idhm")]
        if not idhm_cols:
            idhm_cols = [c for c in cols if "idhm" in c and ("2010" in c or c == "idhm")]
        if not idhm_cols:
            return pd.DataFrame()

        renda_cols = [c for c in cols if c in ("idhm_r", "idhm_renda", "idhm_renda_2010")]
        if not renda_cols:
            renda_cols = [c for c in cols if "idhm" in c and "renda" in c]

        longe_cols = [c for c in cols if c in ("idhm_l", "idhm_longevidade", "idhm_longevidade_2010")]
        if not longe_cols:
            longe_cols = [c for c in cols if "idhm" in c and ("longevidade" in c or "longev" in c)]

        educ_cols = [c for c in cols if c in ("idhm_e", "idhm_educacao", "idhm_educacao_2010")]
        if not educ_cols:
            educ_cols = [c for c in cols if "idhm" in c and ("educacao" in c or "educ" in c)]

        rank_cols = [c for c in cols if "rank" in c or "ranking" in c]

        cod_cols = [c for c in cols if c in ("codmun7", "cod_mun7", "codigo_ibge", "cod_ibge", "codigo_do_municipio")]
        if not cod_cols:
            cod_cols = [c for c in cols if ("cod" in c and ("mun" in c or "ibge" in c))]

        mun_cols = [c for c in cols if c in ("municipio", "nome_municipio", "municipio_nome")]
        if not mun_cols:
            mun_cols = [c for c in cols if "municipio" in c]

        uf_cols = [c for c in cols if c in ("uf", "sigla_uf", "estado")]

        out = pd.DataFrame()
        out["codigo_ibge"] = work[cod_cols[0]].astype(str).str.extract(r"(\d{6,7})")[0] if cod_cols else pd.NA

        municipio_raw = work[mun_cols[0]].astype(str) if mun_cols else pd.Series([pd.NA] * len(work))
        extracted = municipio_raw.str.extract(r"^(.*?)\s*\(([A-Z]{2})\)\s*$")
        out["municipio"] = extracted[0].fillna(municipio_raw).astype(str).str.strip()
        uf_from_mun = extracted[1]

        if uf_cols:
            uf_raw = work[uf_cols[0]].astype(str).str.upper()
            out["uf"] = uf_raw.str.extract(r"([A-Z]{2})")[0]
        else:
            out["uf"] = uf_from_mun

        out["ano"] = 2010
        out["idhm"] = work[idhm_cols[0]].map(self._clean_number)
        out["idhm_renda"] = work[renda_cols[0]].map(self._clean_number) if renda_cols else pd.NA
        out["idhm_longevidade"] = work[longe_cols[0]].map(self._clean_number) if longe_cols else pd.NA
        out["idhm_educacao"] = work[educ_cols[0]].map(self._clean_number) if educ_cols else pd.NA
        out["ranking"] = work[rank_cols[0]].map(self._clean_int) if rank_cols else pd.NA

        out = out.dropna(subset=["idhm"])
        out = out[(out["municipio"].notna()) | (out["codigo_ibge"].notna())]
        return out

    def _read_tables_from_html(self, html: str) -> list[pd.DataFrame]:
        try:
            return pd.read_html(StringIO(html))
        except Exception:
            return []

    def _read_file_tables(self, path: Path) -> list[pd.DataFrame]:
        dfs = []
        suffix = path.suffix.lower()

        if suffix in [".xlsx", ".xls"]:
            try:
                xls = pd.ExcelFile(path)
                sheet_names = list(xls.sheet_names)
                preferred = [s for s in sheet_names if "MUN" in str(s).upper() and "91" in str(s)]
                ordered = preferred + [s for s in sheet_names if s not in preferred]
                for sheet in ordered:
                    try:
                        dfs.append(pd.read_excel(path, sheet_name=sheet, dtype=str))
                    except Exception:
                        pass
            except Exception:
                pass

        elif suffix in [".csv", ".txt"]:
            for enc in ["utf-8", "latin1", "cp1252"]:
                for sep in [";", ",", "\t", "|"]:
                    try:
                        df = pd.read_csv(path, sep=sep, dtype=str, encoding=enc)
                        if len(df.columns) >= 3:
                            dfs.append(df)
                            return dfs
                    except Exception:
                        pass
            try:
                dfs.append(pd.read_csv(path, sep=None, engine="python", dtype=str))
            except Exception:
                pass

        return dfs

    def _extract_zip_tables(self, content: bytes) -> list[pd.DataFrame]:
        dfs = []
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            zpath = tmp / "atlas.zip"
            zpath.write_bytes(content)
            try:
                with zipfile.ZipFile(zpath) as z:
                    z.extractall(tmp)
            except Exception:
                return []
            for file in tmp.rglob("*"):
                if file.suffix.lower() in [".csv", ".txt", ".xlsx", ".xls"]:
                    dfs.extend(self._read_file_tables(file))
        return dfs

    def _try_url(self, url: str) -> tuple[pd.DataFrame, dict]:
        meta = {"url": url}
        try:
            resp = self.session.get(url, timeout=240, allow_redirects=True)
            meta["status_http"] = resp.status_code
            meta["content_type"] = resp.headers.get("content-type", "")

            if resp.status_code >= 400:
                return pd.DataFrame(), meta

            ctype = meta["content_type"].lower()
            lower = url.lower().split("?")[0]
            tables = []

            if "r.jina.ai" in lower:
                df_text = self._parse_markdown_or_text_idhm(resp.text)
                if not df_text.empty:
                    meta["qtd_registros"] = len(df_text)
                    meta["modo_parse"] = "jina_markdown_text"
                    return df_text, meta
                tables = self._read_tables_from_html(resp.text)

            elif lower.endswith(".zip") or "zip" in ctype:
                tables = self._extract_zip_tables(resp.content)
            elif lower.endswith((".xlsx", ".xls", ".csv", ".txt")):
                suffix = Path(lower).suffix or ".dat"
                fpath = self.cache_dir / f"atlas_brasil_download{suffix}"
                fpath.write_bytes(resp.content)
                tables = self._read_file_tables(fpath)
            else:
                tables = self._read_tables_from_html(resp.text)
                df_text = self._parse_markdown_or_text_idhm(resp.text)
                if not df_text.empty:
                    meta["qtd_registros"] = len(df_text)
                    meta["modo_parse"] = "html_text_regex"
                    return df_text, meta

            for table in tables:
                df = self._standardize_dataframe(table)
                if not df.empty:
                    meta["qtd_registros"] = len(df)
                    meta["modo_parse"] = "table"
                    return df, meta

            meta["erro"] = "Nenhuma tabela compatível com IDHM foi identificada."
            if "r.jina.ai" in lower:
                try:
                    debug_path = self.cache_dir / "idh_jina_reader_raw.txt"
                    debug_path.write_text(resp.text[:200000], encoding="utf-8")
                    meta["debug_file"] = str(debug_path)
                    meta["preview"] = resp.text[:1000]
                except Exception:
                    pass
            return pd.DataFrame(), meta

        except Exception as exc:
            meta["erro"] = str(exc)
            return pd.DataFrame(), meta

    def _extract_urls_from_json(self, obj):
        urls = []
        if isinstance(obj, dict):
            for _, value in obj.items():
                if isinstance(value, str) and value.startswith("http"):
                    if any(ext in value.lower() for ext in [".csv", ".xlsx", ".xls", ".zip", ".txt"]):
                        urls.append(value)
                else:
                    urls.extend(self._extract_urls_from_json(value))
        elif isinstance(obj, list):
            for item in obj:
                urls.extend(self._extract_urls_from_json(item))
        return urls

    def _discover_urls_dadosgov_api(self) -> tuple[list[str], dict]:
        attempts = []
        urls = []
        params_options = [
            {"nomeConjuntoDados": "atlasbrasil", "isPrivado": "false", "pagina": 1},
            {"titulo": "atlasbrasil", "isPrivado": "false", "pagina": 1},
            {"termo": "Atlas Brasil", "isPrivado": "false", "pagina": 1},
        ]
        for params in params_options:
            try:
                resp = self.session.get(self.dadosgov_search_url, params=params, timeout=120)
                attempts.append({"url": resp.url, "status_http": resp.status_code})
                if resp.status_code < 400:
                    data = resp.json()
                    urls.extend(self._extract_urls_from_json(data))
            except Exception as exc:
                attempts.append({"params": params, "erro": str(exc)})
        urls = list(dict.fromkeys(urls))
        return urls, {"attempts": attempts, "qtd_urls": len(urls)}

    def collect(self, extra_urls: list[str] | None = None) -> AtlasBrasilResult:
        errors = []

        candidate_urls = (
            list(extra_urls or [])
            + [self.jina_undp_url]
            + [self.undp_url]
            + self.direct_raw_urls
        )

        for url in candidate_urls:
            df, meta = self._try_url(url)
            if not df.empty:
                return AtlasBrasilResult(df=df, metadata={
                    "status": "OK",
                    "url_usada": url,
                    "qtd_registros": len(df),
                    "metodo": meta.get("modo_parse") or ("jina_reader" if "r.jina.ai" in url else "direct"),
                    "tentativas_anteriores": errors,
                })
            errors.append(meta)

        discovered_urls, api_meta = self._discover_urls_dadosgov_api()
        for url in discovered_urls:
            df, meta = self._try_url(url)
            if not df.empty:
                return AtlasBrasilResult(df=df, metadata={
                    "status": "OK",
                    "url_usada": url,
                    "qtd_registros": len(df),
                    "metodo": "dadosgov_api",
                    "tentativas_anteriores": errors,
                })
            errors.append(meta)

        return AtlasBrasilResult(df=pd.DataFrame(), metadata={
            "status": "FALHA",
            "dataset_page": self.dadosgov_dataset_page,
            "undp_url": self.undp_url,
            "jina_undp_url": self.jina_undp_url,
            "raw_xlsx_url": self.direct_raw_urls[0],
            "api_dadosgov": api_meta,
            "erros": errors,
            "observacao": (
                "Não foi possível carregar IDHM automaticamente nem via Jina Reader, nem via PNUD, "
                "nem via arquivo bruto do Atlas. Verifique bloqueio de internet/proxy ou use --url."
            ),
        })
