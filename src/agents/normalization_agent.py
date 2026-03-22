"""Agente para normalizar e consolidar registros de datasets."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from src.agents.base import BaseAgent
from src.schemas.records import DatasetRecord


class NormalizationAgent(BaseAgent):
    name = "normalization"
    prompt_filename = "normalization_agent.yaml"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.get_system_prompt()

        source_lookup = {source.source_id: source for source in context.get("sources", [])}
        findings_by_source = {finding.source_id: finding for finding in context.get("web_research_results", [])}
        master_context = context.get("perplexity_master_context")

        buckets: dict[str, dict[str, Any]] = {}

        for candidate in context.get("dataset_candidates", []):
            key = self._build_dedupe_key(candidate.dataset_name, candidate.aliases, candidate.canonical_url)
            bucket = buckets.setdefault(
                key,
                {
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
                    "confidence_values": [],
                    "provenance": [],
                    "temporal_coverage": candidate.temporal_coverage,
                    "spatial_coverage": candidate.geographic_scope,
                    "update_frequency": candidate.update_frequency,
                    "source_class_votes": [],
                    "source_roles": set(),
                    "data_extractability_votes": [],
                    "historical_records_flags": [],
                    "structured_export_flags": [],
                    "scientific_value_votes": [],
                    "recommended_pipeline_use": set(),
                },
            )

            bucket["aliases"].update(candidate.aliases)
            bucket["source_ids"].update(candidate.source_ids)
            bucket["source_urls"].update(candidate.source_urls)
            bucket["variables"].update(self._normalize_open_labels(candidate.variables_mentioned))
            bucket["themes"].update(self._normalize_open_labels(candidate.tags))
            bucket["evidence_notes"].extend(candidate.evidence_notes)
            bucket["formats"].update(candidate.formats)
            bucket["tags"].update(candidate.tags)
            bucket["confidence_values"].append(candidate.confidence_hint)

            for source_id in candidate.source_ids:
                finding = findings_by_source.get(source_id)
                source = source_lookup.get(source_id)

                if finding:
                    bucket["source_class_votes"].append(finding.source_class)
                    bucket["source_roles"].update(finding.source_roles)
                    bucket["data_extractability_votes"].append(finding.data_extractability)
                    if finding.historical_records_available is not None:
                        bucket["historical_records_flags"].append(finding.historical_records_available)
                    if finding.structured_export_available is not None:
                        bucket["structured_export_flags"].append(finding.structured_export_available)
                    bucket["scientific_value_votes"].append(finding.scientific_value)
                    bucket["recommended_pipeline_use"].update(finding.recommended_pipeline_use)

                if source:
                    bucket["source_class_votes"].append(source.source_class)
                    bucket["source_roles"].update(source.source_roles)
                    bucket["data_extractability_votes"].append(source.data_extractability)
                    if source.historical_records_available is not None:
                        bucket["historical_records_flags"].append(source.historical_records_available)
                    if source.structured_export_available is not None:
                        bucket["structured_export_flags"].append(source.structured_export_available)
                    bucket["scientific_value_votes"].append(source.scientific_value)
                    bucket["recommended_pipeline_use"].update(source.recommended_pipeline_use)

                bucket["provenance"].append(
                    {
                        "source_id": source_id,
                        "source_type": source.source_type if source else "unknown",
                        "source_url": source.base_url if source else "",
                        "evidence": finding.evidence_notes if finding else "No evidence note available.",
                    }
                )

        normalized: list[DatasetRecord] = []
        for idx, bucket in enumerate(buckets.values(), start=1):
            sorted_source_ids = sorted(bucket["source_ids"])
            primary_source_id = sorted_source_ids[0] if sorted_source_ids else "src-unknown"
            source = source_lookup.get(primary_source_id)
            source_url = (
                bucket["canonical_url"]
                or (sorted(bucket["source_urls"])[0] if bucket["source_urls"] else "")
                or (source.base_url if source else "")
            )
            confidence = (
                round(sum(bucket["confidence_values"]) / len(bucket["confidence_values"]), 2)
                if bucket["confidence_values"]
                else 0.5
            )

            normalized.append(
                DatasetRecord(
                    dataset_id=f"norm-{idx:03d}",
                    title=bucket["title"],
                    aliases=sorted(alias for alias in bucket["aliases"] if alias and alias.lower() != bucket["title"].lower()),
                    canonical_url=source_url,
                    entity_type=bucket["entity_type"],
                    description=bucket["description"],
                    source_id=primary_source_id,
                    source_name=source.name if source else "Unknown source",
                    source_url=source_url,
                    source_class=self._majority_choice(bucket["source_class_votes"], default="analytical_data_source"),
                    source_roles=sorted(bucket["source_roles"]),
                    data_extractability=self._majority_choice(bucket["data_extractability_votes"], default="unknown"),
                    historical_records_available=self._bool_vote(bucket["historical_records_flags"]),
                    structured_export_available=self._bool_vote(bucket["structured_export_flags"]),
                    scientific_value=self._majority_choice(bucket["scientific_value_votes"], default="medium"),
                    recommended_pipeline_use=sorted(bucket["recommended_pipeline_use"]),
                    organization_normalized=self._normalize_organization(source.name if source else ""),
                    dataset_kind=bucket["entity_type"],
                    region=self._resolve_region(master_context),
                    thematic_axis=self._resolve_thematic_axis(master_context),
                    temporal_coverage=bucket["temporal_coverage"],
                    spatial_coverage=bucket["spatial_coverage"],
                    update_frequency=bucket["update_frequency"],
                    variables_normalized=sorted(bucket["variables"]),
                    themes_normalized=sorted(bucket["themes"]),
                    confidence=confidence,
                    priority=bucket["priority_hint"],
                    priority_reason=f"Priority carried from discovery stage ({bucket['priority_hint']}).",
                    methodological_notes=self._deduplicate_preserve_order(bucket["evidence_notes"]),
                    evidence_origin=sorted(bucket["source_urls"]),
                    provenance=bucket["provenance"],
                    formats=sorted(fmt for fmt in bucket["formats"] if fmt),
                    tags=sorted(self._normalize_open_labels(bucket["tags"])),
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
            return f"name::{normalized_name}::aliases::{'|'.join(normalized_aliases)}"
        return f"name::{normalized_name}"

    @staticmethod
    def _normalize_open_labels(values: list[str] | set[str]) -> set[str]:
        normalized: set[str] = set()
        for value in values:
            cleaned = " ".join(str(value or "").split()).strip().lower()
            if cleaned:
                normalized.add(cleaned)
        return normalized

    @staticmethod
    def _deduplicate_preserve_order(values: list[str]) -> list[str]:
        ordered: list[str] = []
        seen: set[str] = set()
        for value in values:
            cleaned = " ".join(str(value or "").split()).strip()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            ordered.append(cleaned)
        return ordered

    @staticmethod
    def _majority_choice(values: list[str], default: str) -> str:
        if not values:
            return default
        counts: dict[str, int] = {}
        for value in values:
            counts[value] = counts.get(value, 0) + 1
        return sorted(counts.items(), key=lambda item: item[1], reverse=True)[0][0]

    @staticmethod
    def _bool_vote(values: list[bool]) -> bool | None:
        if not values:
            return None
        positives = sum(1 for value in values if value)
        return positives >= (len(values) / 2)

    @staticmethod
    def _normalize_organization(org_name: str) -> str:
        normalized = " ".join(org_name.strip().upper().split())
        return normalized or "NOT SPECIFIED"

    @staticmethod
    def _resolve_region(master_context: Any) -> str:
        if master_context and getattr(master_context, "geographic_scope", None):
            return " | ".join(master_context.geographic_scope)
        return ""

    @staticmethod
    def _resolve_thematic_axis(master_context: Any) -> str:
        if master_context and getattr(master_context, "thematic_axes", None):
            return " | ".join(master_context.thematic_axes)
        return ""

    @staticmethod
    def _slugify(value: str) -> str:
        normalized = "".join(
            ch for ch in unicodedata.normalize("NFKD", value) if not unicodedata.combining(ch)
        )
        normalized = re.sub(r"[^a-zA-Z0-9]+", "-", normalized)
        return normalized.strip("-").lower()
