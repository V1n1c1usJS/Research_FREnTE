"""Agente para atribuir score de relevancia com criterios auditaveis."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from src.agents.base import BaseAgent


class RelevanceAgent(BaseAgent):
    name = "relevance"
    prompt_filename = "relevance_agent.yaml"

    CRITERIA_WEIGHTS = {
        "geographic_adherence": 0.25,
        "thematic_adherence": 0.35,
        "data_readiness": 0.15,
        "evidence_strength": 0.15,
        "source_confidence": 0.10,
    }

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.get_system_prompt()
        master_context = context.get("perplexity_master_context")

        scored = []
        for dataset in context["datasets"]:
            geographic_adherence = self._score_geography(dataset, master_context)
            thematic_adherence = self._score_thematic(dataset, master_context)
            data_readiness = self._score_data_readiness(dataset)
            evidence_strength = self._score_evidence(dataset)
            source_confidence = float(dataset.confidence)
            axis_scores = self._axis_scores(dataset, master_context)
            expected_output_scores = self._expected_output_scores(dataset, master_context)

            weighted = (
                geographic_adherence * self.CRITERIA_WEIGHTS["geographic_adherence"]
                + thematic_adherence * self.CRITERIA_WEIGHTS["thematic_adherence"]
                + data_readiness * self.CRITERIA_WEIGHTS["data_readiness"]
                + evidence_strength * self.CRITERIA_WEIGHTS["evidence_strength"]
                + source_confidence * self.CRITERIA_WEIGHTS["source_confidence"]
            )
            score = round(min(max(weighted, 0.0), 1.0), 3)
            priority = self._priority_from_score(score)

            scored.append(
                dataset.model_copy(
                    update={
                        "relevance_score": score,
                        "priority": priority,
                        "priority_reason": f"Priority '{priority}' derived from weighted score {score}.",
                        "relevance_rationale": (
                            "Score calculated from geographic adherence, thematic adherence, data readiness, "
                            "evidence strength and source confidence."
                        ),
                        "relevance_breakdown": {
                            "weights": self.CRITERIA_WEIGHTS,
                            "criterion_scores": {
                                "geographic_adherence": geographic_adherence,
                                "thematic_adherence": thematic_adherence,
                                "data_readiness": data_readiness,
                                "evidence_strength": evidence_strength,
                                "source_confidence": source_confidence,
                            },
                            "axis_scores": axis_scores,
                            "expected_output_scores": expected_output_scores,
                            "formula": "sum(weight_i * score_i)",
                        },
                    }
                )
            )

        return {"datasets": scored}

    def _score_geography(self, dataset: Any, master_context: Any) -> float:
        scope_terms = getattr(master_context, "geographic_scope", []) or []
        if not scope_terms:
            return 0.5

        dataset_tokens = self._tokenize(
            " ".join([dataset.spatial_coverage, dataset.region, dataset.title, " ".join(dataset.tags)])
        )
        overlaps = [self._phrase_overlap(dataset_tokens, phrase) for phrase in scope_terms]
        best_overlap = max(overlaps, default=0.0)
        return round(min(0.2 + (best_overlap * 0.8), 1.0), 3)

    def _score_thematic(self, dataset: Any, master_context: Any) -> float:
        thematic_axes = getattr(master_context, "thematic_axes", []) or []
        expected_outputs = getattr(master_context, "expected_outputs", []) or []
        exclusions = getattr(master_context, "exclusions", []) or []
        dataset_text = " ".join(
            [
                dataset.title,
                dataset.description,
                " ".join(dataset.variables_normalized),
                " ".join(dataset.themes_normalized),
                " ".join(dataset.methodological_notes[:3]),
            ]
        )
        dataset_tokens = self._tokenize(dataset_text)

        if not thematic_axes and not expected_outputs:
            return 0.5

        axis_scores = [self._phrase_overlap(dataset_tokens, phrase) for phrase in thematic_axes]
        output_scores = [self._phrase_overlap(dataset_tokens, phrase) for phrase in expected_outputs]
        base_score = self._mean_score(axis_scores, default=0.0) * 0.75 + self._mean_score(output_scores, default=0.0) * 0.25

        if dataset.source_class == "scientific_knowledge_source":
            if "methodological_grounding" in dataset.recommended_pipeline_use:
                base_score += 0.15
            if "dataset_discovery_from_citations" in dataset.recommended_pipeline_use:
                base_score += 0.15

        exclusion_hits = [self._phrase_overlap(dataset_tokens, phrase) for phrase in exclusions]
        if max(exclusion_hits, default=0.0) >= 0.4:
            base_score -= 0.2

        return round(min(max(base_score, 0.0), 1.0), 3)

    @staticmethod
    def _score_data_readiness(dataset: Any) -> float:
        if dataset.source_class == "scientific_knowledge_source":
            score = 0.2
            if dataset.scientific_value == "high":
                score += 0.45
            elif dataset.scientific_value == "medium":
                score += 0.3
            if "dataset_discovery_from_citations" in dataset.recommended_pipeline_use:
                score += 0.2
            if dataset.entity_type in {"documentation", "academic_source"}:
                score += 0.1
            return round(min(score, 1.0), 3)

        score = 0.0
        structured_formats = {"csv", "xlsx", "parquet", "netcdf", "geotiff", "json", "geojson", "shp"}
        if set(fmt.lower() for fmt in dataset.formats) & structured_formats:
            score += 0.35
        if dataset.structured_export_available is True:
            score += 0.25
        if dataset.historical_records_available is True:
            score += 0.2
        if dataset.data_extractability == "high":
            score += 0.2
        elif dataset.data_extractability == "medium":
            score += 0.1
        return round(min(score, 1.0), 3)

    @staticmethod
    def _score_evidence(dataset: Any) -> float:
        evidence_count = len(dataset.evidence_origin) + len(dataset.methodological_notes) + len(dataset.provenance)
        if evidence_count >= 6:
            return 1.0
        if evidence_count >= 4:
            return 0.8
        if evidence_count >= 2:
            return 0.6
        if evidence_count >= 1:
            return 0.4
        return 0.2

    def _axis_scores(self, dataset: Any, master_context: Any) -> dict[str, float]:
        thematic_axes = getattr(master_context, "thematic_axes", []) or []
        if not thematic_axes:
            return {}

        text = " ".join(
            [
                dataset.title,
                dataset.description,
                " ".join(dataset.variables_normalized),
                " ".join(dataset.themes_normalized),
                " ".join(dataset.tags),
            ]
        )
        tokens = self._tokenize(text)
        return {
            axis: round(self._phrase_overlap(tokens, axis), 3)
            for axis in thematic_axes
        }

    def _expected_output_scores(self, dataset: Any, master_context: Any) -> dict[str, float]:
        expected_outputs = getattr(master_context, "expected_outputs", []) or []
        if not expected_outputs:
            return {}

        text = " ".join(
            [
                dataset.title,
                dataset.description,
                " ".join(dataset.variables_normalized),
                " ".join(dataset.themes_normalized),
                " ".join(dataset.tags),
            ]
        )
        tokens = self._tokenize(text)
        return {
            output: round(self._phrase_overlap(tokens, output), 3)
            for output in expected_outputs
        }

    @staticmethod
    def _priority_from_score(score: float) -> str:
        if score >= 0.85:
            return "critical"
        if score >= 0.72:
            return "high"
        if score >= 0.55:
            return "medium"
        if score >= 0.35:
            return "low"
        return "discard"

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        normalized = "".join(
            ch for ch in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(ch)
        )
        normalized = re.sub(r"[^a-z0-9\s]+", " ", normalized)
        return {token for token in normalized.split() if token}

    def _phrase_overlap(self, dataset_tokens: set[str], phrase: str) -> float:
        phrase_tokens = self._tokenize(phrase)
        if not phrase_tokens:
            return 0.0
        return len(dataset_tokens & phrase_tokens) / len(phrase_tokens)

    @staticmethod
    def _mean_score(values: list[float], default: float = 0.5) -> float:
        if not values:
            return default
        return sum(values) / len(values)
