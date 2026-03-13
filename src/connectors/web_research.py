"""Conectores para pesquisa aberta na web (mock + modo real inicial)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from html import unescape
import re
from urllib.parse import parse_qs, urlparse

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
                source_class="scientific_knowledge_source",
                source_roles=["institutional_context", "governance_reference"],
                data_extractability="low",
                historical_records_available=None,
                structured_export_available=None,
                scientific_value="medium",
                recommended_pipeline_use=["institutional_framework", "dataset_discovery_from_portal_docs"],
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
                source_class="analytical_data_source",
                source_roles=["data_provider", "hydrology_series"],
                data_extractability="high",
                historical_records_available=True,
                structured_export_available=True,
                scientific_value="medium",
                recommended_pipeline_use=["direct_analytics_ingestion", "time_series_analysis"],
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
                source_class="analytical_data_source",
                source_roles=["data_provider", "land_use_monitoring"],
                data_extractability="high",
                historical_records_available=True,
                structured_export_available=True,
                scientific_value="medium",
                recommended_pipeline_use=["direct_analytics_ingestion", "spatial_analysis"],
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
                source_class="analytical_data_source",
                source_roles=["data_provider", "fire_monitoring"],
                data_extractability="high",
                historical_records_available=True,
                structured_export_available=True,
                scientific_value="medium",
                recommended_pipeline_use=["direct_analytics_ingestion", "event_series_analysis"],
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
                source_class="analytical_data_source",
                source_roles=["data_provider", "socioenvironmental_context"],
                data_extractability="medium",
                historical_records_available=True,
                structured_export_available=True,
                scientific_value="medium",
                recommended_pipeline_use=["contextual_covariates", "territorial_baseline"],
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
                source_class="analytical_data_source",
                source_roles=["data_provider", "sanitation_metrics"],
                data_extractability="medium",
                historical_records_available=True,
                structured_export_available=True,
                scientific_value="medium",
                recommended_pipeline_use=["direct_analytics_ingestion", "sanitation_pressure_modeling"],
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
                source_class="scientific_knowledge_source",
                source_roles=["scientific_evidence", "dataset_discovery_from_citations"],
                data_extractability="low",
                historical_records_available=None,
                structured_export_available=None,
                scientific_value="high",
                recommended_pipeline_use=["methodological_grounding", "dataset_discovery_from_citations"],
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
    html_search_url = "https://duckduckgo.com/html/"
    bing_search_url = "https://www.bing.com/search"

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
                if not items:
                    items = self._search_html(client=client, term=term)
                if not items:
                    items = self._search_bing_html(client=client, term=term)

                for item in items:
                    if len(results) >= limit:
                        break
                    if not item.get("url"):
                        continue
                    results.append(self._to_record(item=item, term=term))

        return results



    def _search_bing_html(self, client: httpx.Client, term: str) -> list[dict[str, str]]:
        try:
            response = client.get(
                self.bing_search_url,
                params={"q": term},
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
            )
            response.raise_for_status()
            body = response.text
        except httpx.HTTPError:
            return []

        pattern = re.compile(
            r'<h2[^>]*>\s*<a[^>]*href="(?P<url>[^"]+)"[^>]*>(?P<title>.*?)</a>\s*</h2>.*?'
            r'(?:<p[^>]*>(?P<snippet>.*?)</p>)?',
            flags=re.IGNORECASE | re.DOTALL,
        )

        items: list[dict[str, str]] = []
        for match in pattern.finditer(body):
            raw_url = unescape(match.group("url") or "")
            url = self._decode_bing_redirect(raw_url)
            if not url.startswith("http"):
                continue
            title = re.sub(r"<[^>]+>", "", match.group("title") or "").strip()
            snippet = re.sub(r"<[^>]+>", "", match.group("snippet") or "").strip()
            items.append(
                {
                    "title": title or "Web result",
                    "url": url,
                    "snippet": snippet,
                    "source": "Bing HTML",
                }
            )
            if len(items) >= 5:
                break

        return items

    @staticmethod
    def _decode_bing_redirect(url: str) -> str:
        parsed = urlparse(url)
        if '/ck/a' not in parsed.path:
            return url
        params = parse_qs(parsed.query)
        token = params.get('u', [''])[0]
        if not token:
            return url
        if token.startswith('a1'):
            token = token[2:]
        try:
            import base64
            padding = '=' * (-len(token) % 4)
            decoded = base64.urlsafe_b64decode((token + padding).encode('utf-8')).decode('utf-8', errors='ignore')
            return decoded if decoded.startswith('http') else url
        except Exception:  # noqa: BLE001
            return url

    def _search_html(self, client: httpx.Client, term: str) -> list[dict[str, str]]:
        try:
            response = client.get(self.html_search_url, params={"q": term})
            response.raise_for_status()
            body = response.text
        except httpx.HTTPError:
            return []

        pattern = re.compile(
            r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>.*?'
            r'(?:<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(?P<snippet_a>.*?)</a>|'
            r'<div[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(?P<snippet_div>.*?)</div>)?',
            flags=re.IGNORECASE | re.DOTALL,
        )

        items: list[dict[str, str]] = []
        for match in pattern.finditer(body):
            raw_url = unescape(match.group("href") or "")
            parsed = urlparse(raw_url)
            if parsed.path.startswith("/l/"):
                qs = parse_qs(parsed.query)
                raw_url = unescape(qs.get("uddg", [raw_url])[0])

            clean_title = re.sub(r"<[^>]+>", "", match.group("title") or "").strip()
            snippet_html = match.group("snippet_a") or match.group("snippet_div") or ""
            clean_snippet = re.sub(r"<[^>]+>", "", snippet_html).strip()

            if not raw_url.startswith("http"):
                continue
            items.append(
                {
                    "title": clean_title or "Web result",
                    "url": raw_url,
                    "snippet": clean_snippet,
                    "source": "DuckDuckGo HTML",
                }
            )
            if len(items) >= 5:
                break

        return items

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

    @classmethod
    def _to_record(cls, item: dict[str, str], term: str) -> WebResearchResultRecord:
        source_url = item["url"]
        now = datetime.now(timezone.utc).isoformat()
        title = item.get("title") or "Web result"
        snippet = item.get("snippet") or ""
        source_type = cls._infer_source_type(source_url)
        publisher = cls._infer_publisher(item.get("source") or "", source_url)
        variables = cls._extract_variables(title, snippet, term)
        dataset_mentions = cls._extract_dataset_mentions(title, snippet)

        return WebResearchResultRecord(
            source_id=f"real-{abs(hash((source_url, term))) % 10_000_000}",
            source_title=title,
            source_type=source_type,
            source_url=source_url,
            publisher_or_org=publisher,
            dataset_names_mentioned=dataset_mentions,
            variables_mentioned=variables,
            geographic_scope="não identificado",
            relevance_to_100k="Triagem inicial automática; requer validação posterior.",
            evidence_notes=(
                f"Resultado coletado por conector real (DuckDuckGo) em {now}. "
                f"Snippet: {snippet[:220]}"
            ),
            search_terms_extracted=[term],
            citations=[source_url],
            confidence=0.55,
            relevance_hint=0.15,
        )

    @staticmethod
    def _infer_source_type(source_url: str) -> str:
        host = urlparse(source_url).netloc.lower().replace("www.", "")
        if any(token in host for token in ["scielo", "springer", "elsevier", "wiley", "periodicos", "doi.org"]):
            return "academic_literature"
        if any(token in host for token in ["snirh.gov.br", "mapbiomas.org", "ibge.gov.br", "inpe.br"]):
            return "primary_data_portal"
        if ".gov" in host or host.endswith("gov.br"):
            return "institutional_documentation"
        return "web_result"

    @staticmethod
    def _infer_publisher(source_hint: str, source_url: str) -> str:
        if source_hint and source_hint.lower() not in {"duckduckgo", "duckduckgo relatedtopics"}:
            return source_hint
        host = urlparse(source_url).netloc.lower()
        if not host:
            return "Web"
        host = host.replace("www.", "")
        return host.split(".")[0].upper()

    @staticmethod
    def _extract_variables(title: str, snippet: str, term: str) -> list[str]:
        text = f"{title} {snippet} {term}".lower()
        mapping = {
            "hidrologia": ["hidrologia", "hydrology", "vazão", "streamflow", "bacia"],
            "qualidade da água": ["qualidade da água", "water quality", "ph", "turbidez"],
            "uso da terra": ["uso da terra", "land use", "land cover"],
            "bacia hidrográfica": ["bacia hidrográfica", "watershed", "river basin"],
            "rio tietê": ["rio tietê", "tietê", "tiete"],
        }
        found = []
        for label, tokens in mapping.items():
            if any(token in text for token in tokens):
                found.append(label)
        return found

    @staticmethod
    def _extract_dataset_mentions(title: str, snippet: str) -> list[str]:
        text = f"{title} {snippet}".strip()
        lowered = text.lower()
        if any(token in lowered for token in ["dataset", "base", "dados", "portal", "sistema"]):
            return [title[:180]]
        return []


class PreparedWebResearchConnector(DuckDuckGoWebResearchConnector):
    """Alias de compatibilidade para ponto de extensão do conector real."""


__all__ = [
    "WebResearchConnector",
    "MockWebResearchConnector",
    "DuckDuckGoWebResearchConnector",
    "PreparedWebResearchConnector",
]
