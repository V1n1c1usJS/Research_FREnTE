"""Schemas principais do fluxo Perplexity-first."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DatasetRecord(BaseModel):
    """Representa um dataset ou ativo metodologico normalizado."""

    dataset_id: str
    title: str
    aliases: list[str] = Field(default_factory=list)
    canonical_url: str = ""
    entity_type: str = "dataset"
    description: str
    source_id: str
    source_name: str
    source_url: str
    source_class: str = "analytical_data_source"
    source_roles: list[str] = Field(default_factory=list)
    data_extractability: str = "unknown"
    historical_records_available: bool | None = None
    structured_export_available: bool | None = None
    scientific_value: str = "medium"
    recommended_pipeline_use: list[str] = Field(default_factory=list)
    organization_normalized: str = ""
    source_inspiration_note: str = ""
    dataset_kind: str = "environmental"
    region: str = ""
    thematic_axis: str = ""
    temporal_coverage: str = "not specified"
    spatial_coverage: str = "not specified"
    update_frequency: str = "not specified"
    variables_normalized: list[str] = Field(default_factory=list)
    themes_normalized: list[str] = Field(default_factory=list)
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    relevance_rationale: str = ""
    relevance_breakdown: dict[str, object] = Field(default_factory=dict)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    relevance_hint: float = Field(default=0.0, ge=0.0, le=1.0)
    priority: str = "medium"
    priority_reason: str = ""
    access_level: str = "unknown"
    access_notes: str = ""
    access_links: list[str] = Field(default_factory=list)
    documentation_links: list[str] = Field(default_factory=list)
    requires_auth: bool | None = None
    extraction_observations: list[str] = Field(default_factory=list)
    methodological_notes: list[str] = Field(default_factory=list)
    evidence_origin: list[str] = Field(default_factory=list)
    provenance: list[dict[str, str]] = Field(default_factory=list)
    formats: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    discovered_at: datetime = Field(default_factory=_utcnow)


class DatasetCandidate(BaseModel):
    """Candidato consolidado antes da normalizacao."""

    candidate_id: str
    dataset_name: str
    aliases: list[str] = Field(default_factory=list)
    canonical_url: str = ""
    dataset_type: str = "dataset"
    candidate_role: str = "dataset"
    description: str
    variables_mentioned: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    source_mentions: list[dict[str, str]] = Field(default_factory=list)
    mention_origins: list[str] = Field(default_factory=list)
    evidence_notes: list[str] = Field(default_factory=list)
    supporting_queries: list[str] = Field(default_factory=list)
    geographic_scope: str = "not specified"
    temporal_coverage: str = "not specified"
    update_frequency: str = "not specified"
    formats: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    evidence_count: int = 0
    accessibility: str = "institutional_reference"
    verifiability_status: str = "needs_manual_validation"
    confidence_hint: float = Field(default=0.6, ge=0.0, le=1.0)
    priority_hint: str = "medium"


class ResearchSourceRecord(BaseModel):
    """Representa uma fonte consolidada a partir da coleta."""

    source_id: str
    name: str
    base_url: str
    source_type: str
    citation: str
    query: str
    source_class: str = "scientific_knowledge_source"
    source_roles: list[str] = Field(default_factory=list)
    data_extractability: str = "unknown"
    historical_records_available: bool | None = None
    structured_export_available: bool | None = None
    scientific_value: str = "medium"
    recommended_pipeline_use: list[str] = Field(default_factory=list)
    priority: str = "medium"
    methodological_note: str = ""
    discovered_at: datetime = Field(default_factory=_utcnow)


class WebResearchResultRecord(BaseModel):
    """Registro auditavel para reuso pelos agentes seguintes."""

    source_id: str
    source_title: str
    source_type: str
    source_url: str
    publisher_or_org: str
    dataset_names_mentioned: list[str] = Field(default_factory=list)
    variables_mentioned: list[str] = Field(default_factory=list)
    geographic_scope: str
    relevance_to_100k: str
    evidence_notes: str
    search_terms_extracted: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    relevance_hint: float = Field(default=0.0, ge=0.0, le=1.0)
    source_class: str = "scientific_knowledge_source"
    source_roles: list[str] = Field(default_factory=list)
    data_extractability: str = "unknown"
    historical_records_available: bool | None = None
    structured_export_available: bool | None = None
    scientific_value: str = "medium"
    recommended_pipeline_use: list[str] = Field(default_factory=list)


class PerplexityResearchTrackRecord(BaseModel):
    """Configuracao de uma frente tematica de busca no Perplexity."""

    research_track: str
    chat_label: str
    search_profile: str = "general_environmental_search"
    target_intent: str = "dataset_discovery"
    research_question: str
    task_prompt: str
    priority: str = "medium"


class PerplexitySearchQueryRecord(BaseModel):
    """Consulta planejada para coleta via Perplexity."""

    query_id: str
    base_query: str
    query_text: str
    search_profile: str
    target_intent: str
    research_track: str = ""
    chat_label: str = ""
    research_question: str = ""
    task_prompt: str = ""
    priority: str = "medium"


class PerplexityResearchContextRecord(BaseModel):
    """Contexto mestre da pesquisa."""

    context_id: str
    article_goal: str
    geographic_scope: list[str] = Field(default_factory=list)
    thematic_axes: list[str] = Field(default_factory=list)
    preferred_sources: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class PerplexityLinkRecord(BaseModel):
    """Link visivel coletado em uma resposta do Perplexity."""

    title: str = ""
    url: str
    domain: str = ""
    snippet: str = ""


class PerplexitySearchSessionRecord(BaseModel):
    """Resposta bruta coletada via Playwright no Perplexity."""

    query_id: str
    query_text: str
    search_profile: str
    target_intent: str
    research_track: str = ""
    chat_label: str = ""
    research_question: str = ""
    collection_status: str = "ok"
    validated_via_playwright: bool = True
    page_url: str = ""
    preferred_model: str | None = None
    selected_model: str | None = None
    model_selection_blocked: bool = False
    model_selection_blocker: str | None = None
    answer_text: str = ""
    visible_source_count: int = 0
    links: list[PerplexityLinkRecord] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    collected_at: datetime = Field(default_factory=_utcnow)


class IntelligenceSourceRecord(BaseModel):
    """Fonte consolidada a partir das respostas do Perplexity."""

    source_id: str
    title: str
    url: str
    domain: str
    category: str
    source_class: str
    target_intent: str
    article_value: str = "medium"
    dataset_signal: bool = False
    academic_signal: bool = False
    official_signal: bool = False
    priority: str = "medium"
    search_profiles: list[str] = Field(default_factory=list)
    research_tracks: list[str] = Field(default_factory=list)
    supporting_query_ids: list[str] = Field(default_factory=list)
    evidence_count: int = 0
    snippets: list[str] = Field(default_factory=list)
    dataset_names_mentioned: list[str] = Field(default_factory=list)
    variables_mentioned: list[str] = Field(default_factory=list)
    rationale: str = ""


class SourceValidationRecord(BaseModel):
    """Registro auditavel da validacao aplicada a uma fonte antes do discovery."""

    source_id: str
    title: str
    validation_status: str = "validated"
    validation_score: float = Field(default=0.5, ge=0.0, le=1.0)
    manual_validation_required: bool = False
    evidence_count: int = 0
    issues: list[str] = Field(default_factory=list)
    adjustments: list[str] = Field(default_factory=list)
    category_before: str = ""
    category_after: str = ""
    source_class_before: str = ""
    source_class_after: str = ""
    dataset_signal_before: bool = False
    dataset_signal_after: bool = False
    official_signal_before: bool = False
    official_signal_after: bool = False
    confidence_before: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence_after: float = Field(default=0.5, ge=0.0, le=1.0)
