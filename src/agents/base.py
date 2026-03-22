"""Classes base para agentes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.connectors.llm import LLMConnector
from src.utils.prompts import load_prompt


class BaseAgent(ABC):
    """Interface padrao de agente com metodo run."""

    name: str = "base-agent"
    prompt_filename: str = ""

    def get_system_prompt(self) -> str:
        if not self.prompt_filename:
            return ""
        return load_prompt(self.prompt_filename)

    @abstractmethod
    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Executa uma etapa e devolve atualizacoes no contexto."""


class BaseLLMAgent(BaseAgent):
    """Base para agentes com suporte opcional a LLM."""

    def __init__(
        self,
        *,
        llm_connector: LLMConnector | None = None,
        fail_on_error: bool = False,
    ) -> None:
        self.llm_connector = llm_connector
        self.fail_on_error = fail_on_error

    @property
    def has_llm(self) -> bool:
        return self.llm_connector is not None
