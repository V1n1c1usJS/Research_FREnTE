from typing import Any

from src.agents.research_scout_agent import ResearchScoutAgent
from src.schemas.records import WebResearchResultRecord
from src.schemas.settings import PipelineSettings


class EmptyConnector:
    def search(self, query: str, search_terms: list[str], limit: int = 20) -> list[WebResearchResultRecord]:
        return []


class ErrorConnector:
    def search(self, query: str, search_terms: list[str], limit: int = 20) -> list[WebResearchResultRecord]:
        raise TimeoutError("simulated timeout")


def _context() -> dict[str, Any]:
    return {
        "settings": PipelineSettings(
            query="impactos humanos no rio tietê",
            limit=3,
            dry_run=False,
            web_research_mode="real",
            web_timeout_seconds=2.0,
        )
    }


def test_research_scout_real_mode_fallback_when_empty() -> None:
    agent = ResearchScoutAgent(connector=EmptyConnector(), web_research_mode="real", timeout_seconds=2.0)
    result = agent.run(_context())

    assert result["web_research_results"]
    assert result["web_research_meta"]["connector_mode_used"] == "mock-fallback"
    assert result["web_research_meta"]["fallback_reason"] == "empty_real_results"


def test_research_scout_real_mode_fallback_on_error() -> None:
    agent = ResearchScoutAgent(connector=ErrorConnector(), web_research_mode="real", timeout_seconds=2.0)
    result = agent.run(_context())

    assert result["web_research_results"]
    assert result["web_research_meta"]["connector_mode_used"] == "mock-fallback"
    assert result["web_research_meta"]["fallback_reason"].startswith("connector_error")
