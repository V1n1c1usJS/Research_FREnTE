"""Utilitários para carregamento de prompts versionados em YAML."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError


PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


class AgentPromptMetadata(BaseModel):
    name: str
    version: str
    role: str


class StructuredPrompt(BaseModel):
    agent: AgentPromptMetadata
    objective: str
    context: list[str]
    input: list[str]
    output: list[str]
    rules: list[str]
    classification: list[str]
    runtime: list[str]


def _format_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _render_prompt(data: StructuredPrompt) -> str:
    return "\n\n".join(
        [
            "# Agent\n"
            f"- name: {data.agent.name}\n"
            f"- version: {data.agent.version}\n"
            f"- role: {data.agent.role}",
            f"# Objective\n{data.objective}",
            f"# Context\n{_format_list(data.context)}",
            f"# Input\n{_format_list(data.input)}",
            f"# Output\n{_format_list(data.output)}",
            f"# Rules\n{_format_list(data.rules)}",
            f"# Classification\n{_format_list(data.classification)}",
            f"# Runtime\n{_format_list(data.runtime)}",
        ]
    )


@lru_cache(maxsize=64)
def load_prompt(prompt_filename: str) -> str:
    """Carrega um prompt YAML, valida estrutura e renderiza texto para a LLM."""

    prompt_path = PROMPTS_DIR / prompt_filename
    payload = yaml.safe_load(prompt_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Prompt inválido em {prompt_filename}: estrutura YAML deve ser um objeto.")

    try:
        structured = StructuredPrompt.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Prompt inválido em {prompt_filename}: {exc}") from exc

    return _render_prompt(structured)
