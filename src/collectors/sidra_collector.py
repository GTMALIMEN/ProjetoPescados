from __future__ import annotations

import requests
import pandas as pd

from src.utils.retry import retry_api


class SidraCollector:
    """Coletor genérico para API SIDRA/IBGE.

    MVP da Etapa 8:
    - População residente estimada por município: tabela 6579, variável 9324.
    """

    sidra_base_url = "https://apisidra.ibge.gov.br/values"
    agregados_base_url = "https://servicodados.ibge.gov.br/api/v3/agregados"

    @retry_api()
    def _get_json(self, url: str, params: dict | None = None):
        headers = {
            "Accept": "application/json",
            "User-Agent": "radar-pescados-ia/1.0",
        }
        response = requests.get(url, params=params or {}, headers=headers, timeout=90)
        response.raise_for_status()
        return response.json(), {
            "url": response.url,
            "params": params or {},
            "status_http": response.status_code,
            "payload": response.json(),
        }

    def obter_ultimo_periodo(self, tabela: str) -> str:
        url = f"{self.agregados_base_url}/{tabela}/periodos"
        payload, _ = self._get_json(url)

        periodos = []
        for item in payload:
            pid = str(item.get("id") or item.get("nome") or "").strip()
            if pid.isdigit():
                periodos.append(pid)

        if periodos:
            return sorted(periodos)[-1]

        return "last"

    @staticmethod
    def _find_key(header: dict, terms: list[str], exact: bool = False) -> str | None:
        for key, value in header.items():
            label = str(value).lower()
            if exact:
                if any(label == term.lower() for term in terms):
                    return key
            else:
                if all(term.lower() in label for term in terms):
                    return key
        return None

    @staticmethod
    def _to_number(value):
        if value is None:
            return None
        text = str(value).strip()
        if text in ("", "-", "...", "X"):
            return None
        # SIDRA normalmente usa ponto decimal, mas deixamos robusto para vírgula.
        if "," in text and "." in text:
            text = text.replace(".", "").replace(",", ".")
        elif "," in text:
            text = text.replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return None

    def _parse_sidra_rows(
        self,
        payload: list[dict],
        tabela: str,
        indicador: str,
        categoria: str,
        unidade_padrao: str | None = None,
    ) -> pd.DataFrame:
        if not payload or len(payload) <= 1:
            return pd.DataFrame()

        header = payload[0]
        rows = payload[1:]

        key_valor = "V" if "V" in header else self._find_key(header, ["valor"])
        key_mun_cod = self._find_key(header, ["município", "código"]) or self._find_key(header, ["municipio", "codigo"])
        key_mun_nome = self._find_key(header, ["município"], exact=True) or self._find_key(header, ["municipio"], exact=True)
        key_periodo = self._find_key(header, ["ano", "código"]) or self._find_key(header, ["período", "código"]) or self._find_key(header, ["periodo", "codigo"])
        key_periodo_nome = self._find_key(header, ["ano"], exact=True) or self._find_key(header, ["período"], exact=True) or self._find_key(header, ["periodo"], exact=True)
        key_variavel_codigo = self._find_key(header, ["variável", "código"]) or self._find_key(header, ["variavel", "codigo"])
        key_variavel_nome = self._find_key(header, ["variável"], exact=True) or self._find_key(header, ["variavel"], exact=True)
        key_unidade = self._find_key(header, ["unidade", "medida"], exact=True) or self._find_key(header, ["unidade", "medida"])

        registros = []
        for row in rows:
            codigo_ibge = str(row.get(key_mun_cod) or "").strip() if key_mun_cod else None
            municipio = str(row.get(key_mun_nome) or "").strip() if key_mun_nome else None

            # Muitos retornos do SIDRA vêm como "Belo Horizonte - MG".
            uf = None
            if municipio and " - " in municipio:
                nome, uf_tmp = municipio.rsplit(" - ", 1)
                municipio = nome.strip()
                uf = uf_tmp.strip().upper()

            if not codigo_ibge:
                continue

            periodo = str(row.get(key_periodo) or row.get(key_periodo_nome) or "").strip()
            variavel_codigo = str(row.get(key_variavel_codigo) or "").strip() if key_variavel_codigo else ""
            variavel_nome = str(row.get(key_variavel_nome) or "").strip() if key_variavel_nome else ""
            unidade = str(row.get(key_unidade) or unidade_padrao or "").strip() if key_unidade or unidade_padrao else None
            valor = self._to_number(row.get(key_valor)) if key_valor else None

            registros.append(
                {
                    "fonte": "IBGE/SIDRA",
                    "tabela_sidra": str(tabela),
                    "variavel_codigo": variavel_codigo,
                    "variavel_nome": variavel_nome,
                    "periodo": periodo,
                    "codigo_ibge": codigo_ibge,
                    "municipio": municipio,
                    "uf": uf,
                    "indicador": indicador,
                    "categoria": categoria,
                    "valor": valor,
                    "unidade": unidade,
                }
            )

        df = pd.DataFrame(registros)
        if df.empty:
            return df

        return df.dropna(subset=["codigo_ibge", "valor"]).drop_duplicates(
            subset=["tabela_sidra", "variavel_codigo", "periodo", "codigo_ibge", "indicador"]
        )

    def coletar_populacao_estimada(self, periodo: str | None = None) -> tuple[pd.DataFrame, dict]:
        tabela = "6579"
        variavel = "9324"
        indicador = "População residente estimada"
        categoria = "demografia"

        if not periodo:
            periodo = self.obter_ultimo_periodo(tabela)

        # n6/all = municípios; v/9324 = população residente estimada.
        url = f"{self.sidra_base_url}/t/{tabela}/n6/all/v/{variavel}/p/{periodo}"
        payload, metadata = self._get_json(url, params={"formato": "json"})

        df = self._parse_sidra_rows(
            payload=payload,
            tabela=tabela,
            indicador=indicador,
            categoria=categoria,
            unidade_padrao="Pessoas",
        )
        metadata["indicador"] = indicador
        metadata["tabela_sidra"] = tabela
        metadata["variavel_codigo"] = variavel
        metadata["periodo"] = periodo

        return df, metadata
