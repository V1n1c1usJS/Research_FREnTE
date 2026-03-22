"""Sessao incremental de navegador para automacao do Perplexity via Playwright CLI."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Callable, Sequence
from uuid import uuid4


class PlaywrightCLIError(RuntimeError):
    """Erro operacional ao usar o Playwright CLI."""


class PerplexityBrowserSession:
    """Controla uma sessao unica do navegador e executa buscas em etapas curtas."""

    def __init__(
        self,
        *,
        preferred_model: str = "Sonar",
        timeout_seconds: float = 120.0,
        per_query_wait_ms: int = 7000,
        headed: bool = False,
        session_prefix: str = "rf-pplx",
        session_name: str | None = None,
        prompt_dir: Path | None = None,
        command_runner: Callable[[Sequence[str], float], str] | None = None,
    ) -> None:
        self.preferred_model = preferred_model
        self.timeout_seconds = timeout_seconds
        self.per_query_wait_ms = per_query_wait_ms
        self.headed = headed
        self.session_name = session_name or f"{session_prefix}-{uuid4().hex[:6]}"
        self.prompt_dir = prompt_dir or Path("output") / "playwright" / "prompts"
        self.command_runner = command_runner or self._default_command_runner
        self._is_open = False
        self._working_tab_index = 1

    def open(self) -> None:
        if self._is_open:
            return
        args = ["-s=" + self.session_name, "open", "about:blank"]
        if self.headed:
            args.append("--headed")
        self._run_cli(args)
        self._is_open = True

    def close(self) -> None:
        if not self._is_open:
            return
        self._run_cli(["-s=" + self.session_name, "close"])
        self._is_open = False

    def collect_query(self, query_text: str) -> dict[str, object]:
        self.open()
        tab_index = self.open_chat_tab()
        prompt_path = self._write_prompt_file(query_text)
        try:
            try:
                self.wait_for_page_ready()
            except Exception as exc:
                raise PlaywrightCLIError(f"step=wait_for_page_ready | {exc}") from exc
            try:
                self.close_login_modal()
            except Exception as exc:
                raise PlaywrightCLIError(f"step=close_login_modal | {exc}") from exc
            try:
                model_info = self.select_model_if_possible()
            except Exception as exc:
                raise PlaywrightCLIError(f"step=select_model_if_possible | {exc}") from exc
            try:
                submit_meta = self.submit_prompt(prompt_path)
            except Exception as exc:
                raise PlaywrightCLIError(f"step=submit_prompt | {exc}") from exc
            try:
                self.wait_for_answer()
            except Exception as exc:
                raise PlaywrightCLIError(f"step=wait_for_answer | {exc}") from exc
            try:
                links_tab_opened = self.open_links_tab()
            except Exception as exc:
                raise PlaywrightCLIError(f"step=open_links_tab | {exc}") from exc
            try:
                payload = self.extract_payload()
            except Exception as exc:
                raise PlaywrightCLIError(f"step=extract_payload | {exc}") from exc
            payload["browser_tab_index"] = tab_index
            payload["model_requested"] = self.preferred_model
            payload["model_selected"] = model_info.get("selected")
            payload["model_selection_blocked"] = bool(model_info.get("blocked", False))
            payload["model_selection_blocker"] = model_info.get("blocker")
            payload["page_url"] = payload.get("page_url") or submit_meta.get("page_url") or ""
            blockers = [str(item) for item in payload.get("blockers", [])]
            notes = [str(item) for item in payload.get("notes", [])]
            if payload["model_selection_blocked"] and payload["model_selection_blocker"]:
                blockers.append(f"model_selection:{payload['model_selection_blocker']}")
            if links_tab_opened:
                notes.append("links_tab_opened")
            else:
                blockers.append("links_tab_not_opened")
                notes.append("links_tab_unavailable")
            if payload.get("model_selected"):
                notes.append(f"model_selected:{payload['model_selected']}")
            else:
                notes.append("model_kept_default")
            notes.append(f"browser_tab_index:{tab_index}")
            if not payload.get("links"):
                blockers.append("no_links_extracted")
            payload["blockers"] = self._dedupe_strings(blockers)
            payload["notes"] = self._dedupe_strings(notes)
            return payload
        finally:
            try:
                self.close_chat_tab(tab_index)
            except Exception:
                pass
            try:
                prompt_path.unlink(missing_ok=True)
            except OSError:
                pass

    def open_home(self) -> None:
        self._run_cli(["-s=" + self.session_name, "goto", "https://www.perplexity.ai/"])

    def open_chat_tab(self) -> int:
        self._run_cli(["-s=" + self.session_name, "tab-new", "https://www.perplexity.ai/"])
        self.select_tab(self._working_tab_index)
        return self._working_tab_index

    def close_chat_tab(self, tab_index: int) -> None:
        self.select_tab(tab_index)
        self._run_cli(["-s=" + self.session_name, "tab-close", str(tab_index)])
        self.select_tab(0)

    def select_tab(self, tab_index: int) -> None:
        self._run_cli(["-s=" + self.session_name, "tab-select", str(tab_index)])

    def close_login_modal(self) -> None:
        self._run_code(
            "\n".join(
                [
                    "  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));",
                    "  await sleep(1200);",
                    "  try {",
                    "    const closeButton = page.getByRole('button', { name: /Fechar|Close/i });",
                    "    if (await closeButton.count()) {",
                    "      await closeButton.first().click();",
                    "      await sleep(300);",
                    "    }",
                    "  } catch (error) {}",
                    "  return { closed: true, page_url: page.url() };",
                ]
            )
        )

    def wait_for_page_ready(self) -> dict[str, object]:
        script = "\n".join(
            [
                "  await page.waitForLoadState('domcontentloaded');",
                "  await page.waitForTimeout(1800);",
                "  const ready = { page_url: page.url(), body_present: false, main_present: false };",
                "  ready.body_present = await page.locator('body').count() > 0;",
                "  ready.main_present = await page.locator('main').count() > 0;",
                "  return ready;",
            ]
        )
        return self._run_code(script)

    def select_model_if_possible(self) -> dict[str, object]:
        model_value = json.dumps(self.preferred_model, ensure_ascii=True)
        script = "\n".join(
            [
                f"  const preferredModel = {model_value};",
                "  const clean = (value, limit = 0) => {",
                "    const normalized = String(value || '').replace(/\\s+/g, ' ').trim();",
                "    if (!limit || normalized.length <= limit) return normalized;",
                "    return normalized.slice(0, limit);",
                "  };",
                "  const result = { requested: preferredModel || null, selected: null, blocked: false, blocker: null };",
                "  if (!preferredModel) return result;",
                "  try {",
                "    const modelButton = page.getByRole('button', { name: /Modelo|Model/i });",
                "    if (await modelButton.count()) {",
                "      await modelButton.first().click();",
                "      await page.waitForTimeout(600);",
                "      const modelItem = page.getByRole('menuitem', { name: new RegExp(preferredModel, 'i') });",
                "      if (await modelItem.count()) {",
                "        await modelItem.first().click();",
                "        result.selected = preferredModel;",
                "      } else {",
                "        const loginPrompt = page.getByText(/Entre para escolher um modelo|Sign in to choose a model/i);",
                "        if (await loginPrompt.count()) {",
                "          result.blocked = true;",
                "          result.blocker = clean(await loginPrompt.first().innerText(), 180);",
                "        }",
                "      }",
                "    }",
                "  } catch (error) {",
                "    result.blocked = true;",
                "    result.blocker = clean((error && error.message) || error || '', 180);",
                "  }",
                "  return result;",
            ]
        )
        return self._run_code(script)

    def submit_prompt(self, prompt_path: Path) -> dict[str, object]:
        path_value = json.dumps(str(prompt_path.resolve()), ensure_ascii=True)
        script = "\n".join(
            [
                "  const fs = require('fs');",
                f"  const promptPath = {path_value};",
                "  const prompt = String(fs.readFileSync(promptPath, 'utf8') || '').trim();",
                "  const result = { submitted: false, page_url: page.url(), prompt_length: prompt.length, input_selector: null };",
                "  const selectors = ['#ask-input', 'textarea', '[contenteditable=\"true\"]'];",
                "  let input = null;",
                "  for (const selector of selectors) {",
                "    const locator = page.locator(selector);",
                "    if (await locator.count()) {",
                "      await locator.first().waitFor({ state: 'visible', timeout: 20000 });",
                "      input = locator.first();",
                "      result.input_selector = selector;",
                "      break;",
                "    }",
                "  }",
                "  if (!input) {",
                "    throw new Error('perplexity_input_not_found');",
                "  }",
                "  await input.click();",
                "  await page.waitForTimeout(250);",
                "  try { await page.keyboard.press('Control+A'); } catch (error) {}",
                "  try { await page.keyboard.press('Meta+A'); } catch (error) {}",
                "  try { await page.keyboard.press('Backspace'); } catch (error) {}",
                "  await page.keyboard.type(prompt, { delay: 10 });",
                "  await page.keyboard.press('Enter');",
                "  result.submitted = true;",
                "  return result;",
            ]
        )
        return self._run_code(script)

    def wait_for_answer(self) -> None:
        wait_script = "\n".join(
            [
                f"  const waitMs = {int(self.per_query_wait_ms)};",
                "  await page.waitForURL((url) => url.href.indexOf('/search/') >= 0, { timeout: 45000 });",
                "  await page.waitForTimeout(waitMs);",
                "  return { page_url: page.url(), waited_ms: waitMs };",
            ]
        )
        self._run_code(wait_script)

    def open_links_tab(self) -> bool:
        script = "\n".join(
            [
                "  try {",
                "    const linksTab = page.getByRole('tab', { name: /Links/i });",
                "    if (await linksTab.count()) {",
                "      await linksTab.first().click();",
                    "      await page.waitForTimeout(1200);",
                "      return { opened: true };",
                "    }",
                "  } catch (error) {}",
                "  return { opened: false };",
            ]
        )
        return bool(self._run_code(script).get("opened", False))

    def extract_payload(self) -> dict[str, object]:
        script = "\n".join(
            [
                "  const clean = (value, limit = 0) => {",
                "    const normalized = String(value || '').replace(/\\s+/g, ' ').trim();",
                "    if (!limit || normalized.length <= limit) return normalized;",
                "    return normalized.slice(0, limit);",
                "  };",
                "  const answerText = await page.evaluate(() => {",
                "    const panel = document.querySelector('[role=\"tabpanel\"]');",
                "    const main = document.querySelector('main');",
                "    return (panel && panel.textContent) || (main && main.textContent) || '';",
                "  });",
                "  let visibleSourceCount = 0;",
                "  try {",
                "    const sourceButton = page.getByRole('button', { name: /fontes|sources/i });",
                "    if (await sourceButton.count()) {",
                "      const label = clean(await sourceButton.first().innerText(), 40);",
                "      const match = label.match(/(\\d+)/);",
                "      visibleSourceCount = match ? Number(match[1]) : 0;",
                "    }",
                "  } catch (error) {}",
                "  const links = await page.evaluate(() => {",
                "    const clean = (value, limit = 0) => {",
                "      const normalized = String(value || '').replace(/\\s+/g, ' ').trim();",
                "      if (!limit || normalized.length <= limit) return normalized;",
                "      return normalized.slice(0, limit);",
                "    };",
                "    const anchors = Array.from(document.querySelectorAll('[role=\"tabpanel\"] a[href^=\"http\"], main a[href^=\"http\"]'));",
                "    const seen = new Set();",
                "    const items = [];",
                "    for (const anchor of anchors) {",
                "      const url = anchor.href;",
                "      if (!url || seen.has(url)) continue;",
                "      seen.add(url);",
                "      let domain = '';",
                "      try {",
                "        domain = new URL(url).hostname.replace(/^www\\./, '');",
                "      } catch (error) {",
                "        domain = '';",
                "      }",
                "      if (!domain) continue;",
                "      const title = clean(anchor.textContent || '', 220);",
                "      const container = anchor.closest('a, article, li, div');",
                "      const snippetSource = (container && container.textContent) || anchor.textContent || '';",
                "      items.push({ title, url, domain, snippet: clean(snippetSource, 650) });",
                "      if (items.length >= 25) break;",
                "    }",
                "    return items;",
                "  });",
                "  return {",
                "    page_url: page.url(),",
                "    answer_text: clean(answerText, 12000),",
                "    visible_source_count: visibleSourceCount,",
                "    links,",
                "    blockers: [],",
                "    notes: [],",
                "  };",
            ]
        )
        return self._run_code(script)

    def _write_prompt_file(self, query_text: str) -> Path:
        self.prompt_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = self.prompt_dir / f"{self.session_name}-{uuid4().hex[:8]}.txt"
        prompt_path.write_text(query_text, encoding="utf-8")
        return prompt_path

    def _run_code(self, script: str) -> dict[str, object]:
        wrapped_script = "async page => {\n" + script + "\n}"
        output = self._run_cli(["-s=" + self.session_name, "run-code", wrapped_script])
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

    @staticmethod
    def _dedupe_strings(values: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for item in values:
            normalized = str(item).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(normalized)
        return deduped
