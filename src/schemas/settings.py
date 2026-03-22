"""Schemas de configuracao do fluxo Perplexity-first."""

from pydantic import BaseModel, Field


class PipelineSettings(BaseModel):
    query: str = Field(..., min_length=3, description="Tema principal da pesquisa")
    limit: int = Field(default=10, ge=1, le=100, description="Quantidade maxima por etapa")
