"""Agente para atribuir score de relevância com critérios explícitos do projeto 100K."""

from __future__ import annotations

from typing import Any

from src.agents.base import BaseAgent


class RelevanceAgent(BaseAgent):
    name = "relevance"
    prompt_filename = "relevance_agent.yaml"

    # Pesos explícitos (somam 1.0) para saída auditável/reproduzível.
    CRITERIA_WEIGHTS = {
        "geographic_adherence": 0.25,
        "thematic_adherence": 0.35,
        "data_readiness": 0.15,
        "evidence_strength": 0.15,
        "source_confidence": 0.10,
    }

    PRESSURE_TERMS = {
        "land use",
        "desmatamento",
        "fire occurrence",
        "queimadas",
        "wastewater",
        "solid waste",
        "urban occupation",
        "esgoto",
        "resíduos",
    }
    PHYSICAL_TERMS = {
        "hydrology-water-quality",
        "streamflow",
        "water level",
        "meteorology",
        "precipitation",
        "relevo",
        "hydrology",
    }
    RESPONSE_TERMS = {
        "water quality",
        "sediments",
        "organic matter",
        "material orgânico",
        "qualidade da água",
    }

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.get_system_prompt()

        scored = []
        for dataset in context["datasets"]:
            geographic_adherence = self._score_geography(dataset)
            thematic_adherence = self._score_thematic(dataset)
            data_readiness = self._score_data_readiness(dataset)
            evidence_strength = self._score_evidence(dataset)
            source_confidence = float(dataset.confidence)

            weighted = (
                geographic_adherence * self.CRITERIA_WEIGHTS["geographic_adherence"]
                + thematic_adherence * self.CRITERIA_WEIGHTS["thematic_adherence"]
                + data_readiness * self.CRITERIA_WEIGHTS["data_readiness"]
                + evidence_strength * self.CRITERIA_WEIGHTS["evidence_strength"]
                + source_confidence * self.CRITERIA_WEIGHTS["source_confidence"]
            )
            score = round(min(max(weighted, 0.0), 1.0), 3)

            category_scores = self._category_scores(dataset)
            priority = self._priority_from_score(score)

            rationale = {
                "weights": self.CRITERIA_WEIGHTS,
                "criterion_scores": {
                    "geographic_adherence": geographic_adherence,
                    "thematic_adherence": thematic_adherence,
                    "data_readiness": data_readiness,
                    "evidence_strength": evidence_strength,
                    "source_confidence": source_confidence,
                },
                "category_scores": category_scores,
                "formula": "sum(weight_i * score_i)",
            }

            scored.append(
                dataset.model_copy(
                    update={
                        "relevance_score": score,
                        "priority": priority,
                        "priority_reason": (
                            f"Prioridade '{priority}' derivada de score {score} com critérios ponderados do projeto 100K."
                        ),
                        "relevance_rationale": (
                            "Score calculado por aderência geográfica, aderência temática, prontidão de dados, "
                            "força de evidência e confiança de origem."
                        ),
                        "relevance_breakdown": rationale,
                    }
                )
            )

        return {"datasets": scored}

    def _score_geography(self, dataset: Any) -> float:
        text = f"{dataset.spatial_coverage} {dataset.region} {dataset.title}".lower()
        points = 0.0
        if "tiet" in text:
            points += 0.45
        if "jupi" in text or "reservat" in text:
            points += 0.25
        if "são paulo" in text or "três lagoas" in text or "corredor" in text:
            points += 0.2
        if points == 0:
            points = 0.2
        return round(min(points, 1.0), 3)

    def _score_thematic(self, dataset: Any) -> float:
        pool = {v.lower() for v in dataset.variables_normalized} | {t.lower() for t in dataset.themes_normalized}
        pressure = 1.0 if pool & {t.lower() for t in self.PRESSURE_TERMS} else 0.2
        physical = 1.0 if pool & {t.lower() for t in self.PHYSICAL_TERMS} else 0.2
        response = 1.0 if pool & {t.lower() for t in self.RESPONSE_TERMS} else 0.2
        base = (pressure + physical + response) / 3

        if dataset.source_class == "scientific_knowledge_source":
            methodological_bonus = 0.25 if any(
                token in " ".join(dataset.methodological_notes).lower()
                for token in ["métod", "method", "review", "artigo", "tese", "literatura"]
            ) else 0.0
            citation_discovery_bonus = 0.2 if "dataset_discovery_from_citations" in dataset.recommended_pipeline_use else 0.0
            return round(min(base + methodological_bonus + citation_discovery_bonus, 1.0), 3)

        return round(base, 3)

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
        structured_formats = {"csv", "xlsx", "parquet", "netcdf", "geotiff", "json"}
        if set(f.lower() for f in dataset.formats) & structured_formats:
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

    def _category_scores(self, dataset: Any) -> dict[str, float]:
        pool = {v.lower() for v in dataset.variables_normalized} | {t.lower() for t in dataset.themes_normalized}
        pressure = 1.0 if pool & {t.lower() for t in self.PRESSURE_TERMS} else 0.0
        physical = 1.0 if pool & {t.lower() for t in self.PHYSICAL_TERMS} else 0.0
        response = 1.0 if pool & {t.lower() for t in self.RESPONSE_TERMS} else 0.0
        return {
            "anthropic_pressure": pressure,
            "physical_context": physical,
            "environmental_response": response,
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
