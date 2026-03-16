"""Conectores para fontes externas."""

from src.connectors.web_research import (
    BingWebResearchConnector,
    DuckDuckGoWebResearchConnector,
    MockWebResearchConnector,
    PreparedWebResearchConnector,
    WebResearchConnector,
)

__all__ = [
    "WebResearchConnector",
    "MockWebResearchConnector",
    "BingWebResearchConnector",
    "DuckDuckGoWebResearchConnector",
    "PreparedWebResearchConnector",
]
