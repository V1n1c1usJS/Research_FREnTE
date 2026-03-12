"""Conectores para pesquisa aberta na web (mock + modo real inicial)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

import httpx

from src.schemas.records import WebResearchResultRecord


class WebResearchConnector(ABC):
    """Contrato genérico para conectores de pesquisa web."""

    @abstractmethod
    def search(self, query: str, search_terms: list[str], limit: int = 20) -> list[WebResearchResultRecord]:
        """Executa pesquisa aberta e retorna achados estruturados."""


class MockWebResearchConnector(WebResearchConnector):
    """Simulador de pesquisa aberta com resultados plausíveis e auditáveis."""

    def search(self, query: str, search_terms: list[str], limit: int = 20) -> list[WebResearchResultRecord]:
        findings = [
            WebResearchResultRecord(
                source_id="src-ana",
                source_title="ANA - Agência Nacional de Águas e Saneamento Básico",
                source_type="institutional_documentation",
                source_url="https://www.gov.br/ana",
                publisher_or_org="ANA",
                dataset_names_mentioned=["Painéis de recursos hídricos", "Documentos técnicos de gestão"],
                variables_mentioned=["hidrologia", "qualidade da água", "uso da água"],
                geographic_scope="Brasil",
                relevance_to_100k="Alto para governança hídrica e contexto institucional.",
                evidence_notes="Portal institucional para referências regulatórias e técnicas.",
                search_terms_extracted=["ana", "rio tietê", "gestão hídrica"],
                citations=["https://www.gov.br/ana"],
                confidence=0.91,
            ),
            WebResearchResultRecord(
                source_id="src-hidroweb",
                source_title="Portal Hidroweb (SNIRH)",
                source_type="primary_data_portal",
                source_url="https://www.snirh.gov.br/hidroweb",
                publisher_or_org="Hidroweb",
                dataset_names_mentioned=["Séries históricas hidrológicas", "Estações fluviométricas"],
                variables_mentioned=["vazão", "nível", "chuva"],
                geographic_scope="Brasil (com aplicação ao corredor São Paulo-Três Lagoas)",
                relevance_to_100k="Alto para hidrologia no eixo Tietê-Jupiá.",
                evidence_notes="Portal institucional para séries hidrológicas; uso aqui é mock estruturado.",
                search_terms_extracted=["hidrologia", "vazão", "rio tietê"],
                citations=["https://www.snirh.gov.br/hidroweb"],
                confidence=0.95,
            ),
            WebResearchResultRecord(
                source_id="src-mapbiomas",
                source_title="MapBiomas - Coleções de uso e cobertura da terra",
                source_type="primary_data_portal",
                source_url="https://mapbiomas.org",
                publisher_or_org="MapBiomas",
                dataset_names_mentioned=["Coleção de Uso e Cobertura da Terra"],
                variables_mentioned=["uso da terra", "desmatamento", "ocupação urbana"],
                geographic_scope="Brasil",
                relevance_to_100k="Alto para pressão antrópica e mudança de uso do solo.",
                evidence_notes="Fonte de referência para séries anuais espaciais; não consultada em tempo real.",
                search_terms_extracted=["mapbiomas", "uso da terra", "desmatamento"],
                citations=["https://mapbiomas.org"],
                confidence=0.94,
            ),
            WebResearchResultRecord(
                source_id="src-inpe",
                source_title="Programa Queimadas (INPE)",
                source_type="primary_data_portal",
                source_url="https://terrabrasilis.dpi.inpe.br/queimadas/portal/",
                publisher_or_org="INPE",
                dataset_names_mentioned=["Focos de queimadas", "Risco de fogo"],
                variables_mentioned=["queimadas", "focos de calor", "meteorologia"],
                geographic_scope="Brasil",
                relevance_to_100k="Médio-alto para variáveis ambientais que impactam bacias.",
                evidence_notes="Portal institucional com séries geoespaciais; usado como inspiração mock.",
                search_terms_extracted=["inpe queimadas", "focos de calor"],
                citations=["https://terrabrasilis.dpi.inpe.br/queimadas/portal/"],
                confidence=0.9,
            ),
            WebResearchResultRecord(
                source_id="src-ibge",
                source_title="IBGE SIDRA - Banco de tabelas estatísticas",
                source_type="primary_data_portal",
                source_url="https://sidra.ibge.gov.br/",
                publisher_or_org="IBGE",
                dataset_names_mentioned=["Tabelas municipais", "Indicadores territoriais"],
                variables_mentioned=["ocupação urbana", "demografia", "indicadores socioeconômicos"],
                geographic_scope="Brasil",
                relevance_to_100k="Médio para contextualização territorial do corredor de estudo.",
                evidence_notes="Portal estatístico oficial para integração com variáveis ambientais.",
                search_terms_extracted=["ibge", "sidra", "municípios"],
                citations=["https://sidra.ibge.gov.br/"],
                confidence=0.88,
            ),
            WebResearchResultRecord(
                source_id="src-snis",
                source_title="SNIS - Painel de Saneamento",
                source_type="primary_data_portal",
                source_url=(
                    "https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/"
                    "saneamento/snis"
                ),
                publisher_or_org="SNIS",
                dataset_names_mentioned=["Indicadores de água e esgoto", "Cobertura de coleta e tratamento"],
                variables_mentioned=["esgoto", "resíduos", "infraestrutura urbana"],
                geographic_scope="Brasil",
                relevance_to_100k="Alto para indicadores de pressão urbana e saneamento.",
                evidence_notes="Fonte institucional relevante para variáveis de saneamento.",
                search_terms_extracted=["snis", "esgoto", "resíduos"],
                citations=[
                    "https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/snis"
                ],
                confidence=0.91,
            ),
            WebResearchResultRecord(
                source_id="src-academic",
                source_title="SciELO e Portal CAPES - literatura sobre Tietê/Jupiá",
                source_type="academic_literature",
                source_url="https://www.scielo.br/",
                publisher_or_org="Bases Acadêmicas e Relatórios Técnicos",
                dataset_names_mentioned=["Bases ambientais citadas em artigos", "Relatórios técnicos e teses"],
                variables_mentioned=["sedimentos", "material orgânico", "qualidade da água"],
                geographic_scope="Brasil / América Latina",
                relevance_to_100k="Médio-alto para descoberta indireta de datasets citados.",
                evidence_notes="Fonte acadêmica para identificar bases não buscadas diretamente.",
                search_terms_extracted=["artigos rio tietê", "reservatório de jupiá"],
                citations=["https://www.scielo.br/", "https://www.periodicos.capes.gov.br/"],
                confidence=0.84,
            ),
        ]

        return findings[:limit]


class DuckDuckGoWebResearchConnector(WebResearchConnector):
    """Conector real inicial de pesquisa web via DuckDuckGo Instant Answer API.

    Mantém arquitetura desacoplada e retorna apenas resultados com URL/evidência verificável.
    """

    base_url = "https://api.duckduckgo.com/"

    def __init__(self, timeout_seconds: float = 8.0) -> None:
        self.timeout_seconds = timeout_seconds

    def search(self, query: str, search_terms: list[str], limit: int = 20) -> list[WebResearchResultRecord]:
        results: list[WebResearchResultRecord] = []
        requests_budget = max(1, min(limit, 6))
        terms_to_use = [query] + search_terms[: requests_budget - 1]

        with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
            for term in terms_to_use:
                if len(results) >= limit:
                    break
                try:
                    response = client.get(
                        self.base_url,
                        params={
                            "q": term,
                            "format": "json",
                            "no_html": "1",
                            "skip_disambig": "1",
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
                except (httpx.HTTPError, ValueError):
                    continue

                items = self._extract_items(payload)
                for item in items:
                    if len(results) >= limit:
                        break
                    if not item.get("url"):
                        continue
                    results.append(self._to_record(item=item, term=term))

        return results

    @staticmethod
    def _extract_items(payload: dict) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []

        abstract_url = payload.get("AbstractURL")
        if abstract_url:
            items.append(
                {
                    "title": payload.get("Heading") or payload.get("AbstractSource") or "Web result",
                    "url": abstract_url,
                    "snippet": payload.get("AbstractText") or "Resultado retornado pela API de busca.",
                    "source": payload.get("AbstractSource") or "DuckDuckGo",
                }
            )

        for entry in payload.get("RelatedTopics", []) or []:
            if isinstance(entry, dict) and "FirstURL" in entry:
                items.append(
                    {
                        "title": entry.get("Text", "Related topic")[:160],
                        "url": entry.get("FirstURL", ""),
                        "snippet": entry.get("Text", ""),
                        "source": "DuckDuckGo RelatedTopics",
                    }
                )
            for nested in entry.get("Topics", []) if isinstance(entry, dict) else []:
                if isinstance(nested, dict) and "FirstURL" in nested:
                    items.append(
                        {
                            "title": nested.get("Text", "Related topic")[:160],
                            "url": nested.get("FirstURL", ""),
                            "snippet": nested.get("Text", ""),
                            "source": "DuckDuckGo RelatedTopics",
                        }
                    )

        return items

    @staticmethod
    def _to_record(item: dict[str, str], term: str) -> WebResearchResultRecord:
        source_url = item["url"]
        now = datetime.now(timezone.utc).isoformat()
        return WebResearchResultRecord(
            source_id=f"real-{abs(hash((source_url, term))) % 10_000_000}",
            source_title=item.get("title") or "Web result",
            source_type="web_result",
            source_url=source_url,
            publisher_or_org=item.get("source") or "Web",
            dataset_names_mentioned=[],
            variables_mentioned=[],
            geographic_scope="não identificado",
            relevance_to_100k="Triagem inicial automática; requer validação posterior.",
            evidence_notes=f"Resultado coletado por conector real (DuckDuckGo) em {now}.",
            search_terms_extracted=[term],
            citations=[source_url],
            confidence=0.55,
        )


class PreparedWebResearchConnector(DuckDuckGoWebResearchConnector):
    """Alias de compatibilidade para ponto de extensão do conector real."""


__all__ = [
    "WebResearchConnector",
    "MockWebResearchConnector",
    "DuckDuckGoWebResearchConnector",
    "PreparedWebResearchConnector",
]
