"""Modelos de dados e contratos do pipeline."""

from src.schemas.records import (
    DatasetCandidate,
    DatasetRecord,
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
    "DatasetCandidate",
    "DatasetRecord",
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
