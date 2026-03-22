"""Coleta de pesquisas no Perplexity via Playwright CLI."""

from __future__ import annotations

from typing import Callable, Sequence

from src.connectors.perplexity_browser_session import (
    PerplexityBrowserSession,
    PlaywrightCLIError,
)
from src.schemas.records import (
    PerplexityLinkRecord,
    PerplexitySearchQueryRecord,
    PerplexitySearchSessionRecord,
)


class PerplexityPlaywrightCollector:
    """Executa buscas no Perplexity via navegador real controlado pelo Playwright CLI."""

    def __init__(
        self,
        *,
        preferred_model: str = "Sonar",
        timeout_seconds: float = 120.0,
        per_query_wait_ms: int = 7000,
        headed: bool = False,
        session_prefix: str = "rf-pplx",
        command_runner: Callable[[Sequence[str], float], str] | None = None,
    ) -> None:
        self.preferred_model = preferred_model
        self.timeout_seconds = timeout_seconds
        self.per_query_wait_ms = per_query_wait_ms
        self.headed = headed
        self.session_prefix = session_prefix
        self.command_runner = command_runner

    def collect(self, query_plan: list[PerplexitySearchQueryRecord]) -> list[PerplexitySearchSessionRecord]:
        if not query_plan:
            return []

        browser_session = PerplexityBrowserSession(
            preferred_model=self.preferred_model,
            timeout_seconds=self.timeout_seconds,
            per_query_wait_ms=self.per_query_wait_ms,
            headed=self.headed,
            session_prefix=self.session_prefix,
            command_runner=self.command_runner,
        )
        sessions: list[PerplexitySearchSessionRecord] = []

        try:
            browser_session.open()
            for query in query_plan:
                try:
                    payload = browser_session.collect_query(query.query_text)
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
                            validated_via_playwright=True,
                            browser_tab_index=payload.get("browser_tab_index"),
                            page_url=str(payload.get("page_url", "")),
                            preferred_model=str(payload.get("model_requested") or self.preferred_model),
                            selected_model=payload.get("model_selected"),
                            model_selection_blocked=bool(payload.get("model_selection_blocked", False)),
                            model_selection_blocker=payload.get("model_selection_blocker"),
                            answer_text=str(payload.get("answer_text", "")),
                            visible_source_count=int(payload.get("visible_source_count", 0) or 0),
                            links=[
                                PerplexityLinkRecord(
                                    title=str(item.get("title", "")),
                                    url=str(item.get("url", "")),
                                    domain=str(item.get("domain", "")),
                                    snippet=str(item.get("snippet", "")),
                                )
                                for item in payload.get("links", [])
                                if str(item.get("url", "")).startswith("http")
                            ],
                            blockers=[str(item) for item in payload.get("blockers", [])],
                            notes=[str(item) for item in payload.get("notes", [])],
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
                            validated_via_playwright=True,
                            browser_tab_index=None,
                            preferred_model=self.preferred_model,
                            model_selection_blocked=False,
                            answer_text="",
                            visible_source_count=0,
                            links=[],
                            blockers=[f"collector_error:{type(exc).__name__}"],
                            notes=[str(exc)[:300]],
                        )
                    )
        finally:
            try:
                browser_session.close()
            except Exception:  # noqa: BLE001
                pass

        return sessions


__all__ = ["PerplexityPlaywrightCollector", "PlaywrightCLIError"]
