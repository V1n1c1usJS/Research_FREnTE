"""Pipeline inicial de descoberta de bases ambientais."""

from __future__ import annotations

from src.agents.catalog_agent import CatalogAgent
from src.schemas.settings import PipelineSettings


class DiscoveryPipeline:
    def __init__(self, settings: PipelineSettings) -> None:
        self.settings = settings
        self.catalog_agent = CatalogAgent()

    def execute(self) -> str:
        candidates = self.catalog_agent.collect(self.settings)
        mode = "DRY-RUN" if self.settings.dry_run else "EXECUÇÃO"
        return (
            f"[{mode}] Pipeline concluído com {len(candidates)} fontes simuladas "
            f"para o tema '{self.settings.query}'."
        )
