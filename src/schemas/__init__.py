"""Modelos de dados e contratos do pipeline."""

from src.schemas.records import (
    CollectionGuide,
    DatasetCandidate,
    DatasetRecord,
    EnrichedDataset,
    FilteredSource,
    IntelligenceSourceRecord,
    PerplexityLinkRecord,
    PerplexityResearchContextRecord,
    PerplexityResearchTrackRecord,
    PerplexitySearchQueryRecord,
    PerplexitySearchSessionRecord,
    ResearchSourceRecord,
    SourceValidationRecord,
    WebResearchResultRecord,
)
from src.schemas.settings import PipelineSettings

__all__ = [
    "CollectionGuide",
    "DatasetCandidate",
    "DatasetRecord",
    "EnrichedDataset",
    "FilteredSource",
    "IntelligenceSourceRecord",
    "PerplexityLinkRecord",
    "PerplexityResearchContextRecord",
    "PerplexityResearchTrackRecord",
    "PerplexitySearchQueryRecord",
    "PerplexitySearchSessionRecord",
    "PipelineSettings",
    "ResearchSourceRecord",
    "SourceValidationRecord",
    "WebResearchResultRecord",
]
