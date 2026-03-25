"""Schemas principais do fluxo Perplexity-first."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Mapeamentos de herança de trilha — usados pelo EnrichAgent (sem LLM)
# ---------------------------------------------------------------------------

TRACK_TO_LEVEL: dict[str, str] = {
    "n1_": "macro",
    "n2_": "meso",
    "n3_": "bridge",
    "n4_": "micro",
}

TRACK_TO_AXIS: dict[str, str] = {
    "n1_bacia_geomorfologia": "delimitação e geomorfologia",
    "n1_uso_cobertura_solo": "uso e cobertura do solo",
    "n1_clima_hidrologia": "clima e hidrologia",
    "n2_saneamento_esgoto": "saneamento e esgoto",
    "n2_desmatamento_queimadas": "desmatamento e queimadas",
    "n2_agro_residuos_ocupacao": "agropecuária, resíduos e ocupação",
    "n3_qualidade_agua_reservatorios": "qualidade da água nos reservatórios",
    "n3_operacao_reservatorios": "operação dos reservatórios",
    "n3_batimetria_morfometria": "batimetria e morfometria",
    "n4_materia_organica_cdom": "matéria orgânica e CDOM",
    "n4_sensoriamento_remoto_agua": "sensoriamento remoto da qualidade da água",
    "n4_series_temporais_tendencias": "séries temporais e tendências",
}

INTENT_TO_CATEGORY: dict[str, str] = {
    "dataset_discovery": "dataset",
    "academic_knowledge": "academic",
    "contextual_intelligence": "contextual",
}

DOMAIN_CATEGORY_OVERRIDES: dict[str, str] = {
    "cetesb.sp.gov.br": "official_portal",
    "qualar.cetesb.sp.gov.br": "official_portal",
    "snirh.gov.br": "official_portal",
    "hidroweb.ana.gov.br": "official_portal",
    "ana.gov.br": "official_portal",
    "ibge.gov.br": "official_portal",
    "sidra.ibge.gov.br": "official_portal",
    "ons.org.br": "official_portal",
    "inpe.br": "official_portal",
    "terrabrasilis.dpi.inpe.br": "official_portal",
    "mapbiomas.org": "official_portal",
    "scielo.br": "academic",
    "doi.org": "academic",
}


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
    research_tracks: list[str] = Field(default_factory=list)
    search_profiles: list[str] = Field(default_factory=list)
    target_intents: list[str] = Field(default_factory=list)
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
    research_tracks: list[str] = Field(default_factory=list)
    search_profiles: list[str] = Field(default_factory=list)
    target_intents: list[str] = Field(default_factory=list)
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
    search_profiles: list[str] = Field(default_factory=list)
    research_tracks: list[str] = Field(default_factory=list)
    target_intent: str = ""
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
    search_profiles: list[str] = Field(default_factory=list)
    research_tracks: list[str] = Field(default_factory=list)
    target_intent: str = ""
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
    """Resposta bruta coletada via Perplexity Search API."""

    query_id: str
    query_text: str
    search_profile: str
    target_intent: str
    research_track: str = ""
    chat_label: str = ""
    research_question: str = ""
    collection_status: str = "ok"
    collection_method: str = "search_api"
    request_endpoint: str = ""
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


# ---------------------------------------------------------------------------
# Schemas do pipeline refatorado (4 etapas)
# ---------------------------------------------------------------------------


class CollectionGuide(BaseModel):
    """Guia de coleta extraído automaticamente de um portal via Firecrawl."""

    steps: list[str] = Field(
        default_factory=list,
        description="Passos numerados para coletar os dados no portal.",
    )
    filters_available: dict[str, str] = Field(
        default_factory=dict,
        description="Filtros identificados. Chave: nome. Valor: opções relevantes para o Tietê.",
    )
    download_format: str = Field(
        default="unknown",
        description="Formato do arquivo de download. Ex: 'CSV separador ;', 'Shapefile ZIP'.",
    )
    estimated_effort: Literal["minutes", "hours", "days", "requires_contact"] = Field(
        default="hours",
        description="Esforço estimado para coletar.",
    )
    caveats: list[str] = Field(
        default_factory=list,
        description="Alertas e limitações do portal.",
    )
    requires_login: bool = Field(
        default=False,
        description="Se o portal exige cadastro ou login.",
    )
    direct_download_urls: list[str] = Field(
        default_factory=list,
        description="URLs diretas de arquivos encontrados na página.",
    )


class FilteredSource(BaseModel):
    """Fonte filtrada e validada heuristicamente a partir da coleta bruta."""

    url: str
    title: str
    snippet: str
    source_domain: str

    # herdado do track que gerou este resultado
    track_origin: str
    track_priority: str
    track_intent: str

    needs_review: bool = False
    filter_notes: list[str] = Field(default_factory=list)


class EnrichedDataset(FilteredSource):
    """Fonte enriquecida com metadados herdados do track e extraídos pela LLM."""

    # Fase A — herdado do track (determinístico)
    hierarchy_level: Literal["macro", "meso", "bridge", "micro"] = "macro"
    thematic_axis: str = ""
    source_category: str = "contextual"  # official_portal | academic | dataset | contextual

    # Fase B — extraído pela LLM (ou heurística de fallback)
    dataset_name: str = ""
    dataset_description: str = ""
    data_format: Literal[
        "structured",
        "semi_structured",
        "pdf_report",
        "academic_paper",
        "geospatial_platform",
        "unknown",
    ] = "unknown"
    temporal_coverage: str | None = None
    spatial_coverage: str | None = None
    key_parameters: list[str] = Field(default_factory=list)
    collection_guide: CollectionGuide | None = None

    enrichment_method: Literal["llm", "heuristic"] = "heuristic"
    llm_model: str | None = None


class RankedDataset(EnrichedDataset):
    """Dataset enriquecido com rank de acesso e tipo de acesso classificado."""

    rank: int = 0
    access_type: Literal[
        "direct_download",
        "api_access",
        "web_portal",
        "geospatial_platform",
        "pdf_extraction",
        "restricted",
        "unknown",
    ] = "unknown"
    access_notes: str = ""


class CollectionArtifactRecord(BaseModel):
    """Arquivo ou resposta persistida durante uma coleta operacional."""

    artifact_id: str
    target_id: str
    source_name: str
    status: str = "collected"
    relative_path: str
    download_url: str = ""
    media_type: str = ""
    file_format: str = ""
    content_length: int | None = None
    checksum_sha256: str = ""
    notes: list[str] = Field(default_factory=list)
    collected_at: datetime = Field(default_factory=_utcnow)


class OperationalCollectionTargetRecord(BaseModel):
    """Resumo auditavel da coleta de uma fonte operacional."""

    target_id: str
    source_name: str
    dataset_name: str
    collection_status: Literal["collected", "partial", "blocked", "error", "not_attempted"] = "not_attempted"
    access_type: str = "unknown"
    collection_method: str = "http_download"
    requires_auth: bool = False
    year_start: int | None = None
    year_end: int | None = None
    bbox: str | None = None
    provenance_urls: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    join_keys: list[str] = Field(default_factory=list)
    staging_outputs: list[str] = Field(default_factory=list)
    analytic_outputs: list[str] = Field(default_factory=list)
    raw_artifacts: list[CollectionArtifactRecord] = Field(default_factory=list)


class OperationalCollectionRunRecord(BaseModel):
    """Manifesto consolidado de uma rodada de coleta operacional."""

    run_id: str
    pipeline_name: str = "operational_dataset_collection"
    generated_at: datetime = Field(default_factory=_utcnow)
    target_ids: list[str] = Field(default_factory=list)
    target_count: int = 0
    collected_count: int = 0
    partial_count: int = 0
    blocked_count: int = 0
    error_count: int = 0
    targets: list[OperationalCollectionTargetRecord] = Field(default_factory=list)
