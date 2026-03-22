"""Agente para validar a consistencia das fontes categorizadas antes do discovery."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from src.agents.base import BaseAgent
from src.schemas.records import (
    IntelligenceSourceRecord,
    ResearchSourceRecord,
    SourceValidationRecord,
    WebResearchResultRecord,
)


class SourceValidationAgent(BaseAgent):
    name = "source-validation"
    prompt_filename = "source_validation_agent.yaml"

    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.get_system_prompt()

        categorized_sources: list[IntelligenceSourceRecord] = context.get("categorized_sources", [])
        sources_by_id = {source.source_id: source for source in context.get("sources", [])}
        findings_by_id = {finding.source_id: finding for finding in context.get("web_research_results", [])}

        validated_categorized: list[IntelligenceSourceRecord] = []
        validated_sources: list[ResearchSourceRecord] = []
        validated_findings: list[WebResearchResultRecord] = []
        validation_log: list[SourceValidationRecord] = []

        status_summary: dict[str, int] = defaultdict(int)
        issue_summary: dict[str, int] = defaultdict(int)
        adjusted_count = 0
        manual_count = 0

        for item in categorized_sources:
            source = sources_by_id.get(item.source_id)
            finding = findings_by_id.get(item.source_id)
            validated_item, validated_source, validated_finding, validation = self._validate_bundle(
                item=item,
                source=source,
                finding=finding,
            )
            validated_categorized.append(validated_item)
            if validated_source is not None:
                validated_sources.append(validated_source)
            if validated_finding is not None:
                validated_findings.append(validated_finding)
            validation_log.append(validation)

            status_summary[validation.validation_status] += 1
            if validation.manual_validation_required:
                manual_count += 1
            if validation.adjustments:
                adjusted_count += 1
            for issue in validation.issues:
                issue_summary[issue] += 1

        validation_meta = {
            "validated_source_count": len(validation_log),
            "status_summary": dict(status_summary),
            "manual_validation_required_count": manual_count,
            "adjusted_source_count": adjusted_count,
            "issue_summary": dict(issue_summary),
        }

        return {
            "categorized_sources": validated_categorized,
            "sources": validated_sources,
            "web_research_results": validated_findings,
            "source_validation_log": validation_log,
            "source_validation_meta": validation_meta,
        }

    def _validate_bundle(
        self,
        *,
        item: IntelligenceSourceRecord,
        source: ResearchSourceRecord | None,
        finding: WebResearchResultRecord | None,
    ) -> tuple[IntelligenceSourceRecord, ResearchSourceRecord | None, WebResearchResultRecord | None, SourceValidationRecord]:
        issues: list[str] = []
        adjustments: list[str] = []
        category = item.category
        source_class = item.source_class
        dataset_signal = item.dataset_signal
        official_signal = item.official_signal
        academic_signal = item.academic_signal
        dataset_names = list(item.dataset_names_mentioned)
        confidence_before = float(finding.confidence) if finding is not None else 0.5
        validation_score = confidence_before
        manual_validation_required = False

        if item.evidence_count <= 1:
            issues.append("single_supporting_evidence")
            validation_score -= 0.05
            manual_validation_required = True
        else:
            validation_score += 0.08

        if not item.snippets:
            issues.append("missing_snippet_evidence")
            validation_score -= 0.05
            manual_validation_required = True
        else:
            validation_score += 0.05

        if category == "official_data_portal" and not official_signal:
            issues.append("official_category_without_official_signal")
            validation_score -= 0.18
            manual_validation_required = True
            if not dataset_signal:
                category = "institutional_report"
                adjustments.append("downgraded_category_to_institutional_report")

        if category in {"academic_source", "repository"} and not academic_signal:
            issues.append("academic_category_without_academic_signal")
            validation_score -= 0.15
            manual_validation_required = True
            if category == "repository" and not dataset_signal:
                category = "secondary_reference"
                adjustments.append("downgraded_category_to_secondary_reference")

        if source_class == "analytical_data_source" and not dataset_signal:
            issues.append("analytical_source_without_dataset_signal")
            validation_score -= 0.22
            manual_validation_required = True
            source_class = "scientific_knowledge_source"
            adjustments.append("downgraded_source_class_to_scientific_knowledge_source")

        if category in {"journalistic_context", "secondary_reference"} and dataset_signal:
            issues.append("contextual_source_with_dataset_signal")
            validation_score -= 0.25
            manual_validation_required = True
            dataset_signal = False
            source_class = "scientific_knowledge_source"
            dataset_names = []
            adjustments.append("removed_dataset_signal_from_contextual_source")

        source_extractability = source.data_extractability if source is not None else "unknown"
        source_structured = source.structured_export_available if source is not None else None
        finding_structured = finding.structured_export_available if finding is not None else None
        if dataset_signal and source_extractability == "unknown" and source_structured is not True and finding_structured is not True:
            issues.append("weak_dataset_access_evidence")
            validation_score -= 0.12
            manual_validation_required = True

        validation_score = max(0.1, min(round(validation_score, 2), 0.99))
        validation_status = self._resolve_validation_status(
            validation_score=validation_score,
            manual_validation_required=manual_validation_required,
            adjustments=adjustments,
        )
        priority = self._downgraded_priority(item.priority, validation_score)
        source_type = self._source_type_from_category(category)
        source_roles = self._validated_roles(
            roles=(source.source_roles if source is not None else finding.source_roles if finding is not None else []),
            dataset_signal=dataset_signal,
            official_signal=official_signal,
            academic_signal=academic_signal,
        )
        recommended_pipeline_use = self._validated_pipeline_use(
            uses=(source.recommended_pipeline_use if source is not None else finding.recommended_pipeline_use if finding is not None else []),
            dataset_signal=dataset_signal,
            academic_signal=academic_signal,
        )
        rationale_suffix = self._validation_suffix(validation_status, issues, adjustments)
        note_suffix = self._validation_note_suffix(validation_status, issues, adjustments)

        validated_item = item.model_copy(
            update={
                "category": category,
                "source_class": source_class,
                "dataset_signal": dataset_signal,
                "priority": priority,
                "dataset_names_mentioned": dataset_names,
                "rationale": f"{item.rationale} {rationale_suffix}".strip(),
            }
        )

        validated_source = None
        if source is not None:
            validated_source = source.model_copy(
                update={
                    "source_type": source_type,
                    "source_class": source_class,
                    "source_roles": source_roles,
                    "recommended_pipeline_use": recommended_pipeline_use,
                    "priority": priority,
                    "methodological_note": f"{source.methodological_note} {note_suffix}".strip(),
                }
            )

        validated_finding = None
        if finding is not None:
            validated_finding = finding.model_copy(
                update={
                    "source_type": source_type,
                    "source_class": source_class,
                    "dataset_names_mentioned": dataset_names,
                    "source_roles": source_roles,
                    "recommended_pipeline_use": recommended_pipeline_use,
                    "confidence": validation_score,
                    "evidence_notes": f"{finding.evidence_notes} {note_suffix}".strip(),
                }
            )

        validation_record = SourceValidationRecord(
            source_id=item.source_id,
            title=item.title,
            validation_status=validation_status,
            validation_score=validation_score,
            manual_validation_required=manual_validation_required,
            evidence_count=item.evidence_count,
            issues=issues,
            adjustments=adjustments,
            category_before=item.category,
            category_after=category,
            source_class_before=item.source_class,
            source_class_after=source_class,
            dataset_signal_before=item.dataset_signal,
            dataset_signal_after=dataset_signal,
            official_signal_before=item.official_signal,
            official_signal_after=official_signal,
            confidence_before=confidence_before,
            confidence_after=validation_score,
        )

        return validated_item, validated_source, validated_finding, validation_record

    @classmethod
    def _downgraded_priority(cls, current_priority: str, validation_score: float) -> str:
        inferred = "high" if validation_score >= 0.75 else "medium" if validation_score >= 0.5 else "low"
        current_rank = cls.PRIORITY_ORDER.get(current_priority, 1)
        inferred_rank = cls.PRIORITY_ORDER[inferred]
        return current_priority if current_rank >= inferred_rank else inferred

    @staticmethod
    def _resolve_validation_status(
        *,
        validation_score: float,
        manual_validation_required: bool,
        adjustments: list[str],
    ) -> str:
        if adjustments:
            return "adjusted"
        if manual_validation_required and validation_score < 0.45:
            return "weak_evidence"
        if manual_validation_required:
            return "needs_manual_validation"
        return "validated"

    @staticmethod
    def _source_type_from_category(category: str) -> str:
        if category == "official_data_portal":
            return "primary_data_portal"
        if category in {"institutional_report", "civil_society_monitoring"}:
            return "institutional_documentation"
        if category in {"academic_source", "repository"}:
            return "academic_literature"
        return "web_result"

    @staticmethod
    def _validated_roles(
        *,
        roles: list[str],
        dataset_signal: bool,
        official_signal: bool,
        academic_signal: bool,
    ) -> list[str]:
        filtered: list[str] = []
        for role in roles:
            if role == "data_provider" and not dataset_signal:
                continue
            if role == "institutional_context" and not official_signal:
                continue
            if role == "scientific_evidence" and not academic_signal:
                continue
            if role not in filtered:
                filtered.append(role)
        if not filtered:
            filtered.append("context_reference")
        return filtered

    @staticmethod
    def _validated_pipeline_use(
        *,
        uses: list[str],
        dataset_signal: bool,
        academic_signal: bool,
    ) -> list[str]:
        filtered: list[str] = []
        for item in uses:
            if item in {"dataset_discovery_from_source", "direct_analytics_ingestion"} and not dataset_signal:
                continue
            if item in {"dataset_discovery_from_citations", "methodological_grounding"} and not academic_signal:
                continue
            if item not in filtered:
                filtered.append(item)
        if not filtered:
            filtered.append("context_reference")
        return filtered

    @staticmethod
    def _validation_suffix(validation_status: str, issues: list[str], adjustments: list[str]) -> str:
        parts = [f"validation_status={validation_status}"]
        if issues:
            parts.append(f"issues={','.join(issues)}")
        if adjustments:
            parts.append(f"adjustments={','.join(adjustments)}")
        return f"[validation {'; '.join(parts)}]"

    @staticmethod
    def _validation_note_suffix(validation_status: str, issues: list[str], adjustments: list[str]) -> str:
        fragments = [f"Validation status: {validation_status}."]
        if issues:
            fragments.append(f"Issues: {', '.join(issues)}.")
        if adjustments:
            fragments.append(f"Adjustments: {', '.join(adjustments)}.")
        return " ".join(fragments)
