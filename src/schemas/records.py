"""Schemas principais do pipeline multiagente."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DatasetRecord(BaseModel):
    """Representa um dataset identificado e normalizado."""

    dataset_id: str
    title: str
    description: str
    source_id: str
    source_name: str
    source_url: str
    source_inspiration_note: str = "Mock inspirado em fonte plausível; não consultado em tempo real."
    dataset_kind: str = "environmental"
    region: str = "São Paulo -> Três Lagoas"
    thematic_axis: str = "impactos humanos em rios e reservatórios"
    temporal_coverage: str = "não informado"
    spatial_coverage: str = "não informado"
    update_frequency: str = "não informado"
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    relevance_rationale: str = ""
    priority: str = Field(default="medium")
    priority_reason: str = ""
    access_level: str = "unknown"
    access_notes: str = ""
    methodological_notes: list[str] = Field(default_factory=list)
    evidence_origin: list[str] = Field(default_factory=list)
    formats: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    discovered_at: datetime = Field(default_factory=datetime.utcnow)


class ResearchSourceRecord(BaseModel):
    """Representa uma fonte usada na descoberta de datasets."""

    source_id: str
    name: str
    base_url: str
    source_type: str
    citation: str
    query: str
    priority: str = "medium"
    methodological_note: str = "Fonte incluída como inspiração estrutural para dry-run."
    discovered_at: datetime = Field(default_factory=datetime.utcnow)


class PipelineRunMetadata(BaseModel):
    """Metadados e rastreabilidade de uma execução de pipeline."""

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


class CatalogExportRecord(BaseModel):
    """Estrutura consolidada para exportação de catálogo."""

    run_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    dataset_count: int
    datasets: list[DatasetRecord]
    sources: list[ResearchSourceRecord]
