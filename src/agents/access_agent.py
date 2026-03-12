"""Agente para classificar nível de acesso dos datasets."""

from __future__ import annotations

from typing import Any

from src.agents.base import BaseAgent


class AccessAgent(BaseAgent):
    name = "access"
    prompt_filename = "access_agent.txt"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.get_system_prompt()

        updated = []
        for dataset in context["datasets"]:
            if "pdf" in dataset.formats and dataset.dataset_kind == "literature":
                access_level = "open-with-review"
                access_notes = "Fonte textual exige triagem manual de evidências e citações."
            elif dataset.source_name in {"ANA", "Hidroweb", "MapBiomas", "IBGE", "INPE", "SNIS"}:
                access_level = "open"
                access_notes = "Mock de base pública; confirmar termos reais em integração futura."
            else:
                access_level = "unknown"
                access_notes = "Sem evidência suficiente no mock atual."

            updated.append(
                dataset.model_copy(update={"access_level": access_level, "access_notes": access_notes})
            )

        return {"datasets": updated}
