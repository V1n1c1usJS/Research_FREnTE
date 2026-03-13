"""Agente para consolidar candidatos de datasets a partir do scout e query expansion."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from typing import Any

from src.agents.base import BaseAgent
from src.schemas.records import DatasetCandidate


class DatasetDiscoveryAgent(BaseAgent):
    name = "dataset-discovery"
    prompt_filename = "dataset_discovery_agent.txt"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.get_system_prompt()
        findings = context.get("web_research_results", [])
        expanded_queries = context.get("expanded_queries", [])
        limit = context["settings"].limit

        query_list = [item["query"] for item in expanded_queries if isinstance(item, dict) and "query" in item]
        query_list = query_list or [context["settings"].query]

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
                "formats": set(),
                "tags": set(),
                "role_votes": [],
                "accessibility_votes": [],
                "confidence_values": [],
            }
        )

        for finding in findings:
            for dataset_name in finding.dataset_names_mentioned:
                key = self._canonical_key(dataset_name)
                bucket = grouped[key]
                canonical_name = dataset_name.strip()
                bucket["dataset_name"] = bucket["dataset_name"] or canonical_name
                bucket["aliases"].update({canonical_name.lower(), key})
                bucket["variables_mentioned"].update(finding.variables_mentioned)
                bucket["source_ids"].add(finding.source_id)
                bucket["source_urls"].add(finding.source_url)
                bucket["confidence_values"].append(finding.confidence)

                role_vote = self._role_from_finding(dataset_name, finding.source_type)
                bucket["role_votes"].append(role_vote)
                accessibility_vote = self._accessibility_from_source_type(finding.source_type)
                bucket["accessibility_votes"].append(accessibility_vote)
                bucket["mention_origins"].add(self._origin_from_source_type(finding.source_type))

                evidence_line = f"{finding.source_title}: {finding.evidence_notes}"
                bucket["evidence_notes"].append(evidence_line)
                bucket["source_mentions"].append(
                    {
                        "source_id": finding.source_id,
                        "source_type": finding.source_type,
                        "source_url": finding.source_url,
                        "source_title": finding.source_title,
                        "mention_type": accessibility_vote,
                        "evidence": finding.evidence_notes,
                    }
                )

                bucket["supporting_queries"].add(query_list[len(bucket["source_ids"]) % len(query_list)])
                bucket["formats"].update(self._infer_formats(dataset_name, finding.source_type))
                bucket["tags"].update(self._infer_tags(dataset_name, finding.variables_mentioned))

        candidates: list[DatasetCandidate] = []
        preliminary_catalog: list[dict[str, Any]] = []

        for idx, bucket in enumerate(grouped.values(), start=1):
            role = self._resolve_role(bucket["dataset_name"], bucket["role_votes"])
            confidence_hint = (
                round(sum(bucket["confidence_values"]) / len(bucket["confidence_values"]), 2)
                if bucket["confidence_values"]
                else 0.5
            )
            canonical_url = sorted(bucket["source_urls"])[0] if bucket["source_urls"] else ""
            accessibility = self._resolve_accessibility(bucket["accessibility_votes"])
            verifiability = self._resolve_verifiability_status(
                role=role,
                source_urls=bucket["source_urls"],
                source_mentions=bucket["source_mentions"],
                accessibility=accessibility,
            )
            mention_origins = sorted(bucket["mention_origins"])
            evidence_count = len(bucket["source_mentions"])

            candidate = DatasetCandidate(
                candidate_id=f"cand-{idx:03d}",
                dataset_name=bucket["dataset_name"],
                aliases=sorted(bucket["aliases"]),
                canonical_url=canonical_url,
                dataset_type="dataset" if role == "dataset" else "reference",
                candidate_role=role,
                description=(
                    "Candidato consolidado a partir de menções em portais institucionais, "
                    "bases acadêmicas e documentação técnica."
                ),
                variables_mentioned=sorted(bucket["variables_mentioned"]),
                source_ids=sorted(bucket["source_ids"]),
                source_urls=sorted(bucket["source_urls"]),
                source_mentions=bucket["source_mentions"],
                mention_origins=mention_origins,
                evidence_notes=bucket["evidence_notes"],
                supporting_queries=sorted(bucket["supporting_queries"]),
                temporal_coverage="não informado",
                update_frequency="não informado",
                formats=sorted(bucket["formats"]),
                tags=sorted(bucket["tags"]),
                evidence_count=evidence_count,
                accessibility=accessibility,
                verifiability_status=verifiability,
                confidence_hint=confidence_hint,
                priority_hint=self._infer_priority(bucket["source_ids"]),
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
                }
            )

        selected = candidates[:limit]
        selected_catalog = preliminary_catalog[:limit]

        report_lines = ["# Dataset Discovery - Catálogo Preliminar", ""]
        for item in selected:
            report_lines.append(
                "- "
                f"{item.dataset_name} | role={item.candidate_role} | acesso={item.accessibility} "
                f"| verificabilidade={item.verifiability_status} | fontes={', '.join(item.source_ids)}"
            )
            report_lines.append(
                f"  - origens={', '.join(item.mention_origins)} | confiança={item.confidence_hint}"
            )
            report_lines.append(f"  - evidência: {item.evidence_notes[0] if item.evidence_notes else 'n/a'}")

        return {
            "dataset_candidates": selected,
            "preliminary_catalog": selected_catalog,
            "dataset_discovery_report": "\n".join(report_lines),
        }

    @staticmethod
    def _canonical_key(dataset_name: str) -> str:
        lowered = dataset_name.lower().strip()
        lowered = "".join(ch for ch in unicodedata.normalize("NFKD", lowered) if not unicodedata.combining(ch))
        lowered = re.sub(r"[^a-z0-9à-ÿ\s]+", " ", lowered)
        lowered = re.sub(r"\s+", " ", lowered).strip()
        tokens = [t for t in lowered.split() if t not in {"de", "da", "do", "dos", "das", "e"}]
        return " ".join(tokens)

    @classmethod
    def _resolve_role(cls, dataset_name: str, role_votes: list[str]) -> str:
        lexical = cls._infer_role(dataset_name)
        if role_votes:
            if "portal" in role_votes:
                return "portal"
            if "documentation" in role_votes:
                return "documentation"
            if "academic_source" in role_votes:
                return "academic_source"
        return lexical

    @staticmethod
    def _role_from_finding(dataset_name: str, source_type: str) -> str:
        lexical = DatasetDiscoveryAgent._infer_role(dataset_name)
        if lexical != "dataset":
            return lexical
        if source_type == "academic_literature":
            return "academic_source"
        if source_type == "institutional_documentation":
            return "documentation"
        return "dataset"

    @staticmethod
    def _infer_role(dataset_name: str) -> str:
        lowered = dataset_name.lower()
        if any(token in lowered for token in ["portal", "painel"]):
            return "portal"
        if any(token in lowered for token in ["relatório", "tese", "artigo", "documento"]):
            return "documentation"
        if any(token in lowered for token in ["scielo", "capes", "acadêmic"]):
            return "academic_source"
        return "dataset"

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
    def _infer_formats(dataset_name: str, source_type: str) -> set[str]:
        lowered = dataset_name.lower()
        formats: set[str] = set()
        if "séries" in lowered or "indicadores" in lowered:
            formats.update({"csv", "xlsx"})
        if "relatório" in lowered or source_type in {"academic_literature", "institutional_documentation"}:
            formats.add("pdf")
        if not formats:
            formats.add("csv")
        return formats

    @staticmethod
    def _infer_tags(dataset_name: str, variables: list[str]) -> set[str]:
        tags = {"rio tietê", "reservatório de jupiá", "100k"}
        tags.update(v.lower() for v in variables)
        tags.add(dataset_name.lower())
        return tags

    @staticmethod
    def _infer_priority(source_ids: set[str]) -> str:
        if any(source in source_ids for source in {"src-hidroweb", "src-mapbiomas", "src-snis"}):
            return "high"
        if any(source in source_ids for source in {"src-ana", "src-ibge", "src-inpe"}):
            return "medium"
        return "low"
