"""Agente para categorizar fontes coletadas no Perplexity."""

from __future__ import annotations

from collections import defaultdict
from typing import Any
from urllib.parse import urlparse

from src.agents.base import BaseLLMAgent
from src.connectors.llm import LLMConnectorError
from src.schemas.records import (
    IntelligenceSourceRecord,
    PerplexityResearchContextRecord,
    PerplexitySearchSessionRecord,
    ResearchSourceRecord,
    WebResearchResultRecord,
)


class PerplexitySourceCategorizationAgent(BaseLLMAgent):
    """Consolida links coletados e usa LLM para classificar a fonte quando disponivel."""

    name = "perplexity-categorization"
    prompt_filename = "perplexity_source_categorization_agent.yaml"

    ALLOWED_CATEGORIES = {
        "official_data_portal",
        "academic_source",
        "repository",
        "institutional_report",
        "civil_society_monitoring",
        "journalistic_context",
        "secondary_reference",
    }
    ALLOWED_PRIORITIES = {"high", "medium", "low"}
    ALLOWED_ARTICLE_VALUES = {"high", "medium", "low"}
    ALLOWED_SCIENTIFIC_VALUES = {"high", "medium", "low"}
    ALLOWED_EXTRACTABILITY = {"high", "medium", "low", "unknown"}

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.get_system_prompt()
        sessions: list[PerplexitySearchSessionRecord] = context.get("perplexity_sessions", [])
        master_context: PerplexityResearchContextRecord | None = context.get("perplexity_master_context")

        raw_buckets, ok_sessions, error_sessions = self._collect_buckets(sessions)
        inferred_rows: list[dict[str, Any]] = []
        inference_errors: list[str] = []
        llm_used_count = 0

        for bucket in raw_buckets.values():
            inferred, used_llm, error_message = self._infer_bucket(bucket=bucket, master_context=master_context)
            if used_llm:
                llm_used_count += 1
            if error_message:
                inference_errors.append(error_message)
            inferred_rows.append(inferred)

        priority_rank = {"high": 0, "medium": 1, "low": 2}
        inferred_rows.sort(
            key=lambda item: (
                priority_rank.get(item["priority"], 3),
                not item["official_signal"],
                not item["dataset_signal"],
                -item["evidence_count"],
                item["title"].lower(),
            )
        )

        categorized_sources: list[IntelligenceSourceRecord] = []
        research_sources: list[ResearchSourceRecord] = []
        findings: list[WebResearchResultRecord] = []

        for index, item in enumerate(inferred_rows, start=1):
            source_id = f"pplx-src-{index:03d}"
            snippets = self._deduplicate_preserve_order(item["snippets"])[:3]

            categorized_sources.append(
                IntelligenceSourceRecord(
                    source_id=source_id,
                    title=item["title"],
                    url=item["url"],
                    domain=item["domain"],
                    category=item["category"],
                    source_class=item["source_class"],
                    target_intent=item["target_intent"],
                    article_value=item["article_value"],
                    dataset_signal=item["dataset_signal"],
                    academic_signal=item["academic_signal"],
                    official_signal=item["official_signal"],
                    priority=item["priority"],
                    search_profiles=sorted(item["search_profiles"]),
                    research_tracks=sorted(item["research_tracks"]),
                    supporting_query_ids=sorted(item["supporting_query_ids"]),
                    evidence_count=item["evidence_count"],
                    snippets=snippets,
                    dataset_names_mentioned=item["dataset_names_mentioned"],
                    variables_mentioned=item["variables_mentioned"],
                    rationale=item["rationale"],
                )
            )

            research_sources.append(
                ResearchSourceRecord(
                    source_id=source_id,
                    name=item["title"],
                    base_url=item["url"],
                    source_type=item["source_type"],
                    citation=item["url"],
                    query=" | ".join(sorted(item["search_profiles"])),
                    source_class=item["source_class"],
                    source_roles=item["source_roles"],
                    data_extractability=item["data_extractability"],
                    historical_records_available=item["historical_records_available"],
                    structured_export_available=item["structured_export_available"],
                    scientific_value=item["scientific_value"],
                    recommended_pipeline_use=item["recommended_pipeline_use"],
                    priority=item["priority"],
                    methodological_note=(
                        "Fonte consolidada de coleta Perplexity; "
                        f"trilhas={', '.join(sorted(item['research_tracks']))}; "
                        f"evidencias={item['evidence_count']}; "
                        f"classificacao={item['classification_method']}."
                    ),
                )
            )

            findings.append(
                WebResearchResultRecord(
                    source_id=source_id,
                    source_title=item["title"],
                    source_type=item["source_type"],
                    source_url=item["url"],
                    publisher_or_org=item["publisher_or_org"],
                    dataset_names_mentioned=item["dataset_names_mentioned"],
                    variables_mentioned=item["variables_mentioned"],
                    geographic_scope=self._resolve_geographic_scope(master_context),
                    relevance_to_100k=(
                        f"Fonte categorizada como {item['category']} com prioridade {item['priority']} "
                        f"e article_value={item['article_value']}."
                    ),
                    evidence_notes=(
                        "Coleta Perplexity via Playwright; "
                        f"classificacao={item['classification_method']}; "
                        f"amostra={snippets[0] if snippets else 'sem snippet'}"
                    ),
                    search_terms_extracted=sorted(item["search_profiles"]),
                    citations=[item["url"]],
                    confidence=item["confidence"],
                    relevance_hint=item["relevance_hint"],
                    source_class=item["source_class"],
                    source_roles=item["source_roles"],
                    data_extractability=item["data_extractability"],
                    historical_records_available=item["historical_records_available"],
                    structured_export_available=item["structured_export_available"],
                    scientific_value=item["scientific_value"],
                    recommended_pipeline_use=item["recommended_pipeline_use"],
                )
            )

        category_summary = defaultdict(int)
        research_track_summary = defaultdict(int)
        for item in categorized_sources:
            category_summary[item.category] += 1
            for track in item.research_tracks:
                research_track_summary[track] += 1

        execution_mode = "heuristic"
        if self.has_llm and llm_used_count == len(raw_buckets):
            execution_mode = "llm"
        elif self.has_llm and llm_used_count:
            execution_mode = "hybrid"

        return {
            "categorized_sources": categorized_sources,
            "sources": research_sources,
            "web_research_results": findings,
            "perplexity_categorization_meta": {
                "session_count": len(sessions),
                "ok_session_count": ok_sessions,
                "error_session_count": error_sessions,
                "unique_source_count": len(categorized_sources),
                "category_summary": dict(category_summary),
                "research_track_summary": dict(research_track_summary),
                "execution_mode": execution_mode,
                "provider": self.llm_connector.provider if self.has_llm else None,
                "model": self.llm_connector.model if self.has_llm else None,
                "llm_inference_count": llm_used_count,
                "inference_error_count": len(inference_errors),
                "inference_errors": inference_errors[:5],
            },
        }

    def _collect_buckets(
        self,
        sessions: list[PerplexitySearchSessionRecord],
    ) -> tuple[dict[str, dict[str, Any]], int, int]:
        buckets: dict[str, dict[str, Any]] = {}
        ok_sessions = 0
        error_sessions = 0

        for session in sessions:
            if session.collection_status != "ok":
                error_sessions += 1
                continue
            ok_sessions += 1
            answer_excerpt = self._compact_text(session.answer_text, limit=500)

            for link in session.links:
                normalized_url = self._normalize_url(link.url)
                if not normalized_url:
                    continue

                bucket = buckets.setdefault(
                    normalized_url,
                    {
                        "url": normalized_url,
                        "domain": self._normalize_domain(link.domain, normalized_url),
                        "titles": [],
                        "snippets": [],
                        "answer_excerpts": [],
                        "search_profiles": set(),
                        "research_tracks": set(),
                        "supporting_query_ids": set(),
                        "research_questions": set(),
                        "target_intents": set(),
                        "page_urls": set(),
                        "evidence_count": 0,
                    },
                )

                title = self._compact_text(link.title or link.domain or normalized_url, limit=180)
                if title:
                    bucket["titles"].append(title)
                snippet = self._compact_text(link.snippet, limit=500)
                if snippet:
                    bucket["snippets"].append(snippet)
                if answer_excerpt:
                    bucket["answer_excerpts"].append(answer_excerpt)
                if session.search_profile:
                    bucket["search_profiles"].add(session.search_profile)
                if session.research_track:
                    bucket["research_tracks"].add(session.research_track)
                if session.query_id:
                    bucket["supporting_query_ids"].add(session.query_id)
                if session.research_question:
                    bucket["research_questions"].add(session.research_question)
                if session.target_intent:
                    bucket["target_intents"].add(session.target_intent)
                if session.page_url:
                    bucket["page_urls"].add(session.page_url)
                bucket["evidence_count"] += 1

        return buckets, ok_sessions, error_sessions

    def _infer_bucket(
        self,
        *,
        bucket: dict[str, Any],
        master_context: PerplexityResearchContextRecord | None,
    ) -> tuple[dict[str, Any], bool, str | None]:
        if self.has_llm:
            try:
                payload = self.llm_connector.generate_json(
                    system_prompt=self.get_system_prompt(),
                    user_prompt=self._build_inference_prompt(bucket=bucket, master_context=master_context),
                    max_output_tokens=1600,
                    temperature=0.0,
                )
                if isinstance(payload, list):
                    raise LLMConnectorError("Payload de categorizacao deve ser um objeto JSON.")
                return self._sanitize_inference(bucket=bucket, payload=payload, method="llm"), True, None
            except Exception as exc:  # noqa: BLE001
                if self.fail_on_error:
                    raise
                fallback = self._heuristic_inference(bucket)
                return fallback, False, f"{bucket['url']}: {type(exc).__name__}: {exc}"

        return self._heuristic_inference(bucket), False, None

    def _build_inference_prompt(
        self,
        *,
        bucket: dict[str, Any],
        master_context: PerplexityResearchContextRecord | None,
    ) -> str:
        context_lines = []
        if master_context is not None:
            context_lines.extend(
                [
                    f"Objetivo da pesquisa: {master_context.article_goal}",
                    f"Escopo geografico: {', '.join(master_context.geographic_scope) or 'nao informado'}",
                    f"Eixos tematicos: {', '.join(master_context.thematic_axes) or 'nao informados'}",
                    f"Fontes preferidas: {', '.join(master_context.preferred_sources) or 'nao informadas'}",
                ]
            )

        return "\n".join(
            [
                "Classifique UMA fonte coletada via Perplexity e devolva APENAS JSON valido.",
                "Campos obrigatorios:",
                "{",
                '  "canonical_title": str,',
                '  "category": "official_data_portal|academic_source|repository|institutional_report|civil_society_monitoring|journalistic_context|secondary_reference",',
                '  "publisher_or_org": str,',
                '  "dataset_signal": bool,',
                '  "academic_signal": bool,',
                '  "official_signal": bool,',
                '  "priority": "high|medium|low",',
                '  "dataset_names_mentioned": [str],',
                '  "variables_mentioned": [str],',
                '  "source_roles": [str],',
                '  "data_extractability": "high|medium|low|unknown",',
                '  "scientific_value": "high|medium|low",',
                '  "recommended_pipeline_use": [str],',
                '  "article_value": "high|medium|low",',
                '  "historical_records_available": bool|null,',
                '  "structured_export_available": bool|null,',
                '  "rationale": str',
                "}",
                "",
                "Regras:",
                "- Nao use listas predefinidas de dominio; infera pela evidencia textual e pelo proprio link.",
                "- Marque official_signal apenas quando houver evidencia suficiente de fonte oficial ou institucional primaria.",
                "- Marque academic_signal quando houver evidencia suficiente de fonte academica ou repositorio cientifico.",
                "- Extraia variaveis de forma aberta; nao force taxonomias fixas.",
                "- Se a fonte for portal, painel, catalogo, API ou download estruturado, reflita isso em dataset_signal e recommended_pipeline_use.",
                "",
                "Contexto da pesquisa:",
                *context_lines,
                "",
                f"URL: {bucket['url']}",
                f"Dominio: {bucket['domain']}",
                f"Titulos observados: {bucket['titles'][:3]}",
                f"Snippets: {bucket['snippets'][:3]}",
                f"Perguntas relacionadas: {sorted(bucket['research_questions'])[:3]}",
                f"Perfis de busca: {sorted(bucket['search_profiles'])}",
                f"Trilhas: {sorted(bucket['research_tracks'])}",
                f"Intencoes de busca: {sorted(bucket['target_intents'])}",
                f"Excertos de resposta: {bucket['answer_excerpts'][:2]}",
            ]
        )

    def _sanitize_inference(
        self,
        *,
        bucket: dict[str, Any],
        payload: dict[str, Any],
        method: str,
    ) -> dict[str, Any]:
        title = self._clean_text(payload.get("canonical_title")) or self._resolve_title(bucket)
        category = self._clean_choice(payload.get("category"), self.ALLOWED_CATEGORIES) or "secondary_reference"
        dataset_signal = bool(payload.get("dataset_signal", False))
        academic_signal = bool(payload.get("academic_signal", False))
        official_signal = bool(payload.get("official_signal", False))
        priority = self._clean_choice(payload.get("priority"), self.ALLOWED_PRIORITIES) or self._priority_from_flags(
            dataset_signal=dataset_signal,
            official_signal=official_signal,
            academic_signal=academic_signal,
            category=category,
        )
        source_class = self._source_class_from_category(category=category, dataset_signal=dataset_signal)
        source_type = self._source_type_from_category(category=category)
        variables = self._clean_list(payload.get("variables_mentioned"))
        dataset_names = self._clean_list(payload.get("dataset_names_mentioned"))
        if not dataset_names and dataset_signal:
            dataset_names = [title]
        source_roles = self._clean_list(payload.get("source_roles"))
        if not source_roles:
            source_roles = self._default_source_roles(
                category=category,
                official_signal=official_signal,
                academic_signal=academic_signal,
                dataset_signal=dataset_signal,
            )

        target_intent = self._resolve_target_intent(bucket)

        return {
            "title": title,
            "url": bucket["url"],
            "domain": bucket["domain"],
            "category": category,
            "source_class": source_class,
            "source_type": source_type,
            "target_intent": target_intent,
            "dataset_signal": dataset_signal,
            "academic_signal": academic_signal,
            "official_signal": official_signal,
            "priority": priority,
            "search_profiles": set(bucket["search_profiles"]),
            "research_tracks": set(bucket["research_tracks"]),
            "supporting_query_ids": set(bucket["supporting_query_ids"]),
            "snippets": self._deduplicate_preserve_order(bucket["snippets"] + bucket["answer_excerpts"]),
            "evidence_count": bucket["evidence_count"],
            "dataset_names_mentioned": dataset_names,
            "variables_mentioned": variables,
            "rationale": self._clean_text(payload.get("rationale")) or "llm_inference_without_rationale",
            "publisher_or_org": self._clean_text(payload.get("publisher_or_org")) or self._infer_publisher(bucket, title),
            "source_roles": source_roles,
            "data_extractability": self._clean_choice(payload.get("data_extractability"), self.ALLOWED_EXTRACTABILITY)
            or "unknown",
            "scientific_value": self._clean_choice(payload.get("scientific_value"), self.ALLOWED_SCIENTIFIC_VALUES)
            or self._scientific_value_from_category(category),
            "recommended_pipeline_use": self._clean_list(payload.get("recommended_pipeline_use"))
            or self._recommended_use_from_category(
                category=category,
                dataset_signal=dataset_signal,
                academic_signal=academic_signal,
            ),
            "article_value": self._clean_choice(payload.get("article_value"), self.ALLOWED_ARTICLE_VALUES)
            or self._article_value_from_category(category),
            "historical_records_available": self._coerce_optional_bool(payload.get("historical_records_available")),
            "structured_export_available": self._coerce_optional_bool(payload.get("structured_export_available")),
            "confidence": self._confidence_from_signals(
                dataset_signal=dataset_signal,
                academic_signal=academic_signal,
                official_signal=official_signal,
                evidence_count=bucket["evidence_count"],
                used_llm=method == "llm",
            ),
            "relevance_hint": self._relevance_hint_from_flags(
                priority=priority,
                target_intent=target_intent,
                official_signal=official_signal,
                dataset_signal=dataset_signal,
            ),
            "classification_method": method,
        }

    def _heuristic_inference(self, bucket: dict[str, Any]) -> dict[str, Any]:
        title = self._resolve_title(bucket)
        text = " ".join(
            [
                bucket["domain"],
                title,
                *bucket["snippets"][:3],
                *bucket["answer_excerpts"][:2],
                " ".join(sorted(bucket["research_questions"])),
            ]
        ).lower()

        academic_signal = self._looks_academic(bucket["url"], text)
        official_signal = self._looks_official(text)
        dataset_signal = self._has_dataset_signal(text, bucket["url"])
        category = self._guess_category(
            academic_signal=academic_signal,
            official_signal=official_signal,
            dataset_signal=dataset_signal,
            text=text,
        )
        priority = self._priority_from_flags(
            dataset_signal=dataset_signal,
            official_signal=official_signal,
            academic_signal=academic_signal,
            category=category,
        )
        source_class = self._source_class_from_category(category=category, dataset_signal=dataset_signal)
        source_type = self._source_type_from_category(category=category)
        source_roles = self._default_source_roles(
            category=category,
            official_signal=official_signal,
            academic_signal=academic_signal,
            dataset_signal=dataset_signal,
        )
        target_intent = self._resolve_target_intent(bucket)
        dataset_names = [title] if dataset_signal else []

        return {
            "title": title,
            "url": bucket["url"],
            "domain": bucket["domain"],
            "category": category,
            "source_class": source_class,
            "source_type": source_type,
            "target_intent": target_intent,
            "dataset_signal": dataset_signal,
            "academic_signal": academic_signal,
            "official_signal": official_signal,
            "priority": priority,
            "search_profiles": set(bucket["search_profiles"]),
            "research_tracks": set(bucket["research_tracks"]),
            "supporting_query_ids": set(bucket["supporting_query_ids"]),
            "snippets": self._deduplicate_preserve_order(bucket["snippets"] + bucket["answer_excerpts"]),
            "evidence_count": bucket["evidence_count"],
            "dataset_names_mentioned": dataset_names,
            "variables_mentioned": [],
            "rationale": "heuristic_classification_from_text_and_url",
            "publisher_or_org": self._infer_publisher(bucket, title),
            "source_roles": source_roles,
            "data_extractability": self._extractability_from_text(
                dataset_signal=dataset_signal,
                category=category,
                text=text,
            ),
            "scientific_value": self._scientific_value_from_category(category),
            "recommended_pipeline_use": self._recommended_use_from_category(
                category=category,
                dataset_signal=dataset_signal,
                academic_signal=academic_signal,
            ),
            "article_value": self._article_value_from_category(category),
            "historical_records_available": self._optional_flag_from_text(text, ("historical", "series", "time series")),
            "structured_export_available": self._optional_flag_from_text(
                text, ("csv", "xlsx", "json", "download", "api", "geojson", "shapefile")
            ),
            "confidence": self._confidence_from_signals(
                dataset_signal=dataset_signal,
                academic_signal=academic_signal,
                official_signal=official_signal,
                evidence_count=bucket["evidence_count"],
                used_llm=False,
            ),
            "relevance_hint": self._relevance_hint_from_flags(
                priority=priority,
                target_intent=target_intent,
                official_signal=official_signal,
                dataset_signal=dataset_signal,
            ),
            "classification_method": "heuristic",
        }

    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed = urlparse(url.strip())
        if not parsed.scheme or not parsed.netloc:
            return ""
        path = parsed.path.rstrip("/") or "/"
        return f"{parsed.scheme}://{parsed.netloc}{path}"

    @staticmethod
    def _normalize_domain(domain: str, url: str) -> str:
        if domain:
            return domain.replace("www.", "").strip().lower()
        parsed = urlparse(url)
        return parsed.netloc.replace("www.", "").strip().lower()

    @staticmethod
    def _compact_text(text: str, *, limit: int) -> str:
        cleaned = " ".join(str(text or "").split())
        return cleaned[:limit]

    def _resolve_title(self, bucket: dict[str, Any]) -> str:
        for title in bucket["titles"]:
            cleaned = self._clean_text(title)
            if cleaned:
                return cleaned
        return bucket["domain"] or bucket["url"]

    @staticmethod
    def _clean_text(value: Any) -> str:
        return " ".join(str(value or "").split()).strip()

    @staticmethod
    def _clean_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        cleaned: list[str] = []
        for item in value:
            text = " ".join(str(item or "").split()).strip()
            if text and text not in cleaned:
                cleaned.append(text)
        return cleaned

    @staticmethod
    def _clean_choice(value: Any, allowed: set[str]) -> str | None:
        cleaned = " ".join(str(value or "").split()).strip()
        if cleaned in allowed:
            return cleaned
        return None

    @staticmethod
    def _coerce_optional_bool(value: Any) -> bool | None:
        if value is True or value is False:
            return value
        return None

    @staticmethod
    def _resolve_target_intent(bucket: dict[str, Any]) -> str:
        if bucket["target_intents"]:
            return sorted(bucket["target_intents"])[0]
        return "dataset_discovery"

    @staticmethod
    def _resolve_geographic_scope(master_context: PerplexityResearchContextRecord | None) -> str:
        if master_context and master_context.geographic_scope:
            return " / ".join(master_context.geographic_scope)
        return "not specified"

    @staticmethod
    def _source_type_from_category(*, category: str) -> str:
        if category == "official_data_portal":
            return "primary_data_portal"
        if category in {"institutional_report", "civil_society_monitoring"}:
            return "institutional_documentation"
        if category in {"academic_source", "repository"}:
            return "academic_literature"
        return "web_result"

    @staticmethod
    def _source_class_from_category(*, category: str, dataset_signal: bool) -> str:
        if dataset_signal and category in {"official_data_portal", "repository"}:
            return "analytical_data_source"
        return "scientific_knowledge_source"

    @staticmethod
    def _default_source_roles(
        *,
        category: str,
        official_signal: bool,
        academic_signal: bool,
        dataset_signal: bool,
    ) -> list[str]:
        roles: list[str] = []
        if dataset_signal:
            roles.append("data_provider")
        if official_signal:
            roles.append("institutional_context")
        if academic_signal:
            roles.append("scientific_evidence")
        if category in {"academic_source", "repository"}:
            roles.append("dataset_discovery_from_citations")
        if category in {"institutional_report", "civil_society_monitoring", "secondary_reference"}:
            roles.append("context_reference")
        return list(dict.fromkeys(roles or ["context_reference"]))

    @staticmethod
    def _recommended_use_from_category(
        *,
        category: str,
        dataset_signal: bool,
        academic_signal: bool,
    ) -> list[str]:
        uses: list[str] = []
        if dataset_signal:
            uses.append("dataset_discovery_from_source")
        if category == "official_data_portal":
            uses.append("direct_analytics_ingestion")
        if academic_signal or category in {"academic_source", "repository"}:
            uses.append("methodological_grounding")
            uses.append("dataset_discovery_from_citations")
        if category in {"institutional_report", "civil_society_monitoring"}:
            uses.append("contextual_baseline")
        if not uses:
            uses.append("context_reference")
        return list(dict.fromkeys(uses))

    @staticmethod
    def _article_value_from_category(category: str) -> str:
        if category in {"official_data_portal", "academic_source", "repository"}:
            return "high"
        if category in {"institutional_report", "civil_society_monitoring"}:
            return "medium"
        return "low"

    @staticmethod
    def _scientific_value_from_category(category: str) -> str:
        if category in {"academic_source", "repository"}:
            return "high"
        if category in {"official_data_portal", "institutional_report", "civil_society_monitoring"}:
            return "medium"
        return "low"

    @staticmethod
    def _priority_from_flags(
        *,
        dataset_signal: bool,
        official_signal: bool,
        academic_signal: bool,
        category: str,
    ) -> str:
        if dataset_signal and (official_signal or category == "repository"):
            return "high"
        if academic_signal or official_signal or category in {"institutional_report", "civil_society_monitoring"}:
            return "medium"
        return "low"

    @staticmethod
    def _extractability_from_text(*, dataset_signal: bool, category: str, text: str) -> str:
        if "api" in text or "download" in text or "csv" in text or "json" in text:
            return "high"
        if dataset_signal and category in {"official_data_portal", "repository"}:
            return "medium"
        if category in {"academic_source", "institutional_report"}:
            return "low"
        return "unknown"

    @staticmethod
    def _optional_flag_from_text(text: str, tokens: tuple[str, ...]) -> bool | None:
        return True if any(token in text for token in tokens) else None

    @staticmethod
    def _confidence_from_signals(
        *,
        dataset_signal: bool,
        academic_signal: bool,
        official_signal: bool,
        evidence_count: int,
        used_llm: bool,
    ) -> float:
        score = 0.45
        if dataset_signal:
            score += 0.15
        if official_signal:
            score += 0.15
        if academic_signal:
            score += 0.1
        if evidence_count >= 2:
            score += 0.1
        if used_llm:
            score += 0.03
        return round(min(score, 0.98), 2)

    @staticmethod
    def _relevance_hint_from_flags(
        *,
        priority: str,
        target_intent: str,
        official_signal: bool,
        dataset_signal: bool,
    ) -> float:
        score = 0.25
        if priority == "high":
            score += 0.35
        elif priority == "medium":
            score += 0.2
        if target_intent == "dataset_discovery":
            score += 0.15
        if official_signal:
            score += 0.1
        if dataset_signal:
            score += 0.1
        return round(min(score, 1.0), 2)

    @staticmethod
    def _infer_publisher(bucket: dict[str, Any], title: str) -> str:
        title_head = title.split(" - ")[0].strip()
        if title_head:
            return title_head[:80]
        domain = bucket["domain"]
        return domain.split(".")[0].replace("-", " ").upper()

    @staticmethod
    def _looks_academic(url: str, text: str) -> bool:
        combined = f"{url} {text}".lower()
        return any(
            token in combined
            for token in (
                "journal",
                "paper",
                "article",
                "thesis",
                "dissertation",
                "repository",
                "repositorio",
                "university",
                "universidade",
                "peer reviewed",
                "scientific",
                "academic",
                "doi",
            )
        )

    @staticmethod
    def _looks_official(text: str) -> bool:
        return any(
            token in text
            for token in (
                "governo",
                "government",
                "ministerio",
                "ministry",
                "secretaria",
                "agency",
                "agencia",
                "instituto",
                "public institute",
                "official portal",
                "official data",
                "public data",
                "administration",
                "prefeitura",
                "municipal",
                "estadual",
                "federal",
            )
        )

    @staticmethod
    def _has_dataset_signal(text: str, url: str) -> bool:
        combined = f"{text} {url}".lower()
        return any(
            token in combined
            for token in (
                "dataset",
                "data portal",
                "open data",
                "base de dados",
                "dados abertos",
                "catalog",
                "catalogo",
                "series",
                "time series",
                "historical",
                "monitoring",
                "monitoramento",
                "dashboard",
                "painel",
                "api",
                "download",
                "csv",
                "xlsx",
                "json",
                "geojson",
                "shp",
            )
        )

    @staticmethod
    def _guess_category(
        *,
        academic_signal: bool,
        official_signal: bool,
        dataset_signal: bool,
        text: str,
    ) -> str:
        if official_signal and dataset_signal:
            return "official_data_portal"
        if academic_signal and dataset_signal:
            return "repository"
        if academic_signal:
            return "academic_source"
        if official_signal:
            return "institutional_report"
        if any(token in text for token in ("ngo", "nonprofit", "foundation", "associacao", "observatory", "observatorio")):
            return "civil_society_monitoring"
        if any(token in text for token in ("news", "noticia", "jornal", "reportagem", "press")):
            return "journalistic_context"
        return "secondary_reference"

    @staticmethod
    def _deduplicate_preserve_order(items: list[str]) -> list[str]:
        ordered: list[str] = []
        seen: set[str] = set()
        for item in items:
            normalized = " ".join(str(item or "").split()).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
        return ordered
