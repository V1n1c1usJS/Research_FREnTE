"""Agente para consolidar saída textual do pipeline."""

from __future__ import annotations

from typing import Any

from src.agents.base import BaseAgent
from src.schemas.records import CatalogExportRecord


class ReportAgent(BaseAgent):
    name = "report"
    prompt_filename = "report_agent.yaml"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.get_system_prompt()
        datasets = context["datasets"]
        sources = context["sources"]
        analytical_sources = [s for s in sources if s.source_class == "analytical_data_source"]
        scientific_sources = [s for s in sources if s.source_class == "scientific_knowledge_source"]
        extraction_plan = context["extraction_plan"]
        settings = context["settings"]
        web_meta = context.get("web_research_meta", {})

        literature = [d for d in datasets if d.dataset_kind == "literature"]
        data_catalog = [d for d in datasets if d.dataset_kind != "literature"]

        lines = [
            "# Relatório de Exemplo - Pipeline 100K (Dry-Run)",
            "",
            "## Contexto",
            "- Este relatório usa dados **simulados** para validar arquitetura do pipeline.",
            "- Nenhuma fonte foi consultada em tempo real nesta execução.",
            f"- Query: `{settings.query}`",
            f"- Total de registros simulados: `{len(datasets)}`",
            f"- Modo web solicitado/usado: `{web_meta.get('requested_mode', 'n/a')}` / `{web_meta.get('connector_mode_used', 'n/a')}`",
            f"- Status de recuperação web: `{web_meta.get('retrieval_status', 'n/a')}`",
            f"- Resultados brutos/kept/discarded: `{web_meta.get('raw_result_count', 0)}` / `{web_meta.get('kept_result_count', 0)}` / `{web_meta.get('discarded_irrelevant_count', 0)}`",
            "",
            "## Descoberta de datasets",
        ]

        for dataset in data_catalog[:6]:
            lines.append(
                f"- `{dataset.dataset_id}` | **{dataset.title}** | fonte={dataset.source_name} "
                f"| score={dataset.relevance_score} | prioridade={dataset.priority}"
            )

        lines.extend(["", "## Descoberta via literatura", ""])
        if literature:
            for item in literature:
                lines.append(
                    f"- `{item.dataset_id}` | **{item.title}** | score={item.relevance_score} "
                    f"| observação={'; '.join(item.methodological_notes[:1])}"
                )
        else:
            lines.append("- Nenhum registro de literatura gerado para este limite de execução.")


        lines.extend(["", "## Fontes para coleta de dados analíticos", ""])
        if analytical_sources:
            for source in analytical_sources[:8]:
                lines.append(
                    f"- {source.name} ({source.base_url}) | extractability={source.data_extractability} "
                    f"| histórico={source.historical_records_available} | export={source.structured_export_available}"
                )
        else:
            lines.append("- Nenhuma fonte analítica classificada nesta execução.")

        lines.extend(["", "## Fontes para fundamentação científica e metodológica", ""])
        if scientific_sources:
            for source in scientific_sources[:8]:
                lines.append(
                    f"- {source.name} ({source.base_url}) | scientific_value={source.scientific_value} "
                    f"| uso_recomendado={', '.join(source.recommended_pipeline_use[:2])}"
                )
        else:
            lines.append("- Nenhuma fonte científica classificada nesta execução.")

        lines.extend(["", "## Avaliação", ""])
        for dataset in datasets[:6]:
            lines.append(
                f"- {dataset.title}: score={dataset.relevance_score}, prioridade={dataset.priority}, "
                f"acesso={dataset.access_level}."
            )

        lines.extend(["", "## Plano de extração (simulado)"])
        for item in extraction_plan[:6]:
            lines.append(
                f"- {item['dataset_id']}: {item['strategy']} (ordem {item['execution_order']}) "
                f"- {item['methodological_observation']}"
            )

        lines.extend(["", "## Observações metodológicas", ""])
        lines.append("- Scores e prioridades são simulados para validação de fluxo ponta a ponta.")
        lines.append("- Separação entre descoberta, avaliação e relatório foi mantida por agente.")
        lines.append("- Fontes listadas foram usadas apenas como inspiração estrutural no mock.")

        catalog = CatalogExportRecord(
            run_id=context["run_metadata"].run_id,
            dataset_count=len(datasets),
            datasets=datasets,
            sources=sources,
        )
        return {"report_markdown": "\n".join(lines), "catalog_export": catalog}
