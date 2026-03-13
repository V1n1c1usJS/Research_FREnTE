"""Schemas de configuração baseados em Pydantic."""

from typing import Literal

from pydantic import BaseModel, Field


class PipelineSettings(BaseModel):
    query: str = Field(..., min_length=3, description="Tema principal da pesquisa")
    limit: int = Field(default=10, ge=1, le=100, description="Quantidade máxima por etapa")
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
