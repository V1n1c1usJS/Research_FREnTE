"""Agente para expandir consultas de pesquisa a partir dos achados do scout."""

from __future__ import annotations

from typing import Any

from src.agents.base import BaseLLMAgent
from src.schemas.records import QueryExpansionRecord


class QueryExpansionAgent(BaseLLMAgent):
    name = "query-expansion"
    prompt_filename = "query_expansion_agent.txt"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.build_prompt(context)
        base_query = context["settings"].query
        web_findings = context.get("web_research_results", [])

        evidence_source_ids = [item.source_id for item in web_findings]
        variables = self._collect_variables(web_findings)

        expansions = self._build_expansions(evidence_source_ids)
        generated_queries = self._generate_queries(base_query, expansions, variables)

        expanded_queries = [
            {
                "query": base_query,
                "focus": "tema central",
                "stage": "dataset-discovery",
            }
        ]
        expanded_queries.extend(
            {
                "query": query,
                "focus": "expansão técnica e semântica",
                "stage": "dataset-discovery" if "artigo" not in query else "literature-discovery",
            }
            for query in generated_queries
        )

        return {
            "query_expansions": expansions,
            "expanded_queries": expanded_queries,
            "expansion_variables_detected": variables,
        }

    @staticmethod
    def _collect_variables(web_findings: list[Any]) -> list[str]:
        merged: list[str] = []
        for item in web_findings:
            merged.extend(item.variables_mentioned)
        return sorted(set(merged))

    @staticmethod
    def _build_expansions(evidence_source_ids: list[str]) -> list[QueryExpansionRecord]:
        return [
            QueryExpansionRecord(
                base_term="uso da terra",
                synonyms=["land use", "land cover", "land use change"],
                technical_terms=["LULC", "land cover classification"],
                variable_aliases=["uso e cobertura", "mudança de uso"],
                methodological_expressions=["change detection", "time-series land cover"],
                generated_queries=[
                    "land use change bacia do rio tietê",
                    "mapbiomas land cover rio tietê",
                ],
                evidence_source_ids=evidence_source_ids,
            ),
            QueryExpansionRecord(
                base_term="material orgânico",
                synonyms=["dissolved organic matter", "particulate organic matter", "organic carbon"],
                technical_terms=["DOM", "POM", "TOC"],
                variable_aliases=["carbono orgânico dissolvido", "carbono orgânico total"],
                methodological_expressions=["water quality assays", "biogeochemical proxies"],
                generated_queries=[
                    "dissolved organic matter rio tietê",
                    "organic carbon reservatório de jupiá",
                ],
                evidence_source_ids=evidence_source_ids,
            ),
            QueryExpansionRecord(
                base_term="esgoto",
                synonyms=["sanitation", "wastewater", "sewage discharge"],
                technical_terms=["wastewater treatment", "sewer network coverage"],
                variable_aliases=["coleta de esgoto", "tratamento de esgoto"],
                methodological_expressions=["sanitation indicators", "wastewater load estimation"],
                generated_queries=[
                    "wastewater indicadores municípios rio tietê",
                    "sanitation sewage discharge são paulo três lagoas",
                ],
                evidence_source_ids=evidence_source_ids,
            ),
            QueryExpansionRecord(
                base_term="queimadas",
                synonyms=["fire occurrence", "burned area", "fire hotspots"],
                technical_terms=["active fire", "burn scar"],
                variable_aliases=["focos de calor", "área queimada"],
                methodological_expressions=["remote sensing fire products", "spatiotemporal fire analysis"],
                generated_queries=[
                    "fire hotspots bacia do tietê",
                    "burned area inpe corridor são paulo três lagoas",
                ],
                evidence_source_ids=evidence_source_ids,
            ),
        ]

    @staticmethod
    def _generate_queries(base_query: str, expansions: list[QueryExpansionRecord], variables: list[str]) -> list[str]:
        generated: list[str] = []
        generated.append(f"{base_query} dataset portal oficial")
        generated.append(f"{base_query} artigo científico base de dados")

        for expansion in expansions:
            generated.extend(expansion.generated_queries)
            generated.extend(
                f"{base_query} {term}" for term in expansion.synonyms[:2]
            )

        for variable in variables[:4]:
            generated.append(f"{base_query} {variable} série histórica")

        return list(dict.fromkeys(generated))
