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


class MixedConnector:
    def search(self, query: str, search_terms: list[str], limit: int = 20) -> list[WebResearchResultRecord]:
        return [
            WebResearchResultRecord(
                source_id="ir-1",
                source_title="Rio (2011) - IMDb",
                source_type="web_result",
                source_url="https://www.imdb.com/title/tt1436562/",
                publisher_or_org="IMDB",
                dataset_names_mentioned=[],
                variables_mentioned=[],
                geographic_scope="global",
                relevance_to_100k="none",
                evidence_notes="movie page",
                search_terms_extracted=[query],
                citations=["https://www.imdb.com/title/tt1436562/"],
                confidence=0.4,
            ),
            WebResearchResultRecord(
                source_id="ir-2",
                source_title="Cafe Rio: Mexican Grill",
                source_type="web_result",
                source_url="https://www.caferio.com/menu",
                publisher_or_org="Cafe Rio",
                dataset_names_mentioned=[],
                variables_mentioned=[],
                geographic_scope="global",
                relevance_to_100k="none",
                evidence_notes="restaurant menu",
                search_terms_extracted=[query],
                citations=["https://www.caferio.com/menu"],
                confidence=0.3,
            ),
            WebResearchResultRecord(
                source_id="ok-1",
                source_title="Hidroweb - SNIRH",
                source_type="primary_data_portal",
                source_url="https://www.snirh.gov.br/hidroweb",
                publisher_or_org="ANA",
                dataset_names_mentioned=["Séries históricas hidrológicas"],
                variables_mentioned=["vazão", "nível"],
                geographic_scope="Brasil",
                relevance_to_100k="alto",
                evidence_notes="portal hidrologia bacia do tietê dataset",
                search_terms_extracted=[query],
                citations=["https://www.snirh.gov.br/hidroweb"],
                confidence=0.9,
            ),
        ]


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


def test_research_scout_filters_irrelevant_results_regression() -> None:
    agent = ResearchScoutAgent(connector=MixedConnector(), web_research_mode="real", timeout_seconds=2.0)
    result = agent.run(_context())

    urls = [item.source_url for item in result["web_research_results"]]
    assert "https://www.imdb.com/title/tt1436562/" not in urls
    assert "https://www.caferio.com/menu" not in urls
    assert "https://www.snirh.gov.br/hidroweb" in urls
    assert result["web_research_meta"]["discarded_irrelevant_count"] >= 2
    assert result["web_research_results"][0].relevance_hint > 0.5
