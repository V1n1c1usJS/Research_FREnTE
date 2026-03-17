"""Schemas de configuracao baseados em Pydantic."""

from typing import Literal

from pydantic import BaseModel, Field


class PipelineSettings(BaseModel):
    query: str = Field(..., min_length=3, description="Tema principal da pesquisa")
    limit: int = Field(default=10, ge=1, le=100, description="Quantidade maxima por etapa")
    dry_run: bool = Field(default=True, description="Executa pipeline sem efeitos externos")
    web_research_mode: Literal["mock", "real"] = Field(
        default="mock",
        description="Seleciona conector de pesquisa web para o ResearchScoutAgent",
    )
    web_timeout_seconds: float = Field(
        default=8.0,
        ge=1.0,
        le=30.0,
        description="Timeout de chamadas HTTP do conector real de pesquisa web",
    )
    llm_mode: Literal["off", "auto", "openai", "groq"] = Field(
        default="auto",
        description=(
            "Seleciona o uso de LLM. "
            "'auto' usa OpenAI e depois Groq quando houver chaves configuradas; "
            "'off' desabilita; 'openai' e 'groq' exigem configuracao valida."
        ),
    )
    llm_model: str = Field(
        default="gpt-4.1-nano",
        min_length=3,
        description="Modelo do provedor LLM selecionado.",
    )
    llm_timeout_seconds: float = Field(
        default=60.0,
        ge=5.0,
        le=300.0,
        description="Timeout das chamadas ao provedor LLM.",
    )
    llm_temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Temperatura padrao para agentes baseados em LLM.",
    )
    llm_max_output_tokens: int = Field(
        default=1800,
        ge=128,
        le=16000,
        description="Limite de tokens de saida para respostas LLM.",
    )
    llm_fail_on_error: bool = Field(
        default=False,
        description="Quando verdadeiro, falhas de LLM interrompem a execucao em vez de cair no fallback heuristico.",
    )
