"""Coleta de pesquisas no Perplexity via Playwright CLI."""

from __future__ import annotations

import json
import os
import re
import subprocess
from typing import Callable, Sequence
from uuid import uuid4

from src.schemas.records import (
    PerplexityLinkRecord,
    PerplexitySearchQueryRecord,
    PerplexitySearchSessionRecord,
)


class PlaywrightCLIError(RuntimeError):
    """Erro operacional ao usar o Playwright CLI."""


class PerplexityPlaywrightCollector:
    """Executa buscas no Perplexity via navegador real controlado pelo Playwright CLI."""

    def __init__(
        self,
        *,
        preferred_model: str = "Sonar",
        timeout_seconds: float = 120.0,
        per_query_wait_ms: int = 7000,
        session_prefix: str = "rf-pplx",
        command_runner: Callable[[Sequence[str], float], str] | None = None,
    ) -> None:
        self.preferred_model = preferred_model
        self.timeout_seconds = timeout_seconds
        self.per_query_wait_ms = per_query_wait_ms
        self.session_prefix = session_prefix
        self.command_runner = command_runner or self._default_command_runner

    def collect(self, query_plan: list[PerplexitySearchQueryRecord]) -> list[PerplexitySearchSessionRecord]:
        if not query_plan:
            return []

        session_name = f"{self.session_prefix}-{uuid4().hex[:6]}"
        sessions: list[PerplexitySearchSessionRecord] = []

        self._run_cli(["-s=" + session_name, "open", "about:blank"])
        try:
            for query in query_plan:
                try:
                    payload = self._run_query(session_name=session_name, query=query)
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
                self._run_cli(["-s=" + session_name, "close"])
            except Exception:  # noqa: BLE001
                pass

        return sessions

    def _run_query(
        self,
        *,
        session_name: str,
        query: PerplexitySearchQueryRecord,
    ) -> dict[str, object]:
        script = self._build_collection_script(query)
        output = self._run_cli(["-s=" + session_name, "run-code", script])
        return self._extract_result_json(output)

    def _run_cli(self, args: Sequence[str]) -> str:
        return self.command_runner(args, self.timeout_seconds)

    @staticmethod
    def _default_command_runner(args: Sequence[str], timeout_seconds: float) -> str:
        executable = "npx.cmd" if os.name == "nt" else "npx"
        command = [executable, "--yes", "--package", "@playwright/cli", "playwright-cli", *args]
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        output = (process.stdout or "") + (process.stderr or "")
        if process.returncode != 0:
            raise PlaywrightCLIError(output.strip() or "Playwright CLI command failed.")
        return output

    @staticmethod
    def _extract_result_json(output: str) -> dict[str, object]:
        match = re.search(
            r"### Result\s*\r?\n(?P<payload>.+?)\r?\n### Ran Playwright code",
            output,
            flags=re.DOTALL,
        )
        if not match:
            raise PlaywrightCLIError(f"Nao foi possivel extrair JSON do Playwright CLI: {output[:500]}")
        try:
            return json.loads(match.group("payload"))
        except json.JSONDecodeError as exc:  # pragma: no cover - depende do output externo
            raise PlaywrightCLIError(f"JSON invalido retornado pelo Playwright CLI: {exc}") from exc

    def _build_collection_script(self, query: PerplexitySearchQueryRecord) -> str:
        payload = json.dumps(
            {
                "query": query.query_text,
                "preferred_model": self.preferred_model,
                "wait_ms": self.per_query_wait_ms,
            },
            ensure_ascii=False,
        )
        return f"""
async (page) => {{
  const payload = {payload};
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const clean = (value, limit = 0) => {{
    const normalized = String(value || "").replace(/\\s+/g, " ").trim();
    return !limit || normalized.length <= limit ? normalized : normalized.slice(0, limit);
  }};
  const closeLoginModal = async () => {{
    const modal = page.locator('[data-testid="login-modal"]');
    if (await modal.count()) {{
      const closeButton = modal.getByRole('button', {{ name: /Fechar|Close/i }});
      if (await closeButton.count()) {{
        await closeButton.first().click();
        await sleep(400);
      }}
    }}
  }};
  const modelInfo = {{
    requested: payload.preferred_model || null,
    selected: null,
    blocked: false,
    blocker: null,
  }};

  await page.goto('https://www.perplexity.ai/', {{ waitUntil: 'domcontentloaded' }});
  await sleep(2200);
  await closeLoginModal();

  if (payload.preferred_model) {{
    try {{
      const modelButton = page.getByRole('button', {{ name: /Modelo|Model/i }});
      if (await modelButton.count()) {{
        await modelButton.first().click();
        await sleep(600);
        const modelItem = page.getByRole('menuitem', {{ name: new RegExp(payload.preferred_model, 'i') }});
        if (await modelItem.count()) {{
          await modelItem.first().click();
          modelInfo.selected = payload.preferred_model;
        }} else {{
          const loginPrompt = page.getByText(/Entre para escolher um modelo|Sign in to choose a model/i);
          if (await loginPrompt.count()) {{
            modelInfo.blocked = true;
            modelInfo.blocker = clean(await loginPrompt.first().innerText(), 180);
          }}
        }}
      }}
    }} catch (error) {{
      modelInfo.blocked = true;
      modelInfo.blocker = clean(error.message, 180);
    }}
    await closeLoginModal();
  }}

  const input = page.locator('#ask-input');
  await input.click();
  await sleep(250);
  try {{ await page.keyboard.press('Control+A'); }} catch (error) {{}}
  try {{ await page.keyboard.press('Meta+A'); }} catch (error) {{}}
  try {{ await page.keyboard.press('Backspace'); }} catch (error) {{}}
  await page.keyboard.type(payload.query, {{ delay: 12 }});
  await page.keyboard.press('Enter');

  await page.waitForURL(/\\/search\\//, {{ timeout: 45000 }});
  await sleep(payload.wait_ms);

  const answerText = await page.evaluate(() => {{
    const panel = document.querySelector('[role="tabpanel"]');
    const main = document.querySelector('main');
    return (panel?.textContent || main?.textContent || '').replace(/\\s+/g, ' ').trim();
  }});

  let visibleSourceCount = 0;
  try {{
    const sourceButton = page.getByRole('button', {{ name: /fontes|sources/i }});
    if (await sourceButton.count()) {{
      const label = clean(await sourceButton.first().innerText(), 40);
      const match = label.match(/(\\d+)/);
      visibleSourceCount = match ? Number(match[1]) : 0;
    }}
  }} catch (error) {{}}

  let linksTabOpened = false;
  try {{
    const linksTab = page.getByRole('tab', {{ name: /Links/i }});
    if (await linksTab.count()) {{
      await linksTab.first().click();
      await sleep(1200);
      linksTabOpened = true;
    }}
  }} catch (error) {{}}

  const links = await page.evaluate(() => {{
    const clean = (value, limit = 0) => {{
      const normalized = String(value || '').replace(/\\s+/g, ' ').trim();
      return !limit || normalized.length <= limit ? normalized : normalized.slice(0, limit);
    }};
    const anchors = Array.from(document.querySelectorAll('[role="tabpanel"] a[href^="http"], main a[href^="http"]'));
    const seen = new Set();
    const items = [];
    for (const anchor of anchors) {{
      const url = anchor.href;
      if (!url || seen.has(url)) continue;
      seen.add(url);
      let domain = '';
      try {{
        domain = new URL(url).hostname.replace(/^www\\./, '');
      }} catch (error) {{
        domain = '';
      }}
      if (!domain) continue;
      const title = clean(anchor.textContent || '', 220);
      const container = anchor.closest('a, article, li, div');
      const snippet = clean(container?.textContent || anchor.textContent || '', 650);
      items.push({{ title, url, domain, snippet }});
      if (items.length >= 25) break;
    }}
    return items;
  }});

  const blockers = [];
  if (modelInfo.blocked && modelInfo.blocker) blockers.push(`model_selection:${{modelInfo.blocker}}`);
  if (!linksTabOpened) blockers.push('links_tab_not_opened');
  if (!links.length) blockers.push('no_links_extracted');

  return {{
    page_url: page.url(),
    answer_text: clean(answerText, 12000),
    visible_source_count: visibleSourceCount,
    links,
    model_requested: modelInfo.requested,
    model_selected: modelInfo.selected,
    model_selection_blocked: modelInfo.blocked,
    model_selection_blocker: modelInfo.blocker,
    blockers,
    notes: [
      linksTabOpened ? 'links_tab_opened' : 'links_tab_unavailable',
      modelInfo.selected ? `model_selected:${{modelInfo.selected}}` : 'model_kept_default',
    ],
  }};
}}
""".strip()
