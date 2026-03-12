"""Agente para atribuir score de relevância."""

from __future__ import annotations

from typing import Any

from src.agents.base import BaseAgent


class RelevanceAgent(BaseAgent):
    name = "relevance"
    prompt_filename = "relevance_agent.txt"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.get_system_prompt()
        query = context["settings"].query.lower()

        kind_weights = {
            "water-quality": 0.95,
            "hydrology": 0.92,
            "sanitation": 0.9,
            "land-use": 0.87,
            "climate": 0.8,
            "socioeconomic": 0.74,
            "literature": 0.7,
        }

        scored = []
        for dataset in context["datasets"]:
            baseline = kind_weights.get(dataset.dataset_kind, 0.65)
            query_match = 0.03 if any(token in dataset.description.lower() for token in query.split()) else 0.0
            score = round(min(baseline + query_match, 0.99), 2)

            if score >= 0.9:
                priority = "high"
            elif score >= 0.78:
                priority = "medium"
            else:
                priority = "low"

            scored.append(
                dataset.model_copy(
                    update={
                        "relevance_score": score,
                        "priority": priority,
                        "priority_reason": (
                            f"Prioridade '{priority}' derivada de score simulado {score} "
                            f"e tipo {dataset.dataset_kind}."
                        ),
                        "relevance_rationale": (
                            "Score simulado considerando aderência temática, cobertura espacial e utilidade "
                            "para análise de impactos humanos no eixo Tietê-Jupiá."
                        ),
                    }
                )
            )

        return {"datasets": scored}
