from __future__ import annotations

from dataclasses import dataclass
import requests
import pandas as pd

from src.utils.retry import retry_api


@dataclass(frozen=True)
class IBGEEndpoint:
    nome: str
    url: str


# Mapa simples pelo prefixo do código IBGE municipal.
UF_MAP = {
    "11": ("RO", "Rondônia", "Norte", "N"),
    "12": ("AC", "Acre", "Norte", "N"),
    "13": ("AM", "Amazonas", "Norte", "N"),
    "14": ("RR", "Roraima", "Norte", "N"),
    "15": ("PA", "Pará", "Norte", "N"),
    "16": ("AP", "Amapá", "Norte", "N"),
    "17": ("TO", "Tocantins", "Norte", "N"),
    "21": ("MA", "Maranhão", "Nordeste", "NE"),
    "22": ("PI", "Piauí", "Nordeste", "NE"),
    "23": ("CE", "Ceará", "Nordeste", "NE"),
    "24": ("RN", "Rio Grande do Norte", "Nordeste", "NE"),
    "25": ("PB", "Paraíba", "Nordeste", "NE"),
    "26": ("PE", "Pernambuco", "Nordeste", "NE"),
    "27": ("AL", "Alagoas", "Nordeste", "NE"),
    "28": ("SE", "Sergipe", "Nordeste", "NE"),
    "29": ("BA", "Bahia", "Nordeste", "NE"),
    "31": ("MG", "Minas Gerais", "Sudeste", "SE"),
    "32": ("ES", "Espírito Santo", "Sudeste", "SE"),
    "33": ("RJ", "Rio de Janeiro", "Sudeste", "SE"),
    "35": ("SP", "São Paulo", "Sudeste", "SE"),
    "41": ("PR", "Paraná", "Sul", "S"),
    "42": ("SC", "Santa Catarina", "Sul", "S"),
    "43": ("RS", "Rio Grande do Sul", "Sul", "S"),
    "50": ("MS", "Mato Grosso do Sul", "Centro-Oeste", "CO"),
    "51": ("MT", "Mato Grosso", "Centro-Oeste", "CO"),
    "52": ("GO", "Goiás", "Centro-Oeste", "CO"),
    "53": ("DF", "Distrito Federal", "Centro-Oeste", "CO"),
}


class IBGECollector:
    """
    Coletor de localidades do IBGE.

    Endpoints usados:
    - /api/v1/localidades/estados
    - /api/v1/localidades/municipios
    """

    base_url = "https://servicodados.ibge.gov.br/api/v1/localidades"

    @retry_api()
    def _get_json(self, url: str) -> tuple[list[dict], dict]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "radar-pescados-ia/1.0",
        }

        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()

        payload = response.json()

        return payload, {
            "url": url,
            "params": {},
            "status_http": response.status_code,
            "payload": payload,
        }

    def coletar_ufs(self) -> tuple[pd.DataFrame, dict]:
        url = f"{self.base_url}/estados"
        payload, metadata = self._get_json(url)

        linhas = []
        for item in payload:
            regiao = item.get("regiao") or {}

            linhas.append(
                {
                    "id_uf": item.get("id"),
                    "sigla_uf": item.get("sigla"),
                    "nome_uf": item.get("nome"),
                    "id_regiao": regiao.get("id"),
                    "sigla_regiao": regiao.get("sigla"),
                    "nome_regiao": regiao.get("nome"),
                }
            )

        df = pd.DataFrame(linhas)
        if not df.empty:
            df = df.sort_values("sigla_uf")

        return df, metadata

    def coletar_municipios(self) -> tuple[pd.DataFrame, dict]:
        url = f"{self.base_url}/municipios"
        payload, metadata = self._get_json(url)

        linhas = []
        for item in payload:
            codigo_ibge = str(item.get("id")) if item.get("id") is not None else None

            microrregiao = item.get("microrregiao") or {}
            mesorregiao = microrregiao.get("mesorregiao") or {}
            uf = mesorregiao.get("UF") or {}
            regiao = uf.get("regiao") or {}

            sigla_uf = uf.get("sigla")
            nome_uf = uf.get("nome")
            sigla_regiao = regiao.get("sigla")
            nome_regiao = regiao.get("nome")

            # Alguns municípios novos podem vir sem a estrutura antiga de microrregião/mesorregião.
            # Nesses casos, inferimos UF e região pelo prefixo do código IBGE municipal.
            if codigo_ibge and not sigla_uf:
                prefixo = codigo_ibge[:2]
                fallback = UF_MAP.get(prefixo)
                if fallback:
                    sigla_uf, nome_uf, nome_regiao, sigla_regiao = fallback

            linhas.append(
                {
                    "codigo_ibge": codigo_ibge,
                    "municipio": item.get("nome"),
                    "id_microrregiao": microrregiao.get("id"),
                    "microrregiao": microrregiao.get("nome"),
                    "id_mesorregiao": mesorregiao.get("id"),
                    "mesorregiao": mesorregiao.get("nome"),
                    "id_uf": uf.get("id"),
                    "sigla_uf": sigla_uf,
                    "nome_uf": nome_uf,
                    "id_regiao": regiao.get("id"),
                    "sigla_regiao": sigla_regiao,
                    "nome_regiao": nome_regiao,
                }
            )

        df = pd.DataFrame(linhas)
        if not df.empty:
            df = df.sort_values(["sigla_uf", "municipio"], na_position="last")

        return df, metadata
