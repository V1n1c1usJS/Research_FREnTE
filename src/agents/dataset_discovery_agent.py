"""Agente para consolidar candidatos de dataset a partir das fontes categorizadas."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from typing import Any

from src.agents.base import BaseAgent
from src.schemas.records import DatasetCandidate


class DatasetDiscoveryAgent(BaseAgent):
    name = "dataset-discovery"
    prompt_filename = "dataset_discovery_agent.yaml"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.get_system_prompt()
        findings = context.get("web_research_results", [])
        limit = context["settings"].limit

        grouped: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "dataset_name": "",
                "aliases": set(),
                "variables_mentioned": set(),
                "source_ids": set(),
                "source_urls": set(),
                "source_mentions": [],
                "mention_origins": set(),
                "evidence_notes": [],
                "supporting_queries": set(),
                "research_tracks": set(),
                "search_profiles": set(),
                "target_intents": set(),
                "formats": set(),
                "tags": set(),
                "role_votes": [],
                "accessibility_votes": [],
                "confidence_values": [],
            }
        )

        for finding in findings:
            dataset_names = list(finding.dataset_names_mentioned)
            if not dataset_names and finding.source_class == "analytical_data_source":
                dataset_names = [finding.source_title]

            for dataset_name in dataset_names:
                cleaned_name = dataset_name.strip()
                if not cleaned_name:
                    continue

                key = self._canonical_key(cleaned_name)
                bucket = grouped[key]
                bucket["dataset_name"] = bucket["dataset_name"] or cleaned_name
                bucket["aliases"].update({cleaned_name.lower(), key})
                bucket["variables_mentioned"].update(self._clean_list(finding.variables_mentioned))
                bucket["source_ids"].add(finding.source_id)
                bucket["source_urls"].add(finding.source_url)
                bucket["confidence_values"].append(float(finding.confidence))
                bucket["role_votes"].append(self._role_from_finding(dataset_name=cleaned_name, finding=finding))
                bucket["accessibility_votes"].append(self._accessibility_from_source_type(finding.source_type))
                bucket["mention_origins"].add(self._origin_from_source_type(finding.source_type))
                bucket["evidence_notes"].append(f"{finding.source_title}: {finding.evidence_notes}")
                bucket["source_mentions"].append(
                    {
                        "source_id": finding.source_id,
                        "source_type": finding.source_type,
                        "source_url": finding.source_url,
                        "source_title": finding.source_title,
                        "mention_type": self._accessibility_from_source_type(finding.source_type),
                        "evidence": finding.evidence_notes,
                    }
                )
                bucket["supporting_queries"].update(self._clean_list(finding.search_terms_extracted))
                bucket["research_tracks"].update(self._clean_list(getattr(finding, "research_tracks", [])))
                bucket["search_profiles"].update(self._clean_list(getattr(finding, "search_profiles", [])))
                if getattr(finding, "target_intent", ""):
                    bucket["target_intents"].add(finding.target_intent)
                bucket["formats"].update(self._infer_formats(cleaned_name, finding.source_url, finding.evidence_notes))
                bucket["tags"].update(self._infer_tags(cleaned_name, finding.variables_mentioned, finding.search_terms_extracted))

        candidates: list[DatasetCandidate] = []
        preliminary_catalog: list[dict[str, Any]] = []

        for idx, bucket in enumerate(grouped.values(), start=1):
            evidence_count = len(bucket["source_mentions"])
            role = self._resolve_role(bucket["role_votes"])
            confidence_hint = (
                round(sum(bucket["confidence_values"]) / len(bucket["confidence_values"]), 2)
                if bucket["confidence_values"]
                else 0.5
            )
            accessibility = self._resolve_accessibility(bucket["accessibility_votes"])
            verifiability = self._resolve_verifiability_status(
                role=role,
                source_urls=bucket["source_urls"],
                source_mentions=bucket["source_mentions"],
                accessibility=accessibility,
            )
            priority_hint = self._infer_priority(
                evidence_count=evidence_count,
                accessibility=accessibility,
                confidence_hint=confidence_hint,
            )
            canonical_url = sorted(bucket["source_urls"])[0] if bucket["source_urls"] else ""
            supporting_queries = sorted(bucket["supporting_queries"]) or [context["settings"].query]

            candidate = DatasetCandidate(
                candidate_id=f"cand-{idx:03d}",
                dataset_name=bucket["dataset_name"],
                aliases=sorted(bucket["aliases"]),
                canonical_url=canonical_url,
                dataset_type="dataset" if role in {"dataset", "portal"} else "reference",
                candidate_role=role,
                description=(
                    "Candidate consolidated from source mentions collected via Perplexity and validated through the "
                    "categorization stage."
                ),
                variables_mentioned=sorted(bucket["variables_mentioned"]),
                source_ids=sorted(bucket["source_ids"]),
                source_urls=sorted(bucket["source_urls"]),
                source_mentions=bucket["source_mentions"],
                mention_origins=sorted(bucket["mention_origins"]),
                evidence_notes=bucket["evidence_notes"],
                supporting_queries=supporting_queries,
                research_tracks=sorted(bucket["research_tracks"]),
                search_profiles=sorted(bucket["search_profiles"]),
                target_intents=sorted(bucket["target_intents"]),
                temporal_coverage="not specified",
                update_frequency="not specified",
                formats=sorted(bucket["formats"]),
                tags=sorted(bucket["tags"]),
                evidence_count=evidence_count,
                accessibility=accessibility,
                verifiability_status=verifiability,
                confidence_hint=confidence_hint,
                priority_hint=priority_hint,
            )
            candidates.append(candidate)
            preliminary_catalog.append(
                {
                    "candidate_id": candidate.candidate_id,
                    "dataset_name": candidate.dataset_name,
                    "candidate_role": candidate.candidate_role,
                    "accessibility": candidate.accessibility,
                    "verifiability_status": candidate.verifiability_status,
                    "mention_origins": candidate.mention_origins,
                    "source_ids": candidate.source_ids,
                    "source_urls": candidate.source_urls,
                    "evidence_count": candidate.evidence_count,
                    "confidence_hint": candidate.confidence_hint,
                    "priority_hint": candidate.priority_hint,
                    "research_tracks": candidate.research_tracks,
                    "search_profiles": candidate.search_profiles,
                    "target_intents": candidate.target_intents,
                }
            )

        selected = candidates[:limit]
        selected_catalog = preliminary_catalog[:limit]

        report_lines = ["# Dataset Discovery - Preliminary Catalog", ""]
        for item in selected:
            report_lines.append(
                f"- {item.dataset_name} | role={item.candidate_role} | access={item.accessibility} "
                f"| verifiability={item.verifiability_status} | evidence={item.evidence_count}"
            )

        return {
            "dataset_candidates": selected,
            "preliminary_catalog": selected_catalog,
            "dataset_discovery_report": "\n".join(report_lines),
        }

    @staticmethod
    def _canonical_key(dataset_name: str) -> str:
        lowered = dataset_name.lower().strip()
        lowered = "".join(ch for ch in unicodedata.normalize("NFKD", lowered) if not unicodedata.combining(ch))
        lowered = re.sub(r"[^a-z0-9\s]+", " ", lowered)
        lowered = re.sub(r"\s+", " ", lowered).strip()
        tokens = [token for token in lowered.split() if token not in {"de", "da", "do", "dos", "das", "e"}]
        return " ".join(tokens)

    @staticmethod
    def _clean_list(values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in values:
            normalized = " ".join(str(item or "").split()).strip()
            if normalized and normalized not in cleaned:
                cleaned.append(normalized)
        return cleaned

    @staticmethod
    def _role_from_finding(*, dataset_name: str, finding: Any) -> str:
        lowered = dataset_name.lower()
        if finding.source_type == "academic_literature":
            return "academic_source"
        if finding.source_type == "institutional_documentation":
            return "documentation"
        if finding.source_type == "primary_data_portal":
            if any(token in lowered for token in ("portal", "painel", "dashboard", "catalogo", "catalog")):
                return "portal"
            return "dataset"
        return "dataset"

    @staticmethod
    def _resolve_role(role_votes: list[str]) -> str:
        if not role_votes:
            return "dataset"
        counts: dict[str, int] = {}
        for role in role_votes:
            counts[role] = counts.get(role, 0) + 1
        return sorted(counts.items(), key=lambda item: item[1], reverse=True)[0][0]

    @staticmethod
    def _accessibility_from_source_type(source_type: str) -> str:
        if source_type == "primary_data_portal":
            return "direct_access"
        if source_type == "academic_literature":
            return "literature_citation"
        return "institutional_reference"

    @staticmethod
    def _origin_from_source_type(source_type: str) -> str:
        mapping = {
            "primary_data_portal": "primary",
            "academic_literature": "academic",
            "institutional_documentation": "institutional",
            "web_result": "web",
        }
        return mapping.get(source_type, "unknown")

    @staticmethod
    def _resolve_accessibility(votes: list[str]) -> str:
        unique = set(votes)
        if "direct_access" in unique and "literature_citation" in unique:
            return "mixed"
        if "direct_access" in unique:
            return "direct_access"
        if "literature_citation" in unique:
            return "literature_citation"
        return "institutional_reference"

    @staticmethod
    def _resolve_verifiability_status(
        *,
        role: str,
        source_urls: set[str],
        source_mentions: list[dict[str, str]],
        accessibility: str,
    ) -> str:
        has_url = bool(source_urls)
        unique_source_types = {item.get("source_type", "") for item in source_mentions}
        if not has_url:
            return "unverifiable"
        if accessibility == "literature_citation":
            return "cited_not_directly_accessible"
        if accessibility == "mixed":
            return "partially_verifiable"
        if role in {"portal", "dataset"} and "primary_data_portal" in unique_source_types:
            return "verifiable"
        if role in {"documentation", "academic_source"}:
            return "evidence_only"
        return "needs_manual_validation"

    @staticmethod
    def _infer_formats(dataset_name: str, source_url: str, evidence_notes: str) -> set[str]:
        text = f"{dataset_name} {source_url} {evidence_notes}".lower()
        formats = {
            token
            for token in ("csv", "xlsx", "json", "geojson", "shp", "pdf", "zip", "xml", "api")
            if token in text
        }
        return formats or {"unknown"}

    @staticmethod
    def _infer_tags(dataset_name: str, variables: list[str], search_terms: list[str]) -> set[str]:
        tags = {dataset_name.lower()}
        tags.update(item.lower() for item in DatasetDiscoveryAgent._clean_list(variables))
        tags.update(item.lower() for item in DatasetDiscoveryAgent._clean_list(search_terms))
        return tags

    @staticmethod
    def _infer_priority(*, evidence_count: int, accessibility: str, confidence_hint: float) -> str:
        if accessibility == "direct_access" and (evidence_count >= 2 or confidence_hint >= 0.75):
            return "high"
        if accessibility in {"direct_access", "mixed"} or confidence_hint >= 0.6:
            return "medium"
        return "low"
