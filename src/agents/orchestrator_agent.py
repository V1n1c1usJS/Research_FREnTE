"""Orquestrador do pipeline multiagente com persistencia intermediaria."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.agents.access_agent import AccessAgent
from src.agents.dataset_discovery_agent import DatasetDiscoveryAgent
from src.agents.extraction_plan_agent import ExtractionPlanAgent
from src.agents.normalization_agent import NormalizationAgent
from src.agents.query_expansion_agent import QueryExpansionAgent
from src.agents.relevance_agent import RelevanceAgent
from src.agents.report_agent import ReportAgent
from src.agents.research_scout_agent import ResearchScoutAgent
from src.connectors.llm import (
    GroqResponsesConnector,
    LLMConnector,
    LLMConnectorError,
    OpenAIResponsesConnector,
)
from src.schemas.records import PipelineRunMetadata
from src.schemas.settings import PipelineSettings
from src.utils.io import ensure_dir, write_catalog_csv, write_json, write_markdown
from src.utils.prompts import load_prompt


class OrchestratorAgent:
    """Executa os agentes em sequencia e salva artefatos rastreaveis."""

    prompt_filename = "orchestrator_agent.yaml"

    def __init__(self, settings: PipelineSettings) -> None:
        self.settings = settings
        self.llm_setup_error: str | None = None
        self.llm_connector = self._build_llm_connector()
        self.agents = [
            ResearchScoutAgent(
                web_research_mode="mock" if settings.dry_run else settings.web_research_mode,
                timeout_seconds=settings.web_timeout_seconds,
                llm_connector=self.llm_connector,
                fail_on_error=settings.llm_fail_on_error,
            ),
            QueryExpansionAgent(
                llm_connector=self.llm_connector,
                fail_on_error=settings.llm_fail_on_error,
            ),
            DatasetDiscoveryAgent(),
            NormalizationAgent(),
            RelevanceAgent(),
            AccessAgent(),
            ExtractionPlanAgent(),
            ReportAgent(),
        ]

    def run(self) -> dict[str, Any]:
        _prompt = load_prompt(self.prompt_filename)
        run_id = f"run-{uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)
        mode = "dry-run" if self.settings.dry_run else "run"

        run_dir = Path("data") / "runs" / run_id
        ensure_dir(run_dir)

        metadata = PipelineRunMetadata(
            run_id=run_id,
            mode=mode,
            query=self.settings.query,
            started_at=now,
            llm_mode_requested=self.settings.llm_mode,
            llm_provider_used=self.llm_connector.provider if self.llm_connector else None,
            llm_model_used=self.llm_connector.model if self.llm_connector else None,
            llm_enabled_agents=[
                agent.name for agent in self.agents if getattr(agent, "has_llm", False)
            ],
            llm_setup_error=self.llm_setup_error,
        )

        context: dict[str, Any] = {
            "settings": self.settings,
            "run_metadata": metadata,
            "llm_runtime": {
                "requested_mode": self.settings.llm_mode,
                "active_provider": self.llm_connector.provider if self.llm_connector else "heuristic",
                "active_model": self.llm_connector.model if self.llm_connector else None,
                "setup_error": self.llm_setup_error,
            },
        }

        for agent in self.agents:
            updates = agent.run(context)
            context.update(updates)
            metadata.steps.append(agent.name)

            serializable = self._serialize_updates(updates)
            step_file = run_dir / f"{len(metadata.steps):02d}_{agent.name}.json"
            write_json(step_file, serializable)
            metadata.intermediate_files.append(str(step_file))

        report_path = Path("reports") / f"{run_id}.md"
        write_markdown(report_path, context["report_markdown"])
        metadata.report_file = str(report_path)

        catalog_path = run_dir / "catalog.json"
        write_json(catalog_path, context["catalog_export"].model_dump(mode="json"))
        metadata.intermediate_files.append(str(catalog_path))

        export_path = Path("reports") / f"{run_id}.csv"
        rows = [
            {
                "dataset_id": d.dataset_id,
                "title": d.title,
                "source_name": d.source_name,
                "source_url": d.source_url,
                "relevance_score": d.relevance_score,
                "access_level": d.access_level,
                "priority": d.priority,
                "dataset_kind": d.dataset_kind,
                "methodological_note": " | ".join(d.methodological_notes[:1]),
            }
            for d in context["datasets"]
        ]
        write_catalog_csv(export_path, rows)
        metadata.export_file = str(export_path)

        metadata.finished_at = datetime.now(timezone.utc)
        metadata.status = "completed"
        metadata_path = run_dir / "run_metadata.json"
        write_json(metadata_path, metadata.model_dump(mode="json"))

        return {
            "run_id": run_id,
            "report_path": str(report_path),
            "catalog_path": str(catalog_path),
            "export_path": str(export_path),
            "metadata_path": str(metadata_path),
            "dataset_count": len(context["datasets"]),
        }

    def _build_llm_connector(self) -> LLMConnector | None:
        if self.settings.dry_run:
            self.llm_setup_error = "LLM desabilitado em dry-run para preservar execucao sem efeitos externos."
            return None

        if self.settings.llm_mode == "off":
            return None

        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        groq_api_key = os.getenv("GROQ_API_KEY", "").strip()

        if self.settings.llm_mode == "openai" and not openai_api_key:
            raise LLMConnectorError(
                "OPENAI_API_KEY ausente. Defina a chave no ambiente ou no arquivo .env."
            )
        if self.settings.llm_mode == "groq" and not groq_api_key:
            raise LLMConnectorError(
                "GROQ_API_KEY ausente. Defina a chave no ambiente ou no arquivo .env."
            )
        if self.settings.llm_mode == "auto" and not openai_api_key and not groq_api_key:
            self.llm_setup_error = "Nenhuma chave LLM configurada; fallback heuristico ativado."
            return None

        try:
            if self.settings.llm_mode == "groq":
                return GroqResponsesConnector(
                    api_key=groq_api_key,
                    model=self._resolve_model_for_provider("groq"),
                    timeout_seconds=self.settings.llm_timeout_seconds,
                    max_output_tokens=self.settings.llm_max_output_tokens,
                    temperature=self.settings.llm_temperature,
                )

            if openai_api_key:
                return OpenAIResponsesConnector(
                    api_key=openai_api_key,
                    model=self._resolve_model_for_provider("openai"),
                    timeout_seconds=self.settings.llm_timeout_seconds,
                    max_output_tokens=self.settings.llm_max_output_tokens,
                    temperature=self.settings.llm_temperature,
                )

            if groq_api_key:
                return GroqResponsesConnector(
                    api_key=groq_api_key,
                    model=self._resolve_model_for_provider("groq"),
                    timeout_seconds=self.settings.llm_timeout_seconds,
                    max_output_tokens=self.settings.llm_max_output_tokens,
                    temperature=self.settings.llm_temperature,
                )

            self.llm_setup_error = "Nenhuma chave LLM configurada; fallback heuristico ativado."
            return None
        except Exception as exc:  # noqa: BLE001
            self.llm_setup_error = f"{type(exc).__name__}: {exc}"
            if self.settings.llm_mode in {"openai", "groq"} or self.settings.llm_fail_on_error:
                raise
            return None

    def _resolve_model_for_provider(self, provider: str) -> str:
        if provider == "groq" and self.settings.llm_model == "gpt-4.1-nano":
            return os.getenv("RESEARCH_FRENTE_GROQ_TEST_MODEL", "groq/compound-mini")
        return self.settings.llm_model

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
