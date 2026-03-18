"""Agente para descoberta aberta de fontes de dados, literatura e documentacao tecnica."""

from __future__ import annotations

import unicodedata
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from src.agents.base import BaseLLMAgent
from src.connectors.web_research import (
    BingWebResearchConnector,
    DuckDuckGoWebResearchConnector,
    MockWebResearchConnector,
    WebResearchConnector,
)
from src.schemas.records import ResearchSourceRecord, WebResearchResultRecord


class _LLMScoutEvaluation(BaseModel):
    source_id: str
    keep: bool = True
    dataset_names_mentioned: list[str] = Field(default_factory=list)
    variables_mentioned: list[str] = Field(default_factory=list)
    publisher_or_org: str | None = None
    rationale: str = ""


class _LLMScoutPayload(BaseModel):
    follow_up_terms: list[str] = Field(default_factory=list)
    evaluations: list[_LLMScoutEvaluation] = Field(default_factory=list)


class ResearchScoutAgent(BaseLLMAgent):
    name = "research-scout"
    prompt_filename = "research_scout_agent.yaml"

    PRIORITY_DOMAINS = (
        "ana.gov.br",
        "snirh.gov.br",
        "ibge.gov.br",
        "inpe.br",
        "mapbiomas.org",
        "scielo.br",
        "doi.org",
        "periodicos.capes.gov.br",
        "gov.br",
    )
    TIER1_DOMAINS = PRIORITY_DOMAINS
    TIER2_SUFFIXES = (".edu.br", ".org.br")

    HARD_REJECT_KEYWORDS = (
        # entretenimento/turismo
        "imdb",
        "movie",
        "film",
        "trailer",
        "tourism",
        "hotel",
        "football",
        # dicionario/traducao
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
        # religiao/devocional
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
        "qualidade da agua",
        "bacia",
        "watershed",
        "dataset",
        "base de dados",
        "portal",
        "sistema",
        "dados",
        "uso da terra",
        "land use",
        "desmatamento",
        "queimadas",
        "saneamento",
        "esgoto",
        "residuos",
        "sedimentos",
        "meteorologia",
        "estacao",
        "monitoramento",
        "serie historica",
        "tabela",
        "vazao",
    )
    ANALYTICAL_HINTS = (
        "api",
        "download",
        "csv",
        "xlsx",
        "serie historica",
        "tabela",
        "estacao",
        "monitoramento",
        "hidroweb",
        "sidra",
        "mapbiomas",
        "dados abertos",
    )
    SCIENTIFIC_HINTS = ("scielo", "doi.org", "artigo", "paper", "thesis", "relatorio tecnico")
    ANCHOR_KEYWORDS = ("tiete", "jupia", "sao paulo", "tres lagoas")

    def __init__(
        self,
        connector: WebResearchConnector | None = None,
        web_research_mode: str = "mock",
        timeout_seconds: float = 8.0,
        *,
        llm_connector=None,
        fail_on_error: bool = False,
    ) -> None:
        super().__init__(llm_connector=llm_connector, fail_on_error=fail_on_error)
        self.web_research_mode = web_research_mode
        self.timeout_seconds = timeout_seconds
        self.connector = connector or self._build_connector()
        self.secondary_connector = (
            BingWebResearchConnector(timeout_seconds=self.timeout_seconds)
            if self.web_research_mode == "real" and connector is None
            else None
        )

    def _build_connector(self) -> WebResearchConnector:
        if self.web_research_mode == "real":
            return DuckDuckGoWebResearchConnector(timeout_seconds=self.timeout_seconds)
        return MockWebResearchConnector()

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        settings = context["settings"]

        expanded = context.get("expanded_queries", [])
        expanded_terms = [item["query"] for item in expanded if isinstance(item, dict) and "query" in item]
        search_terms = self._build_search_terms(settings.query, expanded_terms)

        findings: list[WebResearchResultRecord] = []
        fallback_reason = ""
        connector_mode_used = self.web_research_mode
        scout_triage_meta = self._empty_triage_meta()
        llm_keep_source_ids: set[str] = set()
        llm_follow_up_terms: list[str] = []

        try:
            findings = self.connector.search(
                query=settings.query,
                search_terms=search_terms,
                limit=settings.limit * 4,
            )
        except Exception as exc:  # noqa: BLE001
            fallback_reason = f"connector_error:{type(exc).__name__}"

        if self.web_research_mode == "real" and self.secondary_connector is not None:
            try:
                secondary_findings = self.secondary_connector.search(
                    query=settings.query,
                    search_terms=search_terms,
                    limit=settings.limit * 3,
                )
            except Exception:  # noqa: BLE001
                secondary_findings = []

            if secondary_findings:
                existing_urls = {item.source_url for item in findings}
                for candidate in secondary_findings:
                    if candidate.source_url not in existing_urls:
                        findings.append(candidate)
                        existing_urls.add(candidate.source_url)

        if not findings and self.web_research_mode == "mock":
            findings = MockWebResearchConnector().search(
                query=settings.query,
                search_terms=search_terms,
                limit=settings.limit * 2,
            )
            connector_mode_used = "mock"

        findings, llm_keep_source_ids, llm_follow_up_terms, scout_triage_meta = self._triage_with_llm(
            findings=findings,
            query=settings.query,
        )

        kept, discarded = self._apply_relevance_filter(findings, llm_keep_source_ids=llm_keep_source_ids)

        second_attempt_used = False
        if self.web_research_mode == "real" and findings and not kept:
            second_attempt_used = True
            priority_queries = self._build_priority_domain_queries(settings.query, llm_follow_up_terms)
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
                retry_findings, retry_llm_keep_ids, _, retry_triage_meta = self._triage_with_llm(
                    findings=retry_findings,
                    query=settings.query,
                )
                if retry_triage_meta["execution_mode"] == "llm":
                    scout_triage_meta = retry_triage_meta
                retry_kept, retry_discarded = self._apply_relevance_filter(
                    retry_findings,
                    llm_keep_source_ids=retry_llm_keep_ids,
                )
                findings = retry_findings
                discarded.extend(retry_discarded)
                if retry_kept:
                    kept = retry_kept

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
            "research_scout_triage_meta": scout_triage_meta,
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
                "triage_execution_mode": scout_triage_meta["execution_mode"],
                "triage_provider": scout_triage_meta["provider"],
                "triage_model": scout_triage_meta["model"],
                "triage_follow_up_term_count": len(scout_triage_meta["follow_up_terms"]),
                "triage_keep_recommendation_count": scout_triage_meta["keep_recommendation_count"],
            },
        }

    def _triage_with_llm(
        self,
        *,
        findings: list[WebResearchResultRecord],
        query: str,
    ) -> tuple[list[WebResearchResultRecord], set[str], list[str], dict[str, Any]]:
        meta = self._empty_triage_meta()
        if not findings or not self.has_llm:
            return findings, set(), [], meta

        try:
            payload = self.llm_connector.generate_json(
                system_prompt=self.get_system_prompt(),
                user_prompt=self._build_triage_prompt(findings=findings, query=query),
            )
            parsed = _LLMScoutPayload.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            meta["error"] = f"{type(exc).__name__}: {exc}"
            if self.fail_on_error:
                raise
            return findings, set(), [], meta

        evaluations_by_source = {item.source_id: item for item in parsed.evaluations}
        keep_source_ids = {item.source_id for item in parsed.evaluations if item.keep}
        follow_up_terms = self._deduplicate(parsed.follow_up_terms)

        enriched_findings: list[WebResearchResultRecord] = []
        for item in findings:
            evaluation = evaluations_by_source.get(item.source_id)
            if evaluation is None:
                enriched_findings.append(item)
                continue

            dataset_names = self._deduplicate(item.dataset_names_mentioned + evaluation.dataset_names_mentioned)
            variables = self._deduplicate(item.variables_mentioned + evaluation.variables_mentioned)
            evidence_notes = item.evidence_notes
            if evaluation.rationale.strip():
                evidence_notes = f"{evidence_notes} | llm_triage: {evaluation.rationale.strip()}"

            publisher = item.publisher_or_org
            if evaluation.publisher_or_org and evaluation.publisher_or_org.strip():
                publisher = evaluation.publisher_or_org.strip()

            enriched_findings.append(
                item.model_copy(
                    update={
                        "dataset_names_mentioned": dataset_names,
                        "variables_mentioned": variables,
                        "publisher_or_org": publisher,
                        "evidence_notes": evidence_notes,
                    }
                )
            )

        meta.update(
            {
                "execution_mode": "llm",
                "provider": self.llm_connector.provider,
                "model": self.llm_connector.model,
                "evaluated_source_count": len(parsed.evaluations),
                "keep_recommendation_count": len(keep_source_ids),
                "follow_up_terms": follow_up_terms,
            }
        )
        return enriched_findings, keep_source_ids, follow_up_terms, meta

    def _build_triage_prompt(self, *, findings: list[WebResearchResultRecord], query: str) -> str:
        findings_summary = [
            {
                "source_id": item.source_id,
                "source_title": item.source_title,
                "source_type": item.source_type,
                "source_url": item.source_url,
                "publisher_or_org": item.publisher_or_org,
                "dataset_names_mentioned": item.dataset_names_mentioned[:4],
                "variables_mentioned": item.variables_mentioned[:6],
                "evidence_notes": item.evidence_notes,
                "confidence": item.confidence,
            }
            for item in findings[:12]
        ]

        return (
            "Voce esta fazendo triagem de links e fontes para descoberta de datasets ambientais.\n\n"
            f"Consulta principal:\n{query}\n\n"
            "Resultados resumidos do conector (JSON):\n"
            f"{findings_summary}\n\n"
            "Retorne apenas JSON valido com o formato:\n"
            "{\n"
            '  "follow_up_terms": ["..."],\n'
            '  "evaluations": [\n'
            "    {\n"
            '      "source_id": "...",\n'
            '      "keep": true,\n'
            '      "dataset_names_mentioned": ["..."],\n'
            '      "variables_mentioned": ["..."],\n'
            '      "publisher_or_org": "...",\n'
            '      "rationale": "..."\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Regras:\n"
            "- use apenas source_id presentes na entrada;\n"
            "- mantenha no maximo 6 follow_up_terms;\n"
            "- follow_up_terms devem ser consultas curtas e pesquisaveis para encontrar portais e bases oficiais;\n"
            "- marque keep=true apenas para fontes plausivelmente uteis ao projeto 100K;\n"
            "- so preencha dataset_names_mentioned e variables_mentioned quando houver boa evidencia pelo titulo, url ou nota;\n"
            "- nao invente URLs, dominios ou datasets inexistentes."
        )

    @staticmethod
    def _empty_triage_meta() -> dict[str, Any]:
        return {
            "execution_mode": "heuristic",
            "provider": None,
            "model": None,
            "error": None,
            "evaluated_source_count": 0,
            "keep_recommendation_count": 0,
            "follow_up_terms": [],
        }

    @classmethod
    def _build_search_terms(cls, query: str, expanded_terms: list[str]) -> list[str]:
        hardened = [
            '"Rio Tiete" dataset',
            '"bacia do Tiete" hidrologia',
            '"Rio Tiete" "qualidade da agua" "base de dados" ANA INPE IBGE MapBiomas',
            '"Rio Tiete" "uso da terra" dataset "MapBiomas"',
            '"reservatorio de Jupia" dados',
            '"SNIRH" vazao',
            '"MapBiomas" "uso da terra"',
            '"INPE Queimadas" dados',
            '"SIDRA" saneamento municipio',
            '"Rio Tiete" dataset site:ana.gov.br',
            '"Rio Tiete" hidrologia site:snirh.gov.br',
            '"Rio Tiete" "qualidade da agua" site:gov.br',
            '"Rio Tiete" "uso da terra" site:mapbiomas.org',
            '"Rio Tiete" "queimadas" site:inpe.br',
            '"Rio Tiete" "saneamento" site:ibge.gov.br',
            query,
        ]
        analytical_recovery = [
            '"Rio Tiete" portal dados serie historica',
            '"Rio Tiete" API download tabela monitoramento',
            '"bacia do Tiete" estacao vazao dados abertos',
            "rio tiete scielo qualidade da agua",
            "reservatorio de jupia hidrologia dados",
        ]
        return list(dict.fromkeys(hardened + analytical_recovery + expanded_terms))

    @classmethod
    def _build_priority_domain_queries(cls, query: str, llm_follow_up_terms: list[str]) -> list[str]:
        domain_queries = [
            '"Rio Tiete" dataset site:ana.gov.br',
            '"Rio Tiete" hidrologia site:snirh.gov.br',
            '"Rio Tiete" "base de dados" site:ibge.gov.br',
            '"Rio Tiete" "uso da terra" site:mapbiomas.org',
            '"Rio Tiete" "queimadas" site:inpe.br',
            '"Rio Tiete" "qualidade da agua" site:scielo.br',
            '"Rio Tiete" site:gov.br',
            query,
        ]
        return list(dict.fromkeys(llm_follow_up_terms + domain_queries))

    @classmethod
    def _apply_relevance_filter(
        cls,
        findings: list[WebResearchResultRecord],
        *,
        llm_keep_source_ids: set[str] | None = None,
    ) -> tuple[list[WebResearchResultRecord], list[dict[str, object]]]:
        kept: list[WebResearchResultRecord] = []
        discarded: list[dict[str, object]] = []
        llm_keep_source_ids = llm_keep_source_ids or set()

        for item in findings:
            text = cls._normalize_text(
                f"{item.source_title.lower()} {item.source_url.lower()} {item.evidence_notes.lower()}"
            )
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
            threshold = 0.52 if tier == 3 else 0.38 if tier == 2 else 0.26
            if item.source_id in llm_keep_source_ids:
                threshold = max(0.22, threshold - 0.10)

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

            if tier == 3 and score < 0.58 and not cls._has_strong_thematic_signal(item):
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
            hint = f"initial_relevance_score={score:.2f}"
            if item.source_id in llm_keep_source_ids:
                hint = f"{hint};llm_triage=keep"

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
    def _domain_tier(cls, source_url: str) -> int:
        host = urlparse(source_url).netloc.lower().replace("www.", "")
        if any(host.endswith(domain) for domain in cls.TIER1_DOMAINS):
            return 1
        if any(host.endswith(suffix) for suffix in cls.TIER2_SUFFIXES):
            return 2
        return 3

    @classmethod
    def _has_strong_thematic_signal(cls, item: WebResearchResultRecord) -> bool:
        text = cls._normalize_text(
            f"{item.source_title.lower()} {item.evidence_notes.lower()} {item.source_url.lower()}"
        )
        anchors = sum(1 for token in cls.ANCHOR_KEYWORDS if token in text)
        technical = sum(1 for token in cls.TECHNICAL_KEYWORDS if token in text)
        return anchors >= 1 and technical >= 2

    @classmethod
    def _relevance_score(cls, item: WebResearchResultRecord) -> float:
        score = item.confidence
        text = cls._normalize_text(
            f"{item.source_title.lower()} {item.evidence_notes.lower()} {item.source_url.lower()}"
        )

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

    @classmethod
    def _is_priority_domain(cls, source_url: str) -> bool:
        host = urlparse(source_url).netloc.lower().replace("www.", "")
        return any(host.endswith(domain) for domain in cls.PRIORITY_DOMAINS)

    @classmethod
    def _infer_source_classification(cls, item: WebResearchResultRecord) -> dict[str, object]:
        url = item.source_url.lower()
        text = cls._normalize_text(f"{item.source_title.lower()} {item.evidence_notes.lower()} {url}")

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
            "serie historica",
            "monitoramento",
            "estacao",
            "tabela",
            "vazao",
        ]
        scientific_signals = [
            "scielo",
            "doi.org",
            "article",
            "paper",
            "thesis",
            "metodologia",
            "relatorio",
        ]

        is_analytical = item.source_type == "primary_data_portal" or any(signal in text for signal in analytical_signals)
        is_scientific = item.source_type == "academic_literature" or any(signal in text for signal in scientific_signals)

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
            data_extractability = (
                "high"
                if any(signal in text for signal in ["api", "csv", "xlsx", "download", "sidra", "hidroweb", "mapbiomas", "snis"])
                else "medium"
            )
            historical_records_available = (
                True
                if any(signal in text for signal in ["serie", "histor", "painel", "sidra", "hidroweb", "mapbiomas"])
                else None
            )
            structured_export_available = (
                True
                if any(signal in text for signal in ["csv", "xlsx", "api", "download", "sidra", "hidroweb", "mapbiomas"])
                else None
            )
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

    @staticmethod
    def _deduplicate(values: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for value in values:
            cleaned = value.strip()
            key = ResearchScoutAgent._normalize_text(cleaned.lower())
            if cleaned and key not in seen:
                seen.add(key)
                normalized.append(cleaned)
        return normalized

    @staticmethod
    def _normalize_text(value: str) -> str:
        return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
