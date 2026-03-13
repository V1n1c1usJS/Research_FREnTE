"""Agente para descoberta aberta de fontes de dados, literatura e documentação técnica."""

from __future__ import annotations

from typing import Any

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
                limit=settings.limit * 3,
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

        sources = self._build_sources(findings, settings.query)
        return {
            "web_research_results": findings,
            "sources": sources,
            "search_terms": search_terms,
            "web_research_meta": {
                "requested_mode": self.web_research_mode,
                "connector_mode_used": connector_mode_used,
                "timeout_seconds": self.timeout_seconds,
                "fallback_reason": fallback_reason,
                "result_count": len(findings),
            },
        }

    @staticmethod
    def _build_search_terms(query: str, expanded_terms: list[str]) -> list[str]:
        core_terms = [
            query,
            "rio tietê",
            "reservatório de jupiá",
            "são paulo três lagoas",
            "uso da terra",
            "desmatamento",
            "queimadas",
            "relevo",
            "hidrologia",
            "qualidade da água",
            "esgoto",
            "resíduos",
            "sedimentos",
            "material orgânico",
            "ocupação urbana",
            "meteorologia",
            "artigos científicos",
            "relatórios técnicos",
        ]
        return list(dict.fromkeys(core_terms + expanded_terms))

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
