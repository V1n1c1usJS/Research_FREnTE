"""Conectores para provedores de LLM."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any


class LLMConnectorError(RuntimeError):
    """Erro de integracao com provedor LLM."""


class LLMConnector(ABC):
    """Contrato generico para conectores de LLM."""

    provider: str = "unknown"
    model: str = "unknown"

    @abstractmethod
    def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Gera texto livre a partir de prompts estruturados."""

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any] | list[Any]:
        raw_text = self.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )
        return extract_json_payload(raw_text)


class OpenAIResponsesConnector(LLMConnector):
    """Conector baseado na Responses API da OpenAI."""

    provider = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gpt-4.1-nano",
        timeout_seconds: float = 60.0,
        max_output_tokens: int = 1800,
        temperature: float = 0.2,
    ) -> None:
        if not api_key:
            raise LLMConnectorError("OPENAI_API_KEY ausente.")

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - depende do ambiente local
            raise LLMConnectorError(
                "Pacote 'openai' nao instalado. Instale as dependencias do projeto antes de usar o modo OpenAI."
            ) from exc

        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        self._client = OpenAI(api_key=api_key, timeout=timeout_seconds)

    def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        response = self._client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
            max_output_tokens=max_output_tokens or self.max_output_tokens,
            temperature=self.temperature if temperature is None else temperature,
        )

        output_text = getattr(response, "output_text", "")
        if output_text:
            return output_text.strip()
        return _coerce_response_output_to_text(response)


class GroqResponsesConnector(LLMConnector):
    """Conector baseado na compatibilidade OpenAI da Groq."""

    provider = "groq"

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "groq/compound-mini",
        timeout_seconds: float = 60.0,
        max_output_tokens: int = 1800,
        temperature: float = 0.2,
    ) -> None:
        if not api_key:
            raise LLMConnectorError("GROQ_API_KEY ausente.")

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - depende do ambiente local
            raise LLMConnectorError(
                "Pacote 'openai' nao instalado. Instale as dependencias do projeto antes de usar o modo Groq."
            ) from exc

        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        self._client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
            timeout=timeout_seconds,
        )

    def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        response = self._client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
            max_output_tokens=max_output_tokens or self.max_output_tokens,
            temperature=self.temperature if temperature is None else temperature,
        )

        output_text = getattr(response, "output_text", "")
        if output_text:
            return output_text.strip()
        return _coerce_response_output_to_text(response)


def extract_json_payload(text: str) -> dict[str, Any] | list[Any]:
    """Extrai um payload JSON de uma resposta textual de LLM."""

    candidate = text.strip()
    if not candidate:
        raise LLMConnectorError("Resposta vazia recebida do LLM.")

    for normalized in _json_candidates(candidate):
        try:
            return json.loads(normalized)
        except json.JSONDecodeError:
            continue

    raise LLMConnectorError("Nao foi possivel extrair JSON valido da resposta do LLM.")


def _json_candidates(text: str) -> list[str]:
    stripped = text.strip()
    candidates = [stripped]

    fence_match = re.search(r"```(?:json)?\s*(.+?)\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        candidates.append(fence_match.group(1).strip())

    for opener, closer in (("{", "}"), ("[", "]")):
        start = stripped.find(opener)
        end = stripped.rfind(closer)
        if start != -1 and end != -1 and end > start:
            candidates.append(stripped[start : end + 1].strip())

    seen: set[str] = set()
    unique_candidates: list[str] = []
    for item in candidates:
        if item and item not in seen:
            seen.add(item)
            unique_candidates.append(item)
    return unique_candidates


def _coerce_response_output_to_text(response: Any) -> str:
    fragments: list[str] = []
    for item in getattr(response, "output", []) or []:
        content = getattr(item, "content", []) or []
        for part in content:
            text = getattr(part, "text", "")
            if text:
                fragments.append(text)
    return "\n".join(fragments).strip()
