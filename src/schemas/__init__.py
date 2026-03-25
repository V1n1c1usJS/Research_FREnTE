"""Modelos de dados e contratos do pipeline."""

from src.schemas.records import (
    CollectionGuide,
    CollectionArtifactRecord,
    DatasetCandidate,
    DatasetRecord,
    EnrichedDataset,
    FilteredSource,
    IntelligenceSourceRecord,
    OperationalCollectionRunRecord,
    OperationalCollectionTargetRecord,
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
    "CollectionArtifactRecord",
    "DatasetCandidate",
    "DatasetRecord",
    "EnrichedDataset",
    "FilteredSource",
    "IntelligenceSourceRecord",
    "OperationalCollectionRunRecord",
    "OperationalCollectionTargetRecord",
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
