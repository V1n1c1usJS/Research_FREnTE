from src.connectors.perplexity_playwright import PerplexityPlaywrightCollector


def test_playwright_cli_result_parser_extracts_json_payload() -> None:
    output = """### Result
{"page_url":"https://www.perplexity.ai/search/mock","answer_text":"ok","visible_source_count":3,"links":[{"title":"Hidroweb","url":"https://www.snirh.gov.br/hidroweb","domain":"www.snirh.gov.br","snippet":"portal"}],"model_requested":"Sonar","model_selected":null,"model_selection_blocked":true,"model_selection_blocker":"Entre para escolher um modelo","blockers":["model_selection:Entre para escolher um modelo"],"notes":["links_tab_opened"]}
### Ran Playwright code
```js
await (async (page) => {{ return {{ ok: true }}; }})(page);
```"""

    payload = PerplexityPlaywrightCollector._extract_result_json(output)

    assert payload["page_url"] == "https://www.perplexity.ai/search/mock"
    assert payload["visible_source_count"] == 3
    assert payload["model_requested"] == "Sonar"
    assert payload["links"][0]["domain"] == "www.snirh.gov.br"
