"""Conector Firecrawl para extracao contextual de guias de coleta."""

from __future__ import annotations

import logging
from typing import Any

from src.schemas.records import CollectionGuide, EnrichedDataset

logger = logging.getLogger(__name__)

COLLECTION_PROMPT_TEMPLATE = """\
Sou pesquisador do projeto 100K, que investiga o impacto antropico
na materia organica dos reservatorios em cascata do Rio Tiete
(Sao Paulo -> Tres Lagoas).

Reservatorios do estudo: Barra Bonita, Bariri, Ibitinga, Promissao,
Nova Avanhandava, Tres Irmaos, Jupia.

Area de estudo: bacia do Tiete, lat [-24, -20.5] lon [-52.2, -45.8].

NESTE PORTAL, estou buscando:
- Tema: {thematic_axis}
- Dataset: {dataset_name}
- Parametros de interesse: {parameters_str}
- Periodo desejado: {temporal_coverage}
- Regiao: {spatial_coverage}

Analise esta pagina e extraia:

1. PASSOS: instrucoes especificas e numeradas para chegar ao download
   desses dados. Inclua: onde clicar, quais menus navegar, quais
   opcoes selecionar. Se houver dropdowns, liste as opcoes relevantes
   para minha pesquisa (reservatorios do Tiete, estado de SP).

2. FILTROS: quais filtros estao disponiveis na pagina e quais valores
   selecionar para os dados que preciso. Se houver codigos internos
   (codigos de estacao de monitoramento, IDs de parametro, numeros
   de tabela, codigos IBGE), liste-os EXPLICITAMENTE com o nome
   correspondente (ex: TIBB02900 = Barra Bonita).

3. FORMATO DO DOWNLOAD: em que formato os dados serao baixados.
   Se houver opcao de escolher formato, indique qual selecionar.

4. ESFORCO ESTIMADO:
   "minutes" se ha botao de download direto com poucos cliques.
   "hours" se precisa navegar portal interativo com multiplas consultas.
   "days" se precisa de scraping, multiplos downloads ou OCR em PDFs.
   "requires_contact" se precisa contatar a instituicao.

5. ALERTAS: limitacoes, requisitos de login, timeout, dados faltantes.

6. DOWNLOADS DIRETOS: URLs completas de arquivos encontrados na pagina.
"""


def build_collection_prompt(dataset: EnrichedDataset) -> str:
    """Monta prompt contextual usando campos das fases A e B."""

    params = ", ".join(dataset.key_parameters) if dataset.key_parameters else ""
    if not params:
        params = "nao especificados - identificar os disponiveis no portal"

    return COLLECTION_PROMPT_TEMPLATE.format(
        thematic_axis=dataset.thematic_axis or "tema nao especificado",
        dataset_name=dataset.dataset_name or dataset.title,
        parameters_str=params,
        temporal_coverage=dataset.temporal_coverage or "maximo disponivel (idealmente 2000-2024)",
        spatial_coverage=dataset.spatial_coverage or "bacia do Rio Tiete, Sao Paulo",
    )


class FirecrawlCollector:
    """Extrai guias de coleta usando Firecrawl JSON mode + prompt contextual."""

    def __init__(
        self,
        api_key: str,
        timeout_seconds: float = 60.0,
        client: Any | None = None,
    ) -> None:
        self.timeout = int(timeout_seconds * 1000)
        self.client = client or self._build_client(api_key)

    def extract_collection_guide(
        self,
        *,
        url: str,
        dataset: EnrichedDataset,
    ) -> CollectionGuide:
        """Extrai CollectionGuide de uma URL a partir do dataset enriquecido."""

        prompt = build_collection_prompt(dataset)

        try:
            result = self._scrape(url=url, prompt=prompt)
            payload = self._extract_json_payload(result)
            if payload:
                return CollectionGuide.model_validate(payload)

            logger.warning("Firecrawl retornou JSON vazio para %s", url)
        except Exception as exc:  # noqa: BLE001
            logger.error("Firecrawl falhou para %s: %s", url, exc)

        return self._fallback_guide(url)

    @staticmethod
    def _build_client(api_key: str) -> Any:
        try:
            from firecrawl import Firecrawl  # type: ignore

            return Firecrawl(api_key=api_key)
        except Exception:
            from firecrawl import FirecrawlApp  # type: ignore

            return FirecrawlApp(api_key=api_key)

    def _scrape(self, *, url: str, prompt: str) -> Any:
        schema = CollectionGuide.model_json_schema()
        params = {
            "formats": ["json"],
            "jsonOptions": {
                "schema": schema,
                "prompt": prompt,
            },
            "onlyMainContent": False,
            "timeout": self.timeout,
        }

        if hasattr(self.client, "scrape"):
            return self.client.scrape(
                url,
                formats=params["formats"],
                json_options=params["jsonOptions"],
                only_main_content=False,
                timeout=self.timeout,
            )

        if hasattr(self.client, "scrape_url"):
            return self.client.scrape_url(
                url,
                params=params,
            )

        raise RuntimeError("Cliente Firecrawl sem metodo scrape/scrape_url compativel.")

    @staticmethod
    def _extract_json_payload(result: Any) -> dict[str, Any] | None:
        if result is None:
            return None

        if hasattr(result, "json") and isinstance(result.json, dict):
            return result.json

        if isinstance(result, dict):
            if isinstance(result.get("json"), dict):
                return result["json"]

            data = result.get("data")
            if isinstance(data, dict):
                if isinstance(data.get("json"), dict):
                    return data["json"]
                if isinstance(data.get("extract"), dict):
                    return data["extract"]

            if isinstance(result.get("extract"), dict):
                return result["extract"]

        return None

    @staticmethod
    def _fallback_guide(url: str) -> CollectionGuide:
        return CollectionGuide(
            steps=[
                f"Acessar {url}",
                "Navegar pela interface do portal",
                "Identificar a secao de download ou consulta",
                "Filtrar por bacia do Tiete, estado de SP e periodo 2000-2024",
                "Baixar no formato disponivel",
            ],
            filters_available={},
            download_format="unknown",
            estimated_effort="hours",
            caveats=[
                "Extracao automatica falhou - instrucoes genericas.",
                "Navegacao manual ainda necessaria para identificar filtros e formatos.",
            ],
            requires_login=False,
            direct_download_urls=[],
        )
