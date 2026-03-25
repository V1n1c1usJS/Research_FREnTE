"""Modelos de dados e contratos do pipeline."""

from src.schemas.records import (
    CollectionGuide,
    CollectionArtifactRecord,
    EnrichedDataset,
    FilteredSource,
    OperationalCollectionRunRecord,
    OperationalCollectionTargetRecord,
    PerplexityLinkRecord,
    PerplexityResearchContextRecord,
    PerplexityResearchTrackRecord,
    PerplexitySearchQueryRecord,
    PerplexitySearchSessionRecord,
    RankedDataset,
)
from src.schemas.settings import PipelineSettings

__all__ = [
    "CollectionGuide",
    "CollectionArtifactRecord",
    "EnrichedDataset",
    "FilteredSource",
    "OperationalCollectionRunRecord",
    "OperationalCollectionTargetRecord",
    "PerplexityLinkRecord",
    "PerplexityResearchContextRecord",
    "PerplexityResearchTrackRecord",
    "PerplexitySearchQueryRecord",
    "PerplexitySearchSessionRecord",
    "PipelineSettings",
    "RankedDataset",
]
