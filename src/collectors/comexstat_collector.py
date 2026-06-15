from __future__ import annotations

import re
import time

import requests
import pandas as pd


class ComexStatCollector:
    """
    Coletor da API Comex Stat.

    Ajustes:
    - Endpoint usa /general?language=pt.
    - Período em AAAA-MM.
    - Métricas mínimas seguras: metricFOB e metricKG.
    - Parser para resposta em data.list.
    - Retry automático para 429/rate limit.
    """

    base_url = "https://api-comexstat.mdic.gov.br"

    def __init__(self, timeout: int = 120, max_retries: int = 5, default_retry_seconds: int = 12):
        self.timeout = timeout
        self.max_retries = max_retries
        self.default_retry_seconds = default_retry_seconds

    @staticmethod
    def _period_start(year: int) -> str:
        return f"{int(year)}-01"

    @staticmethod
    def _period_end(year: int) -> str:
        """Não consulta meses futuros no ano corrente."""
        from datetime import date
        year = int(year)
        today = date.today()
        if year == today.year:
            return f"{year}-{today.month:02d}"
        return f"{year}-12"

    @staticmethod
    def _retry_seconds(response: requests.Response, default: int = 12) -> int:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return max(1, int(float(retry_after)))
            except Exception:
                pass

        text = response.text or ""
        match = re.search(r"(\d+)\s*segundo", text, re.IGNORECASE)
        if match:
            try:
                return max(1, int(match.group(1)) + 2)
            except Exception:
                pass

        return default

    def _post_with_retry(self, endpoint: str, payload: dict, headers: dict) -> requests.Response:
        last_response = None

        for attempt in range(1, self.max_retries + 1):
            response = requests.post(endpoint, json=payload, headers=headers, timeout=self.timeout)
            last_response = response

            if response.status_code == 429:
                wait_seconds = self._retry_seconds(response, self.default_retry_seconds)
                print(
                    f"⚠️ Comex Stat rate limit 429. "
                    f"Tentativa {attempt}/{self.max_retries}. "
                    f"Aguardando {wait_seconds}s..."
                )
                time.sleep(wait_seconds)
                continue

            if 500 <= response.status_code <= 599:
                wait_seconds = min(self.default_retry_seconds * attempt, 60)
                print(
                    f"⚠️ Comex Stat erro {response.status_code}. "
                    f"Tentativa {attempt}/{self.max_retries}. "
                    f"Aguardando {wait_seconds}s..."
                )
                time.sleep(wait_seconds)
                continue

            return response

        return last_response

    def consultar_general(
        self,
        flow: str,
        year_start: int,
        year_end: int,
        ncms: list[str],
        month_detail: bool = True,
    ) -> tuple[pd.DataFrame, dict]:
        endpoint = f"{self.base_url}/general?language=pt"

        payload = {
            "flow": flow,
            "monthDetail": month_detail,
            "period": {
                "from": self._period_start(year_start),
                "to": self._period_end(year_end),
            },
            "filters": [
                {
                    "filter": "ncm",
                    "values": [str(ncm) for ncm in ncms],
                }
            ],
            "details": ["ncm"],
            "metrics": [
                "metricFOB",
                "metricKG",
            ],
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "radar-pescados-ia/1.0",
        }

        response = self._post_with_retry(endpoint, payload, headers)

        if not response.ok:
            error_text = response.text[:2000]
            raise requests.HTTPError(
                f"{response.status_code} Client Error for url: {endpoint} | response={error_text} | payload={payload}",
                response=response,
            )

        data = response.json()
        df = self._parse_response(data)

        metadata = {
            "endpoint": endpoint,
            "request_payload": payload,
            "response_payload": data,
            "status_http": response.status_code,
        }

        return df, metadata

    def _extract_list(self, data: dict | list) -> list:
        if isinstance(data, list):
            return data

        if not isinstance(data, dict):
            return []

        data_node = data.get("data")
        if isinstance(data_node, dict):
            for key in ["list", "results", "items"]:
                if isinstance(data_node.get(key), list):
                    return data_node.get(key)

        if isinstance(data_node, list):
            return data_node

        for key in ["list", "results", "items"]:
            if isinstance(data.get(key), list):
                return data.get(key)

        return []

    def _parse_response(self, data: dict | list) -> pd.DataFrame:
        raw = self._extract_list(data)

        rows = []
        for item in raw:
            if not isinstance(item, dict):
                continue

            year = item.get("year") or item.get("coAno") or item.get("ano") or item.get("Ano")
            month = item.get("monthNumber") or item.get("month") or item.get("coMes") or item.get("mes") or item.get("Mês") or 1
            ncm = item.get("ncm") or item.get("coNcm") or item.get("CO_NCM") or item.get("NCM") or ""
            usd = item.get("metricFOB") or item.get("vlFob") or item.get("VL_FOB") or item.get("FOB") or item.get("valorFob") or 0
            kg = item.get("metricKG") or item.get("kgLiquido") or item.get("KG_LIQUIDO") or item.get("VL_KG") or item.get("netWeight") or 0

            try:
                year = int(year)
                month = int(month)
            except Exception:
                continue

            rows.append({
                "ano": year,
                "mes_numero": month,
                "data": pd.Timestamp(year=year, month=month, day=1).date(),
                "ncm": str(ncm),
                "valor_usd_fob": float(usd or 0),
                "peso_kg": float(kg or 0),
            })

        return pd.DataFrame(rows)
