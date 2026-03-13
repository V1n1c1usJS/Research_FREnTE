"""Orquestrador do pipeline multiagente com persistência intermediária."""

from __future__ import annotations

from datetime import datetime
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
from src.schemas.records import PipelineRunMetadata
from src.schemas.settings import PipelineSettings
from src.utils.io import ensure_dir, write_catalog_csv, write_json, write_markdown
from src.utils.prompts import load_prompt


class OrchestratorAgent:
    """Executa os agentes em sequência e salva artefatos rastreáveis."""

    prompt_filename = "orchestrator_agent.yaml"

    def __init__(self, settings: PipelineSettings) -> None:
        self.settings = settings
        self.agents = [
            ResearchScoutAgent(
                web_research_mode="mock" if settings.dry_run else settings.web_research_mode,
                timeout_seconds=settings.web_timeout_seconds,
            ),
            QueryExpansionAgent(),
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
        now = datetime.utcnow()
        mode = "dry-run" if self.settings.dry_run else "run"

        run_dir = Path("data") / "runs" / run_id
        ensure_dir(run_dir)

        metadata = PipelineRunMetadata(
            run_id=run_id,
            mode=mode,
            query=self.settings.query,
            started_at=now,
        )

        context: dict[str, Any] = {
            "settings": self.settings,
            "run_metadata": metadata,
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

        metadata.finished_at = datetime.utcnow()
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
