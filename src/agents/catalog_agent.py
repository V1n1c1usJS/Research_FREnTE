"""Agente inicial para catalogação simulada de fontes."""

from __future__ import annotations

from src.schemas.settings import PipelineSettings


class CatalogAgent:
    """Representa um agente de descoberta/catálogo sem integrações externas."""

    def collect(self, settings: PipelineSettings) -> list[str]:
        base_item = f"Fonte simulada para: {settings.query}"
        return [f"{base_item} #{i + 1}" for i in range(settings.limit)]
