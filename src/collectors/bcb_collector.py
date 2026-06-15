from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import requests
import pandas as pd

from src.utils.retry import retry_api


@dataclass(frozen=True)
class BCBSerie:
    codigo: str
    indicador: str
    categoria: str
    unidade: str
    periodicidade: str


BCB_SERIES = [
    BCBSerie("1", "Dólar venda", "cambio", "R$/US$", "diaria"),
    BCBSerie("11", "Selic diária", "juros", "% a.d.", "diaria"),
    BCBSerie("433", "IPCA geral", "inflacao", "% mês", "mensal"),
    BCBSerie("1635", "IPCA alimentação e bebidas", "inflacao_alimentos", "% mês", "mensal"),
]


class BCBCollector:
    base_url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"

    @staticmethod
    def _parse_br_date(data_br: str) -> date:
        return datetime.strptime(data_br, "%d/%m/%Y").date()

    @staticmethod
    def _format_br_date(data: date) -> str:
        return data.strftime("%d/%m/%Y")

    @staticmethod
    def _year_chunks(data_inicio: date, data_fim: date) -> list[tuple[date, date]]:
        """Divide período em blocos anuais para evitar HTTP 406 em séries diárias grandes."""
        chunks: list[tuple[date, date]] = []
        atual = data_inicio

        while atual <= data_fim:
            fim_ano = date(atual.year, 12, 31)
            fim = min(fim_ano, data_fim)
            chunks.append((atual, fim))
            atual = fim + timedelta(days=1)

        return chunks

    @retry_api()
    def _request_periodo(
        self,
        serie: BCBSerie,
        data_inicio_br: str,
        data_fim_br: str | None = None,
    ) -> tuple[list[dict], dict]:
        params = {
            "formato": "json",
            "dataInicial": data_inicio_br,
        }
        if data_fim_br:
            params["dataFinal"] = data_fim_br

        url = self.base_url.format(codigo=serie.codigo)
        headers = {
            "Accept": "application/json",
            "User-Agent": "radar-pescados-ia/1.0",
        }

        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        payload = response.json()

        return payload, {
            "url": url,
            "params": params,
            "status_http": response.status_code,
            "payload": payload,
        }

    def coletar_serie(
        self,
        serie: BCBSerie,
        data_inicio: str = "01/01/2000",
        data_fim: str | None = None,
    ) -> tuple[pd.DataFrame, dict]:
        """
        Coleta série do Banco Central.

        Observação importante:
        Algumas séries diárias, como dólar e Selic, podem retornar HTTP 406 quando
        solicitadas desde 2000 em uma única chamada. Para essas séries, a coleta é
        feita em blocos anuais.
        """
        inicio = self._parse_br_date(data_inicio)
        fim = self._parse_br_date(data_fim) if data_fim else date.today()

        payload_total: list[dict] = []
        metadados_partes: list[dict] = []

        if serie.periodicidade == "diaria":
            chunks = self._year_chunks(inicio, fim)

            for ini, fim_chunk in chunks:
                payload, metadata = self._request_periodo(
                    serie=serie,
                    data_inicio_br=self._format_br_date(ini),
                    data_fim_br=self._format_br_date(fim_chunk),
                )
                payload_total.extend(payload)
                metadados_partes.append(
                    {
                        "params": metadata["params"],
                        "status_http": metadata["status_http"],
                        "qtd_registros": len(payload),
                    }
                )
        else:
            payload_total, metadata = self._request_periodo(
                serie=serie,
                data_inicio_br=data_inicio,
                data_fim_br=data_fim,
            )
            metadados_partes.append(
                {
                    "params": metadata["params"],
                    "status_http": metadata["status_http"],
                    "qtd_registros": len(payload_total),
                }
            )

        url = self.base_url.format(codigo=serie.codigo)

        metadata_final = {
            "url": url,
            "params": {
                "formato": "json",
                "dataInicial": data_inicio,
                "dataFinal": data_fim,
                "modo": "chunks_anuais" if serie.periodicidade == "diaria" else "unico",
            },
            "status_http": 200,
            "payload": payload_total,
            "partes": metadados_partes,
        }

        df = pd.DataFrame(payload_total)

        if df.empty:
            return df, metadata_final

        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce").dt.date
        df["valor"] = (
            df["valor"]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .pipe(pd.to_numeric, errors="coerce")
        )

        df = df.dropna(subset=["data", "valor"])
        df = df.drop_duplicates(subset=["data"]).sort_values("data")

        df["fonte"] = "BCB"
        df["codigo_serie"] = serie.codigo
        df["indicador"] = serie.indicador
        df["categoria"] = serie.categoria
        df["subcategoria"] = None
        df["pais"] = "Brasil"
        df["uf"] = ""
        df["municipio"] = ""
        df["regiao_ibge"] = ""
        df["regiao_comercial"] = ""
        df["unidade"] = serie.unidade
        df["periodicidade"] = serie.periodicidade

        df = df[
            [
                "data",
                "fonte",
                "codigo_serie",
                "indicador",
                "categoria",
                "subcategoria",
                "pais",
                "uf",
                "municipio",
                "regiao_ibge",
                "regiao_comercial",
                "valor",
                "unidade",
                "periodicidade",
            ]
        ]

        return df, metadata_final
