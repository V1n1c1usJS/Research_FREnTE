"""Agente para normalizar e consolidar registros de datasets."""

from __future__ import annotations

from typing import Any

from src.agents.base import BaseAgent
from src.schemas.records import DatasetRecord


class NormalizationAgent(BaseAgent):
    name = "normalization"
    prompt_filename = "normalization_agent.txt"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.get_system_prompt()

        source_lookup = {source.source_id: source for source in context.get("sources", [])}
        findings_by_source = {finding.source_id: finding for finding in context.get("web_research_results", [])}

        buckets: dict[str, dict[str, Any]] = {}

        for candidate in context.get("dataset_candidates", []):
            key = self._build_dedupe_key(candidate.dataset_name, candidate.aliases, candidate.canonical_url)
            if key not in buckets:
                buckets[key] = {
                    "candidate_ids": set(),
                    "title": candidate.dataset_name,
                    "aliases": set(candidate.aliases),
                    "canonical_url": candidate.canonical_url,
                    "entity_type": candidate.candidate_role,
                    "description": candidate.description,
                    "source_ids": set(),
                    "source_urls": set(),
                    "variables": set(),
                    "themes": set(),
                    "evidence_notes": [],
                    "formats": set(),
                    "tags": set(),
                    "priority_hint": candidate.priority_hint,
                    "confidence_values": [candidate.confidence_hint],
                    "provenance": [],
                    "temporal_coverage": candidate.temporal_coverage,
                    "spatial_coverage": candidate.geographic_scope,
                    "update_frequency": candidate.update_frequency,
                }

            bucket = buckets[key]
            bucket["candidate_ids"].add(candidate.candidate_id)
            bucket["aliases"].update(candidate.aliases)
            bucket["source_ids"].update(candidate.source_ids)
            bucket["source_urls"].update(candidate.source_urls)
            bucket["variables"].update(self._normalize_variables(candidate.variables_mentioned))
            bucket["themes"].update(self._normalize_themes(candidate.tags))
            bucket["evidence_notes"].extend(candidate.evidence_notes)
            bucket["formats"].update(candidate.formats)
            bucket["tags"].update(candidate.tags)
            bucket["confidence_values"].append(candidate.confidence_hint)

            for source_id in candidate.source_ids:
                finding = findings_by_source.get(source_id)
                bucket["provenance"].append(
                    {
                        "source_id": source_id,
                        "source_type": source_lookup[source_id].source_type if source_id in source_lookup else "unknown",
                        "source_url": (
                            source_lookup[source_id].base_url if source_id in source_lookup else ""
                        ),
                        "evidence": finding.evidence_notes if finding else "Evidência não disponível no achado atual.",
                    }
                )

        normalized: list[DatasetRecord] = []
        for idx, (_, bucket) in enumerate(buckets.items(), start=1):
            sorted_source_ids = sorted(bucket["source_ids"])
            primary_source_id = sorted_source_ids[0] if sorted_source_ids else "src-unknown"
            source = source_lookup.get(primary_source_id)

            source_url = (
                bucket["canonical_url"]
                or (sorted(bucket["source_urls"])[0] if bucket["source_urls"] else "")
                or (source.base_url if source else "")
            )
            confidence = round(sum(bucket["confidence_values"]) / len(bucket["confidence_values"]), 2)

            normalized.append(
                DatasetRecord(
                    dataset_id=f"norm-{idx:03d}",
                    title=bucket["title"],
                    aliases=sorted(alias for alias in bucket["aliases"] if alias and alias != bucket["title"].lower()),
                    canonical_url=source_url,
                    entity_type=bucket["entity_type"],
                    description=bucket["description"],
                    source_id=primary_source_id,
                    source_name=source.name if source else "Fonte não identificada",
                    source_url=source_url,
                    organization_normalized=self._normalize_organization(source.name if source else ""),
                    dataset_kind=bucket["entity_type"],
                    temporal_coverage=bucket["temporal_coverage"],
                    spatial_coverage=bucket["spatial_coverage"],
                    update_frequency=bucket["update_frequency"],
                    variables_normalized=sorted(bucket["variables"]),
                    themes_normalized=sorted(bucket["themes"]),
                    confidence=confidence,
                    priority=bucket["priority_hint"],
                    priority_reason=(
                        f"Prioridade inicial preservada da descoberta ({bucket['priority_hint']})."
                    ),
                    methodological_notes=bucket["evidence_notes"],
                    evidence_origin=sorted(bucket["source_urls"]),
                    provenance=bucket["provenance"],
                    formats=sorted(bucket["formats"]),
                    tags=sorted(bucket["tags"]),
                )
            )

        return {"datasets": normalized}

    @staticmethod
    def _build_dedupe_key(name: str, aliases: list[str], canonical_url: str) -> str:
        normalized_name = name.strip().lower()
        normalized_aliases = sorted(alias.strip().lower() for alias in aliases if alias.strip())
        if canonical_url:
            return f"url::{canonical_url.strip().lower()}"
        if normalized_aliases:
            alias_part = "|".join(normalized_aliases)
            return f"name::{normalized_name}::aliases::{alias_part}"
        return f"name::{normalized_name}"

    @staticmethod
    def _normalize_organization(org_name: str) -> str:
        normalized = org_name.strip().upper()
        aliases = {
            "AGÊNCIA NACIONAL DE ÁGUAS E SANEAMENTO BÁSICO": "ANA",
            "BASES ACADÊMICAS E RELATÓRIOS TÉCNICOS": "BASES ACADÊMICAS",
        }
        return aliases.get(normalized, normalized or "NÃO INFORMADO")

    @staticmethod
    def _normalize_variables(variables: list[str]) -> set[str]:
        mapping = {
            "vazão": "streamflow",
            "nível": "water level",
            "chuva": "precipitation",
            "uso da terra": "land use",
            "qualidade da água": "water quality",
            "esgoto": "wastewater",
            "resíduos": "solid waste",
            "queimadas": "fire occurrence",
            "material orgânico": "organic matter",
            "ocupação urbana": "urban occupation",
            "sedimentos": "sediments",
            "meteorologia": "meteorology",
        }
        normalized = set()
        for item in variables:
            key = item.strip().lower()
            normalized.add(mapping.get(key, key))
        return normalized

    @staticmethod
    def _normalize_themes(tags: list[str]) -> set[str]:
        themes = set()
        for tag in tags:
            lowered = tag.lower()
            if any(token in lowered for token in ["land", "uso"]):
                themes.add("land-use-change")
            elif any(token in lowered for token in ["água", "water", "hidrologia", "vazão"]):
                themes.add("hydrology-water-quality")
            elif any(token in lowered for token in ["esgoto", "wastewater", "resíduo"]):
                themes.add("sanitation-waste")
            elif any(token in lowered for token in ["queimada", "fire"]):
                themes.add("fire-disturbance")
            elif any(token in lowered for token in ["urbana", "demografia"]):
                themes.add("urban-pressure")
        if not themes:
            themes.add("unclassified")
        return themes
