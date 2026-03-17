"""Schemas principais do pipeline multiagente."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DatasetRecord(BaseModel):
    """Representa um dataset identificado e normalizado."""

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
    source_inspiration_note: str = "Mock inspirado em fonte plausivel; nao consultado em tempo real."
    dataset_kind: str = "environmental"
    region: str = "Sao Paulo -> Tres Lagoas"
    thematic_axis: str = "impactos humanos em rios e reservatorios"
    temporal_coverage: str = "nao informado"
    spatial_coverage: str = "nao informado"
    update_frequency: str = "nao informado"
    variables_normalized: list[str] = Field(default_factory=list)
    themes_normalized: list[str] = Field(default_factory=list)
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    relevance_rationale: str = ""
    relevance_breakdown: dict[str, object] = Field(default_factory=dict)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    relevance_hint: float = Field(default=0.0, ge=0.0, le=1.0)
    priority: str = Field(default="medium")
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
    """Candidato consolidado de dataset para normalizacao posterior."""

    candidate_id: str
    dataset_name: str
    aliases: list[str] = Field(default_factory=list)
    canonical_url: str = ""
    dataset_type: str = "dataset"
    candidate_role: str = Field(default="dataset")
    description: str
    variables_mentioned: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    source_mentions: list[dict[str, str]] = Field(default_factory=list)
    mention_origins: list[str] = Field(default_factory=list)
    evidence_notes: list[str] = Field(default_factory=list)
    supporting_queries: list[str] = Field(default_factory=list)
    geographic_scope: str = "Sao Paulo -> Tres Lagoas"
    temporal_coverage: str = "nao informado"
    update_frequency: str = "nao informado"
    formats: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    evidence_count: int = 0
    accessibility: str = "direct_access"
    verifiability_status: str = "needs_manual_validation"
    confidence_hint: float = Field(default=0.6, ge=0.0, le=1.0)
    priority_hint: str = "medium"


class ResearchSourceRecord(BaseModel):
    """Representa uma fonte usada na descoberta de datasets."""

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
    methodological_note: str = "Fonte incluida como inspiracao estrutural para dry-run."
    discovered_at: datetime = Field(default_factory=_utcnow)


class WebResearchResultRecord(BaseModel):
    """Registro auditavel de achado de pesquisa aberta na web."""

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


class QueryExpansionRecord(BaseModel):
    """Representa expansao auditavel de um termo de busca."""

    base_term: str
    synonyms: list[str] = Field(default_factory=list)
    technical_terms: list[str] = Field(default_factory=list)
    variable_aliases: list[str] = Field(default_factory=list)
    methodological_expressions: list[str] = Field(default_factory=list)
    generated_queries: list[str] = Field(default_factory=list)
    evidence_source_ids: list[str] = Field(default_factory=list)


class PipelineRunMetadata(BaseModel):
    """Metadados e rastreabilidade de uma execucao de pipeline."""

    run_id: str
    mode: str
    query: str
    started_at: datetime
    finished_at: datetime | None = None
    status: str = "running"
    steps: list[str] = Field(default_factory=list)
    intermediate_files: list[str] = Field(default_factory=list)
    report_file: str | None = None
    export_file: str | None = None
    llm_mode_requested: str | None = None
    llm_provider_used: str | None = None
    llm_model_used: str | None = None
    llm_enabled_agents: list[str] = Field(default_factory=list)
    llm_setup_error: str | None = None


class CatalogExportRecord(BaseModel):
    """Estrutura consolidada para exportacao de catalogo."""

    run_id: str
    generated_at: datetime = Field(default_factory=_utcnow)
    dataset_count: int
    datasets: list[DatasetRecord]
    sources: list[ResearchSourceRecord]
