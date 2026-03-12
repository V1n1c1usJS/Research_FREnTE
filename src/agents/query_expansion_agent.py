"""Agente para expandir consultas de pesquisa."""

from __future__ import annotations

from typing import Any

from src.agents.base import BaseLLMAgent


class QueryExpansionAgent(BaseLLMAgent):
    name = "query-expansion"
    prompt_filename = "query_expansion_agent.txt"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.build_prompt(context)
        base_query = context["settings"].query

        expanded_queries = [
            {
                "query": base_query,
                "focus": "tema central",
                "stage": "dataset-discovery",
            },
            {
                "query": f"{base_query} qualidade da água rio tietê",
                "focus": "qualidade da água",
                "stage": "dataset-discovery",
            },
            {
                "query": "mapbiomas uso e cobertura do solo bacia do tietê",
                "focus": "pressão antrópica no uso do solo",
                "stage": "dataset-discovery",
            },
            {
                "query": "snis saneamento municípios corredor tietê jupiá",
                "focus": "infraestrutura de saneamento",
                "stage": "dataset-discovery",
            },
            {
                "query": "artigos e relatórios técnicos impactos humanos reservatório de jupiá",
                "focus": "literatura e relatório técnico",
                "stage": "literature-discovery",
            },
        ]
        return {"expanded_queries": expanded_queries}
