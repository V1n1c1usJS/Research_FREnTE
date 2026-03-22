"""Etapa 1 — filtra e valida as fontes brutas da coleta (sem LLM)."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from src.agents.base import BaseAgent
from src.schemas.records import FilteredSource, PerplexitySearchQueryRecord, PerplexitySearchSessionRecord


class FilterValidateAgent(BaseAgent):
    name = "filter-validate"
    prompt_filename = "filter_validate_agent.yaml"

    MIN_SNIPPET_LEN = 20

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        sessions: list[PerplexitySearchSessionRecord] = context.get("perplexity_sessions", [])
        search_plan: list[PerplexitySearchQueryRecord] = context.get("perplexity_search_plan", [])

        priority_by_query = {q.query_id: q.priority for q in search_plan}

        seen_urls: set[str] = set()
        filtered: list[FilteredSource] = []
        skipped_malformed = 0
        skipped_short_snippet = 0
        skipped_duplicate = 0
        review_count = 0

        for session in sessions:
            if session.collection_status != "ok":
                continue

            track_priority = priority_by_query.get(session.query_id, "medium")

            for link in session.links:
                normalized = self._normalize_url(link.url)
                if not normalized:
                    skipped_malformed += 1
                    continue

                notes: list[str] = []
                needs_review = False

                if normalized in seen_urls:
                    skipped_duplicate += 1
                    continue
                seen_urls.add(normalized)

                snippet = link.snippet.strip()
                if len(snippet) < self.MIN_SNIPPET_LEN:
                    skipped_short_snippet += 1
                    notes.append("snippet_curto")
                    needs_review = True

                title = (link.title or "").strip() or link.domain or normalized

                if needs_review:
                    review_count += 1

                filtered.append(
                    FilteredSource(
                        url=normalized,
                        title=title,
                        snippet=snippet,
                        source_domain=self._extract_domain(normalized),
                        track_origin=session.research_track or "",
                        track_priority=track_priority,
                        track_intent=session.target_intent or "dataset_discovery",
                        needs_review=needs_review,
                        filter_notes=notes,
                    )
                )

        return {
            "filtered_sources": filtered,
            "filter_meta": {
                "total_sessions": len(sessions),
                "ok_sessions": sum(1 for s in sessions if s.collection_status == "ok"),
                "error_sessions": sum(1 for s in sessions if s.collection_status != "ok"),
                "total_links_seen": len(seen_urls) + skipped_duplicate + skipped_malformed,
                "filtered_source_count": len(filtered),
                "skipped_malformed": skipped_malformed,
                "skipped_short_snippet": skipped_short_snippet,
                "skipped_duplicate": skipped_duplicate,
                "needs_review_count": review_count,
            },
        }

    @staticmethod
    def _normalize_url(url: str) -> str:
        try:
            parsed = urlparse(url.strip())
        except Exception:
            return ""
        if not parsed.scheme or not parsed.netloc:
            return ""
        path = parsed.path.rstrip("/") or "/"
        return f"{parsed.scheme}://{parsed.netloc}{path}"

    @staticmethod
    def _extract_domain(url: str) -> str:
        try:
            return urlparse(url).netloc.replace("www.", "").strip().lower()
        except Exception:
            return ""
