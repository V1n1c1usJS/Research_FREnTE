"""Conectores para fontes externas."""

from src.connectors.llm import (
    GroqResponsesConnector,
    LLMConnector,
    LLMConnectorError,
    OpenAIResponsesConnector,
)
from src.connectors.web_research import (
    BingWebResearchConnector,
    DuckDuckGoWebResearchConnector,
    MockWebResearchConnector,
    PreparedWebResearchConnector,
    WebResearchConnector,
)

__all__ = [
    "LLMConnector",
    "LLMConnectorError",
    "GroqResponsesConnector",
    "OpenAIResponsesConnector",
    "WebResearchConnector",
    "MockWebResearchConnector",
    "BingWebResearchConnector",
    "DuckDuckGoWebResearchConnector",
    "PreparedWebResearchConnector",
]
