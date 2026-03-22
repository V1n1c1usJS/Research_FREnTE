"""Pipeline principal de pesquisa para artigo via Perplexity + Playwright."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from src.agents.access_agent import AccessAgent
from src.agents.dataset_discovery_agent import DatasetDiscoveryAgent
from src.agents.normalization_agent import NormalizationAgent
from src.agents.perplexity_intelligence_report_agent import PerplexityIntelligenceReportAgent
from src.agents.perplexity_source_categorization_agent import PerplexitySourceCategorizationAgent
from src.agents.relevance_agent import RelevanceAgent
from src.agents.source_validation_agent import SourceValidationAgent
from src.connectors.llm import LLMConnector, LLMConnectorError, OpenAIResponsesConnector
from src.connectors.perplexity_playwright import PerplexityPlaywrightCollector
from src.schemas.records import (
    PerplexityResearchContextRecord,
    PerplexityResearchTrackRecord,
    PerplexitySearchQueryRecord,
)
from src.schemas.settings import PipelineSettings
from src.utils.io import ensure_dir, write_catalog_csv, write_json, write_markdown


class PerplexityIntelligencePipeline:
    """Executa o fluxo principal: contexto mestre, chats tematicos e consolidado de inteligencia."""

    DEFAULT_RESEARCH_TRACKS = (
        {
            "research_track": "official_data_portals",
            "chat_label": "chat-portais-oficiais",
            "search_profile": "official_portals",
            "target_intent": "dataset_discovery",
            "research_question": "Quais portais oficiais e fontes primarias concentram dados relevantes para esta pesquisa?",
            "task_prompt": (
                "Procure ministerios, agencias, institutos, catalogos, APIs, paineis e portais de dados "
                "diretamente relacionados ao tema da pesquisa."
            ),
            "priority": "high",
        },
        {
            "research_track": "monitoring_and_measurements",
            "chat_label": "chat-monitoramento",
            "search_profile": "monitoring_sources",
            "target_intent": "dataset_discovery",
            "research_question": "Quais fontes trazem monitoramento, series historicas e medidas recorrentes sobre o tema?",
            "task_prompt": (
                "Busque programas de monitoramento, series historicas, sensores, estacoes, indicadores e "
                "bases recorrentes ligadas ao objeto de estudo."
            ),
            "priority": "high",
        },
        {
            "research_track": "pressure_and_drivers",
            "chat_label": "chat-pressoes-e-vetores",
            "search_profile": "pressure_drivers",
            "target_intent": "dataset_discovery",
            "research_question": "Quais datasets ajudam a explicar vetores, pressoes e mudancas associadas ao tema?",
            "task_prompt": (
                "Procure bases sobre uso do territorio, ocupacao, pressao antropica, infraestruturas, "
                "saneamento, queimadas, cobertura do solo ou outros vetores relevantes ao tema."
            ),
            "priority": "medium",
        },
        {
            "research_track": "institutional_reports",
            "chat_label": "chat-relatorios-institucionais",
            "search_profile": "institutional_reports",
            "target_intent": "contextual_intelligence",
            "research_question": "Quais relatorios tecnicos e documentos institucionais ajudam a contextualizar a pesquisa?",
            "task_prompt": (
                "Procure relatorios tecnicos, planos, diagnosticos, boletins e documentos institucionais "
                "que ajudem a entender o contexto e apontem para fontes de dados."
            ),
            "priority": "medium",
        },
        {
            "research_track": "academic_knowledge",
            "chat_label": "chat-literatura-academica",
            "search_profile": "academic_knowledge",
            "target_intent": "academic_knowledge",
            "research_question": "Quais artigos, teses e repositorios academicos citam dados ou metodologias relevantes?",
            "task_prompt": (
                "Procure artigos, teses, revisoes e repositorios academicos que citem bases de dados, "
                "monitoramentos, protocolos ou abordagens metodologicas aproveitaveis."
            ),
            "priority": "medium",
        },
    )

    def __init__(
        self,
        *,
        base_query: str,
        limit: int = 20,
        max_searches: int = 5,
        preferred_model: str = "Sonar",
        playwright_timeout_seconds: float = 120.0,
        per_query_wait_ms: int = 7000,
        headed: bool = False,
        master_context_payload: dict[str, Any] | None = None,
        research_tracks_payload: list[dict[str, Any]] | None = None,
        llm_mode: str = "auto",
        llm_model: str = "gpt-4.1-nano",
        llm_timeout_seconds: float = 60.0,
        llm_fail_on_error: bool = False,
        llm_connector: LLMConnector | None = None,
        collector_factory: Callable[[], Any] | None = None,
    ) -> None:
        self.base_query = base_query
        self.limit = limit
        self.max_searches = max_searches
        self.preferred_model = preferred_model
        self.playwright_timeout_seconds = playwright_timeout_seconds
        self.per_query_wait_ms = per_query_wait_ms
        self.headed = headed
        self.master_context_payload = master_context_payload
        self.research_tracks_payload = research_tracks_payload
        self.llm_mode = llm_mode
        self.llm_model = llm_model
        self.llm_timeout_seconds = llm_timeout_seconds
        self.llm_fail_on_error = llm_fail_on_error
        self.llm_connector = llm_connector or self._build_llm_connector()
        self.collector_factory = collector_factory or (
            lambda: PerplexityPlaywrightCollector(
                preferred_model=self.preferred_model,
                timeout_seconds=self.playwright_timeout_seconds,
                per_query_wait_ms=self.per_query_wait_ms,
                headed=self.headed,
            )
        )

    def execute(self) -> dict[str, Any]:
        research_id = f"perplexity-intel-{uuid4().hex[:8]}"
        generated_at = datetime.now(timezone.utc).isoformat()
        init_dir = Path("data") / "initializations" / research_id
        ensure_dir(init_dir)

        master_context = self._build_master_context()
        research_tracks = self._build_research_tracks()
        search_plan = self._build_search_plan(master_context, research_tracks)
        write_json(init_dir / "00_master-context.json", master_context.model_dump(mode="json"))
        write_json(init_dir / "01_search-plan.json", [item.model_dump(mode="json") for item in search_plan])

        collector = self.collector_factory()
        sessions = collector.collect(search_plan)
        write_json(init_dir / "02_raw-sessions.json", [item.model_dump(mode="json") for item in sessions])

        settings = PipelineSettings(query=self.base_query, limit=self.limit)
        context: dict[str, Any] = {
            "base_query": self.base_query,
            "settings": settings,
            "perplexity_master_context": master_context,
            "perplexity_search_plan": search_plan,
            "perplexity_sessions": sessions,
        }

        agents = [
            PerplexitySourceCategorizationAgent(
                llm_connector=self.llm_connector,
                fail_on_error=self.llm_fail_on_error,
            ),
            SourceValidationAgent(),
            DatasetDiscoveryAgent(),
            NormalizationAgent(),
            RelevanceAgent(),
            AccessAgent(),
            PerplexityIntelligenceReportAgent(),
        ]

        for index, agent in enumerate(agents, start=3):
            updates = agent.run(context)
            context.update(updates)
            write_json(init_dir / f"{index:02d}_{agent.name}.json", self._serialize_updates(updates))

        report_path = Path("reports") / f"{research_id}.md"
        write_markdown(report_path, context["intelligence_markdown"])

        validation_by_source = {item.source_id: item for item in context.get("source_validation_log", [])}
        sources_csv_path = Path("reports") / f"{research_id}-sources.csv"
        write_catalog_csv(
            sources_csv_path,
            [
                {
                    "source_id": item.source_id,
                    "title": item.title,
                    "url": item.url,
                    "domain": item.domain,
                    "category": item.category,
                    "priority": item.priority,
                    "dataset_signal": item.dataset_signal,
                    "academic_signal": item.academic_signal,
                    "official_signal": item.official_signal,
                    "evidence_count": item.evidence_count,
                    "validation_status": validation_by_source.get(item.source_id).validation_status
                    if validation_by_source.get(item.source_id)
                    else "not_validated",
                    "validation_score": validation_by_source.get(item.source_id).validation_score
                    if validation_by_source.get(item.source_id)
                    else "",
                    "manual_validation_required": validation_by_source.get(item.source_id).manual_validation_required
                    if validation_by_source.get(item.source_id)
                    else "",
                    "target_intent": item.target_intent,
                    "search_profiles": ",".join(item.search_profiles),
                    "research_tracks": ",".join(item.research_tracks),
                }
                for item in context.get("categorized_sources", [])
            ],
            fieldnames=[
                "source_id",
                "title",
                "url",
                "domain",
                "category",
                "priority",
                "dataset_signal",
                "academic_signal",
                "official_signal",
                "evidence_count",
                "validation_status",
                "validation_score",
                "manual_validation_required",
                "target_intent",
                "search_profiles",
                "research_tracks",
            ],
        )

        datasets_csv_path = Path("reports") / f"{research_id}-datasets.csv"
        write_catalog_csv(
            datasets_csv_path,
            [
                {
                    "dataset_id": item.dataset_id,
                    "title": item.title,
                    "source_name": item.source_name,
                    "source_url": item.source_url,
                    "relevance_score": item.relevance_score,
                    "priority": item.priority,
                    "access_level": item.access_level,
                    "research_tracks": ",".join(item.research_tracks),
                    "target_intents": ",".join(item.target_intents),
                }
                for item in context.get("datasets", [])
            ],
            fieldnames=[
                "dataset_id",
                "title",
                "source_name",
                "source_url",
                "relevance_score",
                "priority",
                "access_level",
                "research_tracks",
                "target_intents",
            ],
        )

        intelligence_path = init_dir / "10_intelligence_payload.json"
        collection_meta = dict(context.get("perplexity_categorization_meta", {}))
        collection_meta["source_validation_meta"] = context.get("source_validation_meta", {})
        intelligence_payload = {
            "research_id": research_id,
            "generated_at": generated_at,
            "base_query": self.base_query,
            "master_context_path": str(init_dir / "00_master-context.json"),
            "preferred_model": self.preferred_model,
            "llm_mode": self.llm_mode,
            "llm_provider": self.llm_connector.provider if self.llm_connector else None,
            "llm_model": self.llm_connector.model if self.llm_connector else None,
            "search_plan_count": len(search_plan),
            "session_count": len(sessions),
            "categorized_source_count": len(context.get("categorized_sources", [])),
            "validated_source_count": len(context.get("source_validation_log", [])),
            "dataset_candidate_count": len(context.get("dataset_candidates", [])),
            "dataset_count": len(context.get("datasets", [])),
            "report_path": str(report_path),
            "sources_csv_path": str(sources_csv_path),
            "datasets_csv_path": str(datasets_csv_path),
            "collection_meta": collection_meta,
            "intelligence": context["intelligence_payload"],
        }
        write_json(intelligence_path, intelligence_payload)

        return {
            "research_id": research_id,
            "master_context_path": str(init_dir / "00_master-context.json"),
            "report_path": str(report_path),
            "sources_csv_path": str(sources_csv_path),
            "datasets_csv_path": str(datasets_csv_path),
            "intelligence_path": str(intelligence_path),
            "categorized_source_count": len(context.get("categorized_sources", [])),
            "validated_source_count": len(context.get("source_validation_log", [])),
            "dataset_candidate_count": len(context.get("dataset_candidates", [])),
            "dataset_count": len(context.get("datasets", [])),
        }

    def _build_master_context(self) -> PerplexityResearchContextRecord:
        if self.master_context_payload:
            return PerplexityResearchContextRecord.model_validate(self.master_context_payload)

        return PerplexityResearchContextRecord(
            context_id="ctx-article-001",
            article_goal=f"Discover sources, datasets and academic knowledge for the research topic: {self.base_query}",
            geographic_scope=[],
            thematic_axes=[
                "environmental context",
                "anthropic pressures and drivers",
                "monitoring and time series",
                "environmental response indicators",
                "scientific and institutional data sources",
            ],
            preferred_sources=[
                "official and institutional portals",
                "academic repositories",
                "technical reports with citations to data",
                "catalogs, APIs and time-series datasets",
            ],
            expected_outputs=[
                "direct links to portals, documents or repositories",
                "datasets and recurring monitoring programs",
                "academic studies that cite data sources",
                "methodological clues for the article",
            ],
            exclusions=[
                "generic summaries without sources",
                "promotional content",
                "low-value contextual noise",
            ],
            notes=[
                f"User-provided research context: {self.base_query}",
                "Prefer a few deep thematic chats over one broad generic search.",
            ],
        )

    def _build_research_tracks(self) -> list[PerplexityResearchTrackRecord]:
        payload = self.research_tracks_payload or list(self.DEFAULT_RESEARCH_TRACKS)
        tracks = [PerplexityResearchTrackRecord.model_validate(item) for item in payload]
        if self.research_tracks_payload:
            return tracks
        return tracks[: self.max_searches]

    def _build_search_plan(
        self,
        master_context: PerplexityResearchContextRecord,
        research_tracks: list[PerplexityResearchTrackRecord],
    ) -> list[PerplexitySearchQueryRecord]:
        plan: list[PerplexitySearchQueryRecord] = []
        for index, track in enumerate(research_tracks, start=1):
            query_text = self._compose_chat_prompt(master_context=master_context, track=track)
            plan.append(
                PerplexitySearchQueryRecord(
                    query_id=f"pplx-q-{index:02d}",
                    base_query=self.base_query,
                    query_text=query_text,
                    search_profile=track.search_profile,
                    target_intent=track.target_intent,
                    research_track=track.research_track,
                    chat_label=track.chat_label,
                    research_question=track.research_question,
                    task_prompt=track.task_prompt,
                    priority=track.priority,
                )
            )
        return plan

    @staticmethod
    def _compose_chat_prompt(
        *,
        master_context: PerplexityResearchContextRecord,
        track: PerplexityResearchTrackRecord,
    ) -> str:
        geographic_scope = PerplexityIntelligencePipeline._compact_items(master_context.geographic_scope, max_items=4, item_limit=120)
        thematic_axes = PerplexityIntelligencePipeline._compact_items(master_context.thematic_axes, max_items=6, item_limit=90)
        preferred_sources = PerplexityIntelligencePipeline._compact_items(
            master_context.preferred_sources,
            max_items=6,
            item_limit=80,
            strip_urls=True,
        )
        expected_outputs = PerplexityIntelligencePipeline._compact_items(master_context.expected_outputs, max_items=4, item_limit=90)
        exclusions = PerplexityIntelligencePipeline._compact_items(master_context.exclusions, max_items=3, item_limit=70)
        notes = PerplexityIntelligencePipeline._compact_items(master_context.notes, max_items=3, item_limit=90)

        return (
            f"Projeto 100K. Objetivo: {PerplexityIntelligencePipeline._compact_text(master_context.article_goal, 260)}. "
            f"Trilha: {track.research_track}. "
            f"Pergunta: {PerplexityIntelligencePipeline._compact_text(track.research_question, 220)}. "
            f"Tarefa: {PerplexityIntelligencePipeline._compact_text(track.task_prompt, 420)}. "
            f"Area: {geographic_scope}. "
            f"Eixos: {thematic_axes}. "
            f"Priorizar: {preferred_sources}. "
            f"Saidas esperadas: {expected_outputs}. "
            f"Evitar: {exclusions}. "
            f"Notas: {notes}. "
            "Retorne fontes oficiais, institucionais ou academicas, com links claros para portal, download, API, documento tecnico ou estudo cientifico."
        )

    @staticmethod
    def _compact_text(value: str, limit: int) -> str:
        cleaned = " ".join(str(value or "").split())
        if len(cleaned) <= limit:
            return cleaned
        return cleaned[: max(limit - 3, 0)].rstrip() + "..."

    @staticmethod
    def _compact_items(
        values: list[str],
        *,
        max_items: int,
        item_limit: int,
        strip_urls: bool = False,
    ) -> str:
        if not values:
            return "not specified"

        compacted: list[str] = []
        for item in values[:max_items]:
            text = " ".join(str(item or "").split())
            if strip_urls:
                text = re.sub(r"https?://\S+", "", text).strip(" -—,;")
            compacted.append(PerplexityIntelligencePipeline._compact_text(text, item_limit))

        remainder = len(values) - len(compacted)
        if remainder > 0:
            compacted.append(f"+{remainder} itens")

        return "; ".join(compacted)

    def _build_llm_connector(self) -> LLMConnector | None:
        if self.llm_mode == "off":
            return None

        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            if self.llm_mode == "openai":
                raise LLMConnectorError("OPENAI_API_KEY ausente para inferencia obrigatoria.")
            return None

        try:
            return OpenAIResponsesConnector(
                api_key=api_key,
                model=self.llm_model,
                timeout_seconds=self.llm_timeout_seconds,
            )
        except Exception:
            if self.llm_fail_on_error or self.llm_mode == "openai":
                raise
            return None

    @staticmethod
    def _serialize_updates(updates: dict[str, Any]) -> dict[str, Any]:
        serialized: dict[str, Any] = {}
        for key, value in updates.items():
            if hasattr(value, "model_dump"):
                serialized[key] = value.model_dump(mode="json")
            elif isinstance(value, list):
                serialized[key] = [
                    item.model_dump(mode="json") if hasattr(item, "model_dump") else item
                    for item in value
                ]
            else:
                serialized[key] = value
        return serialized
