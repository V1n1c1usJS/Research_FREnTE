"""Agente para descoberta aberta de fontes de dados, literatura e documentação técnica."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from src.agents.base import BaseAgent
from src.connectors.web_research import (
    DuckDuckGoWebResearchConnector,
    MockWebResearchConnector,
    WebResearchConnector,
)
from src.schemas.records import ResearchSourceRecord, WebResearchResultRecord


class ResearchScoutAgent(BaseAgent):
    name = "research-scout"
    prompt_filename = "research_scout_agent.txt"

    PRIORITY_DOMAINS = (
        "gov.br",
        "ana.gov.br",
        "ibge.gov.br",
        "inpe.br",
        "mapbiomas.org",
        "scielo.br",
        "doi.org",
        "periodicos.capes.gov.br",
        "snirh.gov.br",
    )

    IRRELEVANT_KEYWORDS = (
        "imdb",
        "movie",
        "film",
        "trailer",
        "restaurant",
        "mexican grill",
        "menu",
        "pizza",
        "hotel",
        "tourism",
        "football",
    )

    REQUIRED_SIGNAL_KEYWORDS = (
        "hydrolog",
        "hidrolog",
        "water quality",
        "qualidade da água",
        "uso da terra",
        "land use",
        "dataset",
        "base de dados",
        "mapbiomas",
        "ana",
        "inpe",
        "ibge",
    )

    def __init__(
        self,
        connector: WebResearchConnector | None = None,
        web_research_mode: str = "mock",
        timeout_seconds: float = 8.0,
    ) -> None:
        self.web_research_mode = web_research_mode
        self.timeout_seconds = timeout_seconds
        self.connector = connector or self._build_connector()

    def _build_connector(self) -> WebResearchConnector:
        if self.web_research_mode == "real":
            return DuckDuckGoWebResearchConnector(timeout_seconds=self.timeout_seconds)
        return MockWebResearchConnector()

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.get_system_prompt()
        settings = context["settings"]

        expanded = context.get("expanded_queries", [])
        expanded_terms = [item["query"] for item in expanded if isinstance(item, dict) and "query" in item]

        search_terms = self._build_search_terms(settings.query, expanded_terms)

        findings: list[WebResearchResultRecord] = []
        fallback_reason = ""
        connector_mode_used = self.web_research_mode
        try:
            findings = self.connector.search(
                query=settings.query,
                search_terms=search_terms,
                limit=settings.limit * 4,
            )
        except Exception as exc:  # noqa: BLE001
            fallback_reason = f"connector_error:{type(exc).__name__}"

        if not findings and self.web_research_mode == "real":
            fallback_reason = fallback_reason or "empty_real_results"
            connector_mode_used = "mock-fallback"
            findings = MockWebResearchConnector().search(
                query=settings.query,
                search_terms=search_terms,
                limit=settings.limit * 2,
            )

        filtered_findings, discarded_count = self._apply_relevance_filter(findings)
        ranked_findings = sorted(filtered_findings, key=self._relevance_score, reverse=True)
        selected_findings = ranked_findings[: settings.limit * 3]

        if not selected_findings and self.web_research_mode == "real":
            fallback_reason = fallback_reason or "all_results_filtered_as_irrelevant"
            connector_mode_used = "mock-fallback"
            selected_findings = MockWebResearchConnector().search(
                query=settings.query,
                search_terms=search_terms,
                limit=settings.limit * 2,
            )
            discarded_count = max(discarded_count, len(findings))

        sources = self._build_sources(selected_findings, settings.query)
        return {
            "web_research_results": selected_findings,
            "sources": sources,
            "search_terms": search_terms,
            "web_research_meta": {
                "requested_mode": self.web_research_mode,
                "connector_mode_used": connector_mode_used,
                "timeout_seconds": self.timeout_seconds,
                "fallback_reason": fallback_reason,
                "result_count": len(selected_findings),
                "discarded_irrelevant_count": discarded_count,
            },
        }

    @classmethod
    def _build_search_terms(cls, query: str, expanded_terms: list[str]) -> list[str]:
        specific_queries = [
            '"Rio Tietê" "bacia do Tietê" "water quality" hidrologia "uso da terra" dataset',
            '"Rio Tietê" "qualidade da água" "base de dados" ANA INPE IBGE MapBiomas',
            '"bacia do Tietê" hidrologia "uso da terra" "base de dados" gov.br',
            '"Rio Tietê" "water quality" "land use" dataset "MapBiomas"',
            '"Rio Tietê" "bacia hidrográfica" "qualidade da água" "ANA" "Hidroweb"',
            '"Rio Tietê" "IBGE" "INPE" "MapBiomas" "dados"',
            query,
        ]

        curated_terms = [
            "rio tietê dataset",
            "bacia do tietê base de dados",
            "rio tietê water quality dataset",
            "rio tietê hidrologia ana",
            "rio tietê uso da terra mapbiomas",
            "rio tietê ibge inpe dados",
            "rio tietê scielo qualidade da água",
            "reservatório de jupiá hidrologia dados",
        ]

        return list(dict.fromkeys(specific_queries + curated_terms + expanded_terms))

    @classmethod
    def _apply_relevance_filter(
        cls, findings: list[WebResearchResultRecord]
    ) -> tuple[list[WebResearchResultRecord], int]:
        kept: list[WebResearchResultRecord] = []
        discarded = 0

        for item in findings:
            title = item.source_title.lower()
            url = item.source_url.lower()
            text = f"{title} {url} {item.evidence_notes.lower()}"

            if any(token in text for token in cls.IRRELEVANT_KEYWORDS):
                discarded += 1
                continue

            if "rio de janeiro" in text and "tiet" not in text and "bacia" not in text:
                discarded += 1
                continue

            if not cls._has_relevant_signal(text, item.source_url):
                discarded += 1
                continue

            score = cls._relevance_score(item)
            hint = f"initial_relevance_score={score:.2f}"
            kept.append(
                item.model_copy(
                    update={
                        "relevance_hint": score,
                        "relevance_to_100k": f"{item.relevance_to_100k} | {hint}",
                    }
                )
            )

        return kept, discarded

    @classmethod
    def _has_relevant_signal(cls, text: str, source_url: str) -> bool:
        if cls._is_priority_domain(source_url):
            return True

        has_anchor = any(token in text for token in ["tietê", "tiete", "jupiá", "jupia"])
        has_technical = any(token in text for token in cls.REQUIRED_SIGNAL_KEYWORDS)
        has_institutional = any(token in text for token in ["ana", "inpe", "ibge", "mapbiomas", "hidroweb", "snirh"])

        return has_anchor and (has_technical or has_institutional)

    @classmethod
    def _relevance_score(cls, item: WebResearchResultRecord) -> float:
        score = item.confidence
        host = urlparse(item.source_url).netloc.lower()
        text = f"{item.source_title.lower()} {item.evidence_notes.lower()}"

        if cls._is_priority_domain(item.source_url):
            score += 0.35
        elif host.endswith(".org") or host.endswith(".edu"):
            score += 0.10

        if any(token in text for token in ["tiet", "bacia", "hidrolog", "water quality", "qualidade da água"]):
            score += 0.20
        if any(token in text for token in ["dataset", "base de dados", "dados", "sistema", "portal"]):
            score += 0.10
        if item.source_type in {"institutional_documentation", "primary_data_portal", "academic_literature"}:
            score += 0.15

        return round(min(score, 1.0), 2)

    @classmethod
    def _is_priority_domain(cls, source_url: str) -> bool:
        host = urlparse(source_url).netloc.lower().replace("www.", "")
        return any(host.endswith(domain) for domain in cls.PRIORITY_DOMAINS)

    @staticmethod
    def _build_sources(findings: list[WebResearchResultRecord], query: str) -> list[ResearchSourceRecord]:
        sources: list[ResearchSourceRecord] = []
        seen_ids: set[str] = set()

        for item in findings:
            if item.source_id in seen_ids:
                continue

            if item.source_type == "primary_data_portal":
                priority = "high"
            elif item.source_type == "institutional_documentation":
                priority = "high"
            elif item.source_type == "academic_literature":
                priority = "medium"
            else:
                priority = "medium"

            sources.append(
                ResearchSourceRecord(
                    source_id=item.source_id,
                    name=item.publisher_or_org,
                    base_url=item.source_url,
                    source_type=item.source_type,
                    citation=item.source_title,
                    query=query,
                    priority=priority,
                    methodological_note=item.evidence_notes,
                )
            )
            seen_ids.add(item.source_id)

        return sources
