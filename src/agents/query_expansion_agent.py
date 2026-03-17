"""Agente para expandir consultas de pesquisa a partir dos achados do scout."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from src.agents.base import BaseLLMAgent
from src.schemas.records import QueryExpansionRecord


class _LLMQueryExpansionItem(BaseModel):
    base_term: str
    synonyms: list[str] = Field(default_factory=list)
    technical_terms: list[str] = Field(default_factory=list)
    variable_aliases: list[str] = Field(default_factory=list)
    methodological_expressions: list[str] = Field(default_factory=list)
    generated_queries: list[str] = Field(default_factory=list)


class _LLMQueryExpansionPayload(BaseModel):
    variables: list[str] = Field(default_factory=list)
    generated_queries: list[str] = Field(default_factory=list)
    expansions: list[_LLMQueryExpansionItem] = Field(default_factory=list)


class QueryExpansionAgent(BaseLLMAgent):
    name = "query-expansion"
    prompt_filename = "query_expansion_agent.yaml"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        base_query = context["settings"].query
        web_findings = context.get("web_research_results", [])

        evidence_source_ids = [item.source_id for item in web_findings]
        variables = self._collect_variables(web_findings)

        query_expansion_meta = {
            "execution_mode": "heuristic",
            "provider": None,
            "model": None,
            "error": None,
        }

        if self.has_llm:
            try:
                expansions, generated_queries, variables = self._expand_with_llm(
                    base_query=base_query,
                    web_findings=web_findings,
                    evidence_source_ids=evidence_source_ids,
                    fallback_variables=variables,
                )
                query_expansion_meta.update(
                    {
                        "execution_mode": "llm",
                        "provider": self.llm_connector.provider,
                        "model": self.llm_connector.model,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                query_expansion_meta["error"] = f"{type(exc).__name__}: {exc}"
                if self.fail_on_error:
                    raise
                expansions = self._build_expansions(evidence_source_ids)
                generated_queries = self._generate_queries(base_query, expansions, variables)
        else:
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
                "focus": "expansao tecnica e semantica",
                "stage": "dataset-discovery" if "artigo" not in query.lower() else "literature-discovery",
            }
            for query in generated_queries
        )

        return {
            "query_expansions": expansions,
            "expanded_queries": expanded_queries,
            "expansion_variables_detected": variables,
            "query_expansion_meta": query_expansion_meta,
        }

    def _expand_with_llm(
        self,
        *,
        base_query: str,
        web_findings: list[Any],
        evidence_source_ids: list[str],
        fallback_variables: list[str],
    ) -> tuple[list[QueryExpansionRecord], list[str], list[str]]:
        findings_summary = []
        for item in web_findings[:8]:
            findings_summary.append(
                {
                    "source_id": item.source_id,
                    "source_title": item.source_title,
                    "source_type": item.source_type,
                    "dataset_names_mentioned": item.dataset_names_mentioned[:4],
                    "variables_mentioned": item.variables_mentioned[:6],
                    "source_url": item.source_url,
                }
            )

        user_prompt = (
            "Base query:\n"
            f"{base_query}\n\n"
            "Achados resumidos do scout (JSON):\n"
            f"{findings_summary}\n\n"
            "Retorne apenas JSON valido com o formato:\n"
            "{\n"
            '  "variables": ["..."],\n'
            '  "generated_queries": ["..."],\n'
            '  "expansions": [\n'
            "    {\n"
            '      "base_term": "...",\n'
            '      "synonyms": ["..."],\n'
            '      "technical_terms": ["..."],\n'
            '      "variable_aliases": ["..."],\n'
            '      "methodological_expressions": ["..."],\n'
            '      "generated_queries": ["..."]\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Regras:\n"
            "- produza no maximo 6 expansoes;\n"
            "- priorize hidrologia, qualidade da agua, uso da terra, saneamento e queimadas quando houver evidencia;\n"
            "- mantenha queries curtas e pesquisaveis;\n"
            "- inclua termos em portugues e ingles quando fizer sentido;\n"
            "- nao invente fontes inexistentes."
        )

        payload = self.llm_connector.generate_json(
            system_prompt=self.get_system_prompt(),
            user_prompt=user_prompt,
        )
        parsed = _LLMQueryExpansionPayload.model_validate(payload)

        variables = sorted(set(parsed.variables or fallback_variables))
        expansions = [
            QueryExpansionRecord(
                base_term=item.base_term,
                synonyms=self._deduplicate(item.synonyms),
                technical_terms=self._deduplicate(item.technical_terms),
                variable_aliases=self._deduplicate(item.variable_aliases),
                methodological_expressions=self._deduplicate(item.methodological_expressions),
                generated_queries=self._deduplicate(item.generated_queries),
                evidence_source_ids=evidence_source_ids,
            )
            for item in parsed.expansions[:6]
            if item.base_term.strip()
        ]
        if not expansions:
            expansions = self._build_expansions(evidence_source_ids)

        generated_queries = self._deduplicate(
            [query for query in parsed.generated_queries if query.strip()]
            + self._generate_queries(base_query, expansions, variables)
        )
        return expansions, generated_queries, variables

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
                variable_aliases=["uso e cobertura", "mudanca de uso"],
                methodological_expressions=["change detection", "time-series land cover"],
                generated_queries=[
                    "land use change bacia do rio tiete",
                    "mapbiomas land cover rio tiete",
                ],
                evidence_source_ids=evidence_source_ids,
            ),
            QueryExpansionRecord(
                base_term="material organico",
                synonyms=["dissolved organic matter", "particulate organic matter", "organic carbon"],
                technical_terms=["DOM", "POM", "TOC"],
                variable_aliases=["carbono organico dissolvido", "carbono organico total"],
                methodological_expressions=["water quality assays", "biogeochemical proxies"],
                generated_queries=[
                    "dissolved organic matter rio tiete",
                    "organic carbon reservatorio de jupia",
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
                    "wastewater indicadores municipios rio tiete",
                    "sanitation sewage discharge sao paulo tres lagoas",
                ],
                evidence_source_ids=evidence_source_ids,
            ),
            QueryExpansionRecord(
                base_term="queimadas",
                synonyms=["fire occurrence", "burned area", "fire hotspots"],
                technical_terms=["active fire", "burn scar"],
                variable_aliases=["focos de calor", "area queimada"],
                methodological_expressions=["remote sensing fire products", "spatiotemporal fire analysis"],
                generated_queries=[
                    "fire hotspots bacia do tiete",
                    "burned area inpe corridor sao paulo tres lagoas",
                ],
                evidence_source_ids=evidence_source_ids,
            ),
        ]

    @staticmethod
    def _generate_queries(base_query: str, expansions: list[QueryExpansionRecord], variables: list[str]) -> list[str]:
        generated: list[str] = []
        generated.append(f"{base_query} dataset portal oficial")
        generated.append(f"{base_query} artigo cientifico base de dados")

        for expansion in expansions:
            generated.extend(expansion.generated_queries)
            generated.extend(f"{base_query} {term}" for term in expansion.synonyms[:2])

        for variable in variables[:4]:
            generated.append(f"{base_query} {variable} serie historica")

        return QueryExpansionAgent._deduplicate(generated)

    @staticmethod
    def _deduplicate(values: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for value in values:
            cleaned = value.strip()
            key = cleaned.lower()
            if cleaned and key not in seen:
                seen.add(key)
                normalized.append(cleaned)
        return normalized
