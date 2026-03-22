from unittest.mock import MagicMock, patch

from src.connectors.perplexity_api import PerplexityAPICollector, PerplexityAPIError
from src.schemas.records import PerplexitySearchQueryRecord


def _make_query(query_id: str = "pplx-q-01") -> PerplexitySearchQueryRecord:
    return PerplexitySearchQueryRecord(
        query_id=query_id,
        base_query="rio tiete",
        query_text="Quais datasets de qualidade da agua existem para o Tiete?",
        search_profile="monitoring_sources",
        target_intent="dataset_discovery",
        research_track="n3_qualidade_agua",
        chat_label="chat-qualidade",
        research_question="Quais datasets de qualidade da agua existem?",
        task_prompt="Busque dados de qualidade da agua.",
        priority="high",
    )


def test_collect_returns_empty_for_empty_plan() -> None:
    collector = PerplexityAPICollector(api_key="test-key")
    assert collector.collect([]) == []


def test_collect_ok_session_on_success() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "title": "Portal Hidroweb",
                "url": "https://www.snirh.gov.br/hidroweb",
                "snippet": "Series historicas hidrologicas.",
                "date": "2024-01-01",
            },
            {
                "title": "QUALAR CETESB",
                "url": "https://qualar.cetesb.sp.gov.br",
                "snippet": "Dados de qualidade da agua em SP.",
                "date": "2024-01-01",
            },
        ]
    }

    collector = PerplexityAPICollector(api_key="test-key", max_results=20)
    with patch("src.connectors.perplexity_api.httpx.post", return_value=mock_response):
        sessions = collector.collect([_make_query()])

    assert len(sessions) == 1
    s = sessions[0]
    assert s.collection_status == "ok"
    assert len(s.links) == 2
    assert s.links[0].domain == "snirh.gov.br"
    assert s.links[0].title == "Portal Hidroweb"
    assert s.links[0].snippet == "Series historicas hidrologicas."
    assert s.visible_source_count == 2


def test_collect_error_session_on_api_failure() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.text = "Too Many Requests"

    collector = PerplexityAPICollector(api_key="test-key")
    with patch("src.connectors.perplexity_api.httpx.post", return_value=mock_response):
        sessions = collector.collect([_make_query()])

    assert len(sessions) == 1
    s = sessions[0]
    assert s.collection_status == "error"
    assert any("api_error" in b for b in s.blockers)


def test_perplexity_api_error_is_runtime_error() -> None:
    assert isinstance(PerplexityAPIError("teste"), RuntimeError)
