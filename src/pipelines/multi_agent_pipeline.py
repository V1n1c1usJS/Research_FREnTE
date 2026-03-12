"""Pipeline inicial que delega execução ao OrchestratorAgent."""

from __future__ import annotations

from src.agents.orchestrator_agent import OrchestratorAgent
from src.schemas.settings import PipelineSettings


class MultiAgentPipeline:
    def __init__(self, settings: PipelineSettings) -> None:
        self.settings = settings

    def execute(self) -> dict[str, str | int]:
        orchestrator = OrchestratorAgent(settings=self.settings)
        return orchestrator.run()
