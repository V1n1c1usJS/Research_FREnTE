"""Agente para consolidar saida textual do pipeline."""

from __future__ import annotations

from typing import Any

from src.agents.base import BaseAgent
from src.schemas.records import CatalogExportRecord


class ReportAgent(BaseAgent):
    name = "report"
    prompt_filename = "report_agent.yaml"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        datasets = context["datasets"]
        sources = context["sources"]
        analytical_sources = [s for s in sources if s.source_class == "analytical_data_source"]
        scientific_sources = [s for s in sources if s.source_class == "scientific_knowledge_source"]
        extraction_plan = context["extraction_plan"]
        settings = context["settings"]
        web_meta = context.get("web_research_meta", {})
        scout_triage_meta = context.get("research_scout_triage_meta", {})
        query_expansion_meta = context.get("query_expansion_meta", {})
        llm_runtime = context.get("llm_runtime", {})

        literature = [d for d in datasets if d.dataset_kind == "literature"]
        data_catalog = [d for d in datasets if d.dataset_kind != "literature"]

        lines = [
            f"# Relatorio de Execucao - Pipeline 100K ({'Dry-Run' if settings.dry_run else 'Run'})",
            "",
            "## Contexto",
            f"- Query: `{settings.query}`",
            f"- Total de registros: `{len(datasets)}`",
            f"- Modo web solicitado/usado: `{web_meta.get('requested_mode', 'n/a')}` / `{web_meta.get('connector_mode_used', 'n/a')}`",
            f"- Status de recuperacao web: `{web_meta.get('retrieval_status', 'n/a')}`",
            f"- Resultados brutos/kept/discarded: `{web_meta.get('raw_result_count', 0)}` / `{web_meta.get('kept_result_count', 0)}` / `{web_meta.get('discarded_irrelevant_count', 0)}`",
            f"- Scout triage via: `{scout_triage_meta.get('execution_mode', 'heuristic')}`",
            f"- Query expansion via: `{query_expansion_meta.get('execution_mode', 'heuristic')}`",
            f"- Provedor/modelo LLM ativos: `{llm_runtime.get('active_provider', 'heuristic')}` / `{llm_runtime.get('active_model', 'n/a')}`",
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
                    f"| observacao={'; '.join(item.methodological_notes[:1])}"
                )
        else:
            lines.append("- Nenhum registro de literatura gerado para este limite de execucao.")

        lines.extend(["", "## Fontes para coleta de dados analiticos", ""])
        if analytical_sources:
            for source in analytical_sources[:8]:
                lines.append(
                    f"- {source.name} ({source.base_url}) | extractability={source.data_extractability} "
                    f"| historico={source.historical_records_available} | export={source.structured_export_available}"
                )
        else:
            lines.append("- Nenhuma fonte analitica classificada nesta execucao.")

        lines.extend(["", "## Fontes para fundamentacao cientifica e metodologica", ""])
        if scientific_sources:
            for source in scientific_sources[:8]:
                lines.append(
                    f"- {source.name} ({source.base_url}) | scientific_value={source.scientific_value} "
                    f"| uso_recomendado={', '.join(source.recommended_pipeline_use[:2])}"
                )
        else:
            lines.append("- Nenhuma fonte cientifica classificada nesta execucao.")

        lines.extend(["", "## Avaliacao", ""])
        for dataset in datasets[:6]:
            lines.append(
                f"- {dataset.title}: score={dataset.relevance_score}, prioridade={dataset.priority}, "
                f"acesso={dataset.access_level}."
            )

        lines.extend(["", "## Plano de extracao"])
        for item in extraction_plan[:6]:
            lines.append(
                f"- {item['dataset_id']}: {item['strategy']} (ordem {item['execution_order']}) "
                f"- {item['methodological_observation']}"
            )

        lines.extend(["", "## Observacoes metodologicas", ""])
        lines.append("- A execucao preserva separacao entre descoberta, avaliacao e relatorio.")
        lines.append("- O uso de LLM foi restringido a descoberta de fontes e expansao de queries.")
        lines.append("- O relatorio final permanece deterministico para reduzir deriva narrativa.")
        if llm_runtime.get("setup_error"):
            lines.append(f"- Configuracao LLM com ressalva: {llm_runtime['setup_error']}")
        if scout_triage_meta.get("error"):
            lines.append(f"- Scout triage caiu em fallback: {scout_triage_meta['error']}")
        if query_expansion_meta.get("error"):
            lines.append(f"- Query expansion caiu em fallback: {query_expansion_meta['error']}")

        catalog = CatalogExportRecord(
            run_id=context["run_metadata"].run_id,
            dataset_count=len(datasets),
            datasets=datasets,
            sources=sources,
        )
        return {
            "report_markdown": "\n".join(lines),
            "catalog_export": catalog,
            "report_meta": {
                "execution_mode": "heuristic",
                "provider": None,
                "model": None,
                "error": None,
            },
        }
