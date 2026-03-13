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

    TIER1_DOMAINS = (
        "ana.gov.br",
        "snirh.gov.br",
        "ibge.gov.br",
        "inpe.br",
        "mapbiomas.org",
        "scielo.br",
        "doi.org",
        "gov.br",
    )
    TIER2_SUFFIXES = (".gov.br", ".edu.br", ".org.br", "periodicos.capes.gov.br")

    HARD_REJECT_KEYWORDS = (
        # entretenimento/turismo
        "imdb",
        "movie",
        "film",
        "trailer",
        "tourism",
        "hotel",
        # dicionário/tradução
        "dictionary",
        "translation",
        "translate",
        "wordhippo",
        "reverso",
        "spanishdict",
        # e-commerce/marcas/produtos
        "amazon",
        "shop",
        "store",
        "product",
        # religião/devocional
        "novena",
        "catequese",
        "cancaonova",
        "opusdei",
        # receitas
        "recipe",
        "kitchen",
        "servings",
        # restaurantes
        "restaurant",
        "mexican grill",
        "pizza",
    )

    TECHNICAL_KEYWORDS = (
        "hidrolog",
        "hydrolog",
        "water quality",
        "qualidade da água",
        "dataset",
        "base de dados",
        "portal",
        "sistema",
        "dados",
        "uso da terra",
        "desmatamento",
        "queimadas",
        "saneamento",
        "esgoto",
        "resíduos",
        "sedimentos",
        "meteorologia",
        "estação",
        "monitoramento",
        "série histórica",
        "tabela",
        "vazão",
    )
    ANALYTICAL_HINTS = (
        "api",
        "download",
        "csv",
        "xlsx",
        "série histórica",
        "serie historica",
        "tabela",
        "estação",
        "monitoramento",
        "hidroweb",
        "sidra",
        "mapbiomas",
        "dados abertos",
    )
    SCIENTIFIC_HINTS = ("scielo", "doi.org", "artigo", "paper", "thesis", "relatório técnico")

    ANCHOR_KEYWORDS = ("tietê", "tiete", "jupiá", "jupia", "são paulo", "três lagoas")

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
            findings = MockWebResearchConnector().search(
                query=settings.query,
                search_terms=search_terms,
                limit=settings.limit * 2,
            )
            connector_mode_used = "mock"

        kept, discarded = self._apply_relevance_filter(findings)

        second_attempt_used = False
        if self.web_research_mode == "real" and findings and not kept:
            second_attempt_used = True
            priority_queries = self._build_priority_domain_queries(settings.query)
            try:
                retry_findings = self.connector.search(
                    query=priority_queries[0],
                    search_terms=priority_queries[1:],
                    limit=settings.limit * 4,
                )
            except Exception as exc:  # noqa: BLE001
                fallback_reason = fallback_reason or f"priority_retry_error:{type(exc).__name__}"
                retry_findings = []

            if retry_findings:
                findings = retry_findings
                kept, retry_discarded = self._apply_relevance_filter(retry_findings)
                discarded.extend(retry_discarded)

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

        # Quality gate por lote (evita consolidar lotes dominados por domínios irrelevantes)
        quality_gate_status = "passed"
        top_slice = selected_findings[: max(3, settings.limit)]
        irrelevant_top = 0
        for item in top_slice:
            if self._domain_tier(item.source_url) == 3 and not self._has_strong_thematic_signal(item):
                irrelevant_top += 1
        if top_slice and irrelevant_top / len(top_slice) > 0.5:
            quality_gate_status = "failed_quality_gate"
            selected_findings = []

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
                "quality_gate_status": quality_gate_status,
                "raw_result_count": len(findings),
                "kept_result_count": len(selected_findings),
                "discarded_irrelevant_count": len(discarded),
                "result_count": len(selected_findings),
            },
        }

    @classmethod
    def _build_search_terms(cls, query: str, expanded_terms: list[str]) -> list[str]:
        hardened = [
            '"Rio Tietê" dataset',
            '"bacia do Tietê" hidrologia',
            '"São Paulo" "qualidade da água" dataset',
            '"reservatório Jupiá" dados',
            '"SNIRH" vazão',
            '"MapBiomas" "uso da terra"',
            '"INPE Queimadas" dados',
            '"SIDRA" saneamento município',
            '"Rio Tietê" dataset site:ana.gov.br',
            '"Rio Tietê" hidrologia site:snirh.gov.br',
            '"Rio Tietê" "qualidade da água" site:gov.br',
            '"Rio Tietê" "uso da terra" site:mapbiomas.org',
            '"Rio Tietê" "queimadas" site:inpe.br',
            '"Rio Tietê" "saneamento" site:ibge.gov.br',
            query,
        ]
        analytical_recovery = [
            '"Rio Tietê" portal dados série histórica',
            '"Rio Tietê" API download tabela monitoramento',
            '"bacia do Tietê" estação vazão dados abertos',
        ]
        return list(dict.fromkeys(hardened + analytical_recovery + expanded_terms))

    @classmethod
    def _build_priority_domain_queries(cls, query: str) -> list[str]:
        return [
            '"Rio Tietê" dataset site:ana.gov.br',
            '"Rio Tietê" hidrologia site:snirh.gov.br',
            '"Rio Tietê" "base de dados" site:ibge.gov.br',
            '"Rio Tietê" "uso da terra" site:mapbiomas.org',
            '"Rio Tietê" "queimadas" site:inpe.br',
            '"Rio Tietê" "qualidade da água" site:scielo.br',
            '"Rio Tietê" site:gov.br',
            query,
        ]

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

            tier = cls._domain_tier(item.source_url)
            score = cls._relevance_score(item)
            threshold = 0.65 if tier == 3 else 0.45 if tier == 2 else 0.30
            if score < threshold:
                discarded.append(
                    {
                        "source_id": item.source_id,
                        "source_title": item.source_title,
                        "source_url": item.source_url,
                        "reason": f"low_score_below_threshold:tier{tier}:{score:.2f}<{threshold:.2f}",
                    }
                )
                continue

            if tier == 3 and not cls._has_strong_thematic_signal(item):
                discarded.append(
                    {
                        "source_id": item.source_id,
                        "source_title": item.source_title,
                        "source_url": item.source_url,
                        "reason": "tier3_without_strong_thematic_signal",
                    }
                )
                continue

            classification = cls._infer_source_classification(item)
            kept.append(
                item.model_copy(
                    update={
                        "relevance_hint": score,
                        "relevance_to_100k": f"{item.relevance_to_100k} | initial_relevance_score={score:.2f}",
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
    def _domain_tier(cls, source_url: str) -> int:
        host = urlparse(source_url).netloc.lower().replace("www.", "")
        if any(host.endswith(d) for d in cls.TIER1_DOMAINS):
            return 1
        if any(host.endswith(d) for d in cls.TIER2_SUFFIXES):
            return 2
        return 3

    @classmethod
    def _has_strong_thematic_signal(cls, item: WebResearchResultRecord) -> bool:
        text = f"{item.source_title.lower()} {item.evidence_notes.lower()} {item.source_url.lower()}"
        anchors = sum(1 for t in cls.ANCHOR_KEYWORDS if t in text)
        technical = sum(1 for t in cls.TECHNICAL_KEYWORDS if t in text)
        return anchors >= 1 and technical >= 2

    @classmethod
    def _relevance_score(cls, item: WebResearchResultRecord) -> float:
        score = item.confidence
        text = f"{item.source_title.lower()} {item.evidence_notes.lower()} {item.source_url.lower()}"

        tier = cls._domain_tier(item.source_url)
        if tier == 1:
            score += 0.45
        elif tier == 2:
            score += 0.20

        technical_hits = sum(1 for token in cls.TECHNICAL_KEYWORDS if token in text)
        analytical_hits = sum(1 for token in cls.ANALYTICAL_HINTS if token in text)
        anchor_hits = sum(1 for token in cls.ANCHOR_KEYWORDS if token in text)

        score += min(0.30, technical_hits * 0.06)
        score += min(0.20, analytical_hits * 0.07)
        score += min(0.20, anchor_hits * 0.10)

        if item.source_type in {"institutional_documentation", "primary_data_portal", "academic_literature"}:
            score += 0.10

        if tier == 3 and analytical_hits == 0 and technical_hits < 2:
            score -= 0.25

        return round(max(0.0, min(score, 1.0)), 2)

    @staticmethod
    def _infer_source_classification(item: WebResearchResultRecord) -> dict[str, object]:
        url = item.source_url.lower()
        text = f"{item.source_title.lower()} {item.evidence_notes.lower()} {url}"

        analytical_signals = [
            "hidroweb",
            "snirh",
            "sidra",
            "mapbiomas",
            "api",
            "download",
            "csv",
            "xlsx",
            "dados abertos",
            "série histórica",
            "monitoramento",
            "estação",
            "tabela",
            "vazão",
        ]
        scientific_signals = ["scielo", "doi.org", "article", "paper", "thesis", "metodologia", "relatório"]

        is_analytical = item.source_type == "primary_data_portal" or any(s in text for s in analytical_signals)
        is_scientific = item.source_type == "academic_literature" or any(s in text for s in scientific_signals)

        source_class = "analytical_data_source" if is_analytical else "scientific_knowledge_source"

        roles: list[str] = []
        if is_analytical:
            roles.append("data_provider")
        if is_scientific:
            roles.append("scientific_evidence")
        if item.source_type == "institutional_documentation":
            roles.append("institutional_context")
        if not roles:
            roles.append("context_reference")

        if source_class == "analytical_data_source":
            data_extractability = "high" if any(s in text for s in ["api", "csv", "xlsx", "download", "sidra", "hidroweb", "mapbiomas"]) else "medium"
            historical_records_available = True if any(s in text for s in ["série", "histor", "painel", "sidra", "hidroweb", "mapbiomas"]) else None
            structured_export_available = True if any(s in text for s in ["csv", "xlsx", "api", "download", "sidra", "hidroweb", "mapbiomas"]) else None
            scientific_value = "medium"
            recommended_pipeline_use = ["direct_analytics_ingestion", "time_series_analysis"]
        else:
            data_extractability = "low"
            historical_records_available = None
            structured_export_available = None
            scientific_value = "high" if is_scientific else "medium"
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

            priority = "high" if item.source_type in {"primary_data_portal", "institutional_documentation"} else "medium"

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
