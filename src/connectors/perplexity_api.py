"""Coleta de pesquisas via Search API oficial do Perplexity."""

from __future__ import annotations

from urllib.parse import urlparse

import httpx

from src.schemas.records import (
    PerplexityLinkRecord,
    PerplexitySearchQueryRecord,
    PerplexitySearchSessionRecord,
)

PERPLEXITY_SEARCH_URL = "https://api.perplexity.ai/search"


class PerplexityAPIError(RuntimeError):
    """Erro operacional ao chamar a API do Perplexity."""


class PerplexityAPICollector:
    """Executa buscas no Perplexity via Search API oficial."""

    def __init__(
        self,
        *,
        api_key: str,
        max_results: int = 20,
        timeout_seconds: float = 60.0,
    ) -> None:
        self.api_key = api_key
        self.max_results = max_results
        self.timeout_seconds = timeout_seconds

    def collect(self, query_plan: list[PerplexitySearchQueryRecord]) -> list[PerplexitySearchSessionRecord]:
        if not query_plan:
            return []
        sessions: list[PerplexitySearchSessionRecord] = []
        for query in query_plan:
            try:
                results = self._call_api(query.query_text)
                links = [
                    PerplexityLinkRecord(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        domain=_extract_domain(item.get("url", "")),
                        snippet=item.get("snippet", ""),
                    )
                    for item in results
                    if str(item.get("url", "")).startswith("http")
                ]
                answer_text = "\n\n".join(
                    f"{item.get('title', '')}: {item.get('snippet', '')}"
                    for item in results
                    if item.get("snippet")
                )
                sessions.append(
                    PerplexitySearchSessionRecord(
                        query_id=query.query_id,
                        query_text=query.query_text,
                        search_profile=query.search_profile,
                        target_intent=query.target_intent,
                        research_track=query.research_track,
                        chat_label=query.chat_label,
                        research_question=query.research_question,
                        collection_status="ok",
                        collection_method="search_api",
                        request_endpoint=PERPLEXITY_SEARCH_URL,
                        answer_text=answer_text,
                        visible_source_count=len(links),
                        links=links,
                        blockers=[],
                        notes=[f"max_results:{self.max_results}", "source:perplexity_search_api"],
                    )
                )
            except Exception as exc:  # noqa: BLE001
                sessions.append(
                    PerplexitySearchSessionRecord(
                        query_id=query.query_id,
                        query_text=query.query_text,
                        search_profile=query.search_profile,
                        target_intent=query.target_intent,
                        research_track=query.research_track,
                        chat_label=query.chat_label,
                        research_question=query.research_question,
                        collection_status="error",
                        collection_method="search_api",
                        request_endpoint=PERPLEXITY_SEARCH_URL,
                        answer_text="",
                        visible_source_count=0,
                        links=[],
                        blockers=[f"api_error:{type(exc).__name__}"],
                        notes=[str(exc)[:300]],
                    )
                )
        return sessions

    def _call_api(self, query_text: str) -> list[dict[str, object]]:
        response = httpx.post(
            PERPLEXITY_SEARCH_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "query": query_text,
                "max_results": self.max_results,
            },
            timeout=self.timeout_seconds,
        )
        if response.status_code != 200:
            raise PerplexityAPIError(f"HTTP {response.status_code}: {response.text[:300]}")
        data = response.json()
        return data.get("results", [])


def _extract_domain(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").replace("www.", "")
    except Exception:
        return ""


__all__ = ["PerplexityAPICollector", "PerplexityAPIError"]
