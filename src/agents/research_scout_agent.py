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
    prompt_filename = "research_scout_agent.yaml"

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

    HARD_REJECT_KEYWORDS = (
        "imdb",
        "movie",
        "film",
        "trailer",
        "restaurant",
        "mexican grill",
        "pizza",
        "tourism",
        "hotel",
        "football",
    )

    TECHNICAL_KEYWORDS = (
        "hidrolog",
        "hydrolog",
        "water quality",
        "qualidade da água",
        "bacia",
        "watershed",
        "dataset",
        "base de dados",
        "portal",
        "sistema",
        "dados",
        "uso da terra",
        "land use",
    )

    ANCHOR_KEYWORDS = ("tietê", "tiete", "jupiá", "jupia")

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

        if not findings and self.web_research_mode == "mock":
            # Segurança para dry-run: mock sempre disponível.
            findings = MockWebResearchConnector().search(
                query=settings.query,
                search_terms=search_terms,
                limit=settings.limit * 2,
            )
            connector_mode_used = "mock"

        kept, discarded = self._apply_relevance_filter(findings)

        second_attempt_used = False
        second_attempt_findings: list[WebResearchResultRecord] = []
        if self.web_research_mode == "real" and findings and not kept:
            # Segunda tentativa real restrita a domínios prioritários antes de declarar baixa recuperação.
            second_attempt_used = True
            priority_queries = self._build_priority_domain_queries(settings.query)
            try:
                second_attempt_findings = self.connector.search(
                    query=priority_queries[0],
                    search_terms=priority_queries[1:],
                    limit=settings.limit * 4,
                )
            except Exception as exc:  # noqa: BLE001
                fallback_reason = fallback_reason or f"priority_retry_error:{type(exc).__name__}"
                second_attempt_findings = []

            if second_attempt_findings:
                retry_kept, retry_discarded = self._apply_relevance_filter(second_attempt_findings)
                discarded.extend(retry_discarded)
                if retry_kept:
                    kept = retry_kept
                    findings = second_attempt_findings

        ranked_findings = sorted(kept, key=self._relevance_score, reverse=True)
        selected_findings = ranked_findings[: settings.limit * 3]

        retrieval_status = "ok"
        if not findings and self.web_research_mode == "real":
            retrieval_status = "no_results"
            fallback_reason = fallback_reason or "no_results"
        elif findings and not selected_findings:
            retrieval_status = "all_filtered"
            fallback_reason = fallback_reason or "all_filtered"
        elif findings and len(selected_findings) < max(1, settings.limit // 2):
            retrieval_status = "low_recall"

        if self.web_research_mode == "mock":
            retrieval_status = "mock_fallback"

        sources = self._build_sources(selected_findings, settings.query)
        return {
            "web_research_results": selected_findings,
            "web_research_results_raw": [item.model_dump(mode="json") for item in findings],
            "web_research_results_discarded": discarded,
            "web_research_results_kept": [item.model_dump(mode="json") for item in selected_findings],
            "sources": sources,
            "search_terms": search_terms,
            "web_research_meta": {
                "requested_mode": self.web_research_mode,
                "connector_mode_used": connector_mode_used,
                "timeout_seconds": self.timeout_seconds,
                "fallback_reason": fallback_reason,
                "retrieval_status": retrieval_status,
                "second_attempt_used": second_attempt_used,
                "raw_result_count": len(findings),
                "kept_result_count": len(selected_findings),
                "discarded_irrelevant_count": len(discarded),
                "result_count": len(selected_findings),
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
    def _build_priority_domain_queries(cls, query: str) -> list[str]:
        domain_queries = [
            '"Rio Tietê" "bacia do Tietê" hidrologia "qualidade da água" dataset site:gov.br',
            '"Rio Tietê" "bacia do Tietê" "base de dados" site:ana.gov.br',
            '"Rio Tietê" hidrologia dataset site:snirh.gov.br',
            '"Rio Tietê" "uso da terra" dataset site:mapbiomas.org',
            '"Rio Tietê" "qualidade da água" site:scielo.br',
            query,
        ]
        return list(dict.fromkeys(domain_queries))

    @classmethod
    def _apply_relevance_filter(
        cls, findings: list[WebResearchResultRecord]
    ) -> tuple[list[WebResearchResultRecord], list[dict[str, object]]]:
        kept: list[WebResearchResultRecord] = []
        discarded: list[dict[str, object]] = []

        for item in findings:
            text = f"{item.source_title.lower()} {item.source_url.lower()} {item.evidence_notes.lower()}"

            hard_reason = cls._hard_reject_reason(text)
            if hard_reason:
                discarded.append(
                    {
                        "source_id": item.source_id,
                        "source_title": item.source_title,
                        "source_url": item.source_url,
                        "reason": hard_reason,
                    }
                )
                continue

            score = cls._relevance_score(item)
            threshold = 0.45
            if cls._is_priority_domain(item.source_url):
                threshold = 0.35

            if score < threshold:
                discarded.append(
                    {
                        "source_id": item.source_id,
                        "source_title": item.source_title,
                        "source_url": item.source_url,
                        "reason": f"low_score_below_threshold:{score:.2f}<{threshold:.2f}",
                    }
                )
                continue

            classification = cls._infer_source_classification(item)
            hint = f"initial_relevance_score={score:.2f}"
            kept.append(
                item.model_copy(
                    update={
                        "relevance_hint": score,
                        "relevance_to_100k": f"{item.relevance_to_100k} | {hint}",
                        **classification,
                    }
                )
            )

        return kept, discarded

    @classmethod
    def _hard_reject_reason(cls, text: str) -> str:
        for token in cls.HARD_REJECT_KEYWORDS:
            if token in text:
                return f"hard_reject:{token}"
        if "rio de janeiro" in text and not any(anchor in text for anchor in cls.ANCHOR_KEYWORDS):
            return "hard_reject:generic_rio_de_janeiro"
        return ""

    @classmethod
    def _relevance_score(cls, item: WebResearchResultRecord) -> float:
        score = item.confidence
        host = urlparse(item.source_url).netloc.lower()
        text = f"{item.source_title.lower()} {item.evidence_notes.lower()}"

        if cls._is_priority_domain(item.source_url):
            score += 0.35
        elif host.endswith(".org") or host.endswith(".edu"):
            score += 0.10

        if any(token in text for token in cls.ANCHOR_KEYWORDS):
            score += 0.20

        technical_hits = sum(1 for token in cls.TECHNICAL_KEYWORDS if token in text)
        if technical_hits >= 3:
            score += 0.30
        elif technical_hits >= 1:
            score += 0.15

        if item.source_type in {"institutional_documentation", "primary_data_portal", "academic_literature"}:
            score += 0.15

        return round(min(score, 1.0), 2)

    @classmethod
    def _is_priority_domain(cls, source_url: str) -> bool:
        host = urlparse(source_url).netloc.lower().replace("www.", "")
        return any(host.endswith(domain) for domain in cls.PRIORITY_DOMAINS)

    @staticmethod
    def _infer_source_classification(item: WebResearchResultRecord) -> dict[str, object]:
        url = item.source_url.lower()
        title = item.source_title.lower()
        source_type = item.source_type

        is_analytical = source_type == "primary_data_portal" or any(
            token in url for token in ["hidroweb", "mapbiomas", "sidra", "snis", "api", "download", "dados"]
        )
        is_scientific = source_type == "academic_literature" or any(
            token in url for token in ["scielo", "doi.org", "periodicos", "article", "paper", "thesis"]
        )

        source_class = "analytical_data_source" if is_analytical else "scientific_knowledge_source"

        roles: list[str] = []
        if is_analytical:
            roles.append("data_provider")
        if is_scientific:
            roles.append("scientific_evidence")
        if source_type == "institutional_documentation":
            roles.append("institutional_context")
        if not roles:
            roles.append("context_reference")

        if source_class == "analytical_data_source":
            data_extractability = "high" if any(
                x in url for x in ["api", "sidra", "hidroweb", "mapbiomas", "snis"]
            ) else "medium"
            historical_records_available = True if any(
                x in title + url for x in ["série", "histor", "painel", "sidra", "hidroweb", "mapbiomas"]
            ) else None
            structured_export_available = True if any(
                x in title + url for x in ["csv", "xlsx", "api", "sidra", "hidroweb", "mapbiomas"]
            ) else None
            scientific_value = "medium"
            recommended_pipeline_use = ["direct_analytics_ingestion", "time_series_analysis"]
        else:
            data_extractability = "low"
            historical_records_available = None
            structured_export_available = None
            scientific_value = "high" if source_type == "academic_literature" else "medium"
            recommended_pipeline_use = ["methodological_grounding", "dataset_discovery_from_citations"]

        return {
            "source_class": source_class,
            "source_roles": roles,
            "data_extractability": data_extractability,
            "historical_records_available": historical_records_available,
            "structured_export_available": structured_export_available,
            "scientific_value": scientific_value,
            "recommended_pipeline_use": recommended_pipeline_use,
        }

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
                    source_class=item.source_class,
                    source_roles=item.source_roles,
                    data_extractability=item.data_extractability,
                    historical_records_available=item.historical_records_available,
                    structured_export_available=item.structured_export_available,
                    scientific_value=item.scientific_value,
                    recommended_pipeline_use=item.recommended_pipeline_use,
                    priority=priority,
                    methodological_note=item.evidence_notes,
                )
            )
            seen_ids.add(item.source_id)

        return sources
