"""Schemas de configuração baseados em Pydantic."""

from pydantic import BaseModel, Field


class PipelineSettings(BaseModel):
    query: str = Field(..., min_length=3, description="Tema principal da pesquisa")
    limit: int = Field(default=10, ge=1, le=100, description="Quantidade máxima por etapa")
    dry_run: bool = Field(default=True, description="Executa pipeline sem efeitos externos")
