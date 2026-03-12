"""Agente para normalizar registros de datasets."""

from __future__ import annotations

from typing import Any

from src.agents.base import BaseAgent
from src.schemas.records import DatasetRecord


class NormalizationAgent(BaseAgent):
    name = "normalization"
    prompt_filename = "normalization_agent.txt"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.get_system_prompt()

        normalized = [
            DatasetRecord(
                dataset_id=item["dataset_id"],
                title=item["title"],
                description=item["description"],
                source_id=item["source_id"],
                source_name=item["source_name"],
                source_url=item["source_url"],
                dataset_kind=item["dataset_kind"],
                temporal_coverage=item["temporal_coverage"],
                spatial_coverage=item["spatial_coverage"],
                update_frequency=item["update_frequency"],
                priority=item["priority_hint"],
                priority_reason=f"Prioridade inicial sugerida em descoberta ({item['priority_hint']}).",
                methodological_notes=item["methodological_notes"],
                evidence_origin=item["evidence_origin"],
                formats=item["formats"],
                tags=item["tags"] + [item["query_focus"], item["discovery_stage"]],
            )
            for item in context["raw_datasets"]
        ]
        return {"datasets": normalized}
