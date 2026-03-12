"""Agente para planejar extração dos datasets."""

from __future__ import annotations

from typing import Any

from src.agents.base import BaseAgent


class ExtractionPlanAgent(BaseAgent):
    name = "extraction-plan"
    prompt_filename = "extraction_plan_agent.txt"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.get_system_prompt()

        plan = []
        for dataset in context["datasets"]:
            if dataset.priority == "high":
                strategy = "ingest-first"
                order = 1
            elif dataset.priority == "medium":
                strategy = "ingest-second"
                order = 2
            else:
                strategy = "ingest-later"
                order = 3

            plan.append(
                {
                    "dataset_id": dataset.dataset_id,
                    "strategy": strategy,
                    "priority": dataset.priority,
                    "execution_order": order,
                    "methodological_observation": (
                        "Plano simulado para dry-run; sem conexão com APIs reais nesta fase."
                    ),
                    "notes": "Extensão futura: conector automático por fonte.",
                }
            )

        return {"extraction_plan": sorted(plan, key=lambda item: item["execution_order"])}
