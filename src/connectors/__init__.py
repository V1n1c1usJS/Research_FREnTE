"""Conectores usados pelo fluxo Perplexity-first."""

from src.connectors.firecrawl_collector import FirecrawlCollector, build_collection_prompt
from src.connectors.llm import LLMConnector, LLMConnectorError, OpenAIResponsesConnector
from src.connectors.perplexity_api import PerplexityAPICollector, PerplexityAPIError

__all__ = [
    "FirecrawlCollector",
    "LLMConnector",
    "LLMConnectorError",
    "OpenAIResponsesConnector",
    "PerplexityAPICollector",
    "PerplexityAPIError",
    "build_collection_prompt",
]
