"""Classes base para agentes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.utils.prompts import load_prompt


class BaseAgent(ABC):
    """Interface padrão de agente com método run."""

    name: str = "base-agent"
    prompt_filename: str = ""

    def get_system_prompt(self) -> str:
        if not self.prompt_filename:
            return ""
        return load_prompt(self.prompt_filename)

    @abstractmethod
    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Executa uma etapa e devolve atualizações no contexto."""


class BaseLLMAgent(BaseAgent):
    """Base para agentes com potencial uso futuro de LLM."""

    def __init__(self, model_name: str = "mock-llm") -> None:
        self.model_name = model_name

    def build_prompt(self, context: dict[str, Any]) -> str:
        # Extensão futura: montar prompt dinâmico com contexto de execução.
        return f"{self.get_system_prompt()}\n\n# Contexto\nChaves: {list(context.keys())}"
