from pathlib import Path

import pytest

from src.utils.prompts import load_prompt


def test_load_prompt_from_yaml_and_render_sections() -> None:
    rendered = load_prompt("enrich_agent.yaml")

    assert "# Agent" in rendered
    assert "name: EnrichAgent" in rendered
    assert "# Objective" in rendered
    assert "# Rules" in rendered


def test_load_prompt_raises_on_invalid_yaml_structure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bad_prompt = tmp_path / "bad.yaml"
    bad_prompt.write_text("[]", encoding="utf-8")

    import src.utils.prompts as prompts_module

    monkeypatch.setattr(prompts_module, "PROMPTS_DIR", tmp_path)
    load_prompt.cache_clear()

    with pytest.raises(ValueError):
        load_prompt("bad.yaml")
