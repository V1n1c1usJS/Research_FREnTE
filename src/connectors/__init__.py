"""Conectores usados pelo fluxo Perplexity-first."""

from src.connectors.firecrawl_collector import FirecrawlCollector, build_collection_prompt
from src.connectors.llm import LLMConnector, LLMConnectorError, OpenAIResponsesConnector
from src.connectors.operational_dataset_collector import (
    AVAILABLE_OPERATIONAL_TARGETS,
    DEFAULT_TIETE_BBOX,
    OperationalDatasetCollector,
)
from src.connectors.perplexity_api import PerplexityAPICollector, PerplexityAPIError

__all__ = [
    "AVAILABLE_OPERATIONAL_TARGETS",
    "DEFAULT_TIETE_BBOX",
    "FirecrawlCollector",
    "LLMConnector",
    "LLMConnectorError",
    "OpenAIResponsesConnector",
    "OperationalDatasetCollector",
    "PerplexityAPICollector",
    "PerplexityAPIError",
    "build_collection_prompt",
]
