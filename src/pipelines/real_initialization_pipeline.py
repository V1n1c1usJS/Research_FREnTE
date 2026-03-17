"""Inicializacao real em larga escala com multiplas queries e agregacao deduplicada."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from src.pipelines.multi_agent_pipeline import MultiAgentPipeline
from src.schemas.settings import PipelineSettings
from src.utils.io import write_catalog_csv, write_json, write_markdown
from src.utils.manual_research_guides import (
    build_default_manual_research_guides,
    build_manual_research_guides,
    render_manual_research_guides_markdown,
)


class RealInitializationPipeline:
    """Executa multiplos runs reais e consolida um bootstrap inicial do catalogo."""

    DEFAULT_SEED_QUERIES = (
        "impactos humanos no Rio Tiete reservatorios Sao Paulo Tres Lagoas qualidade agua",
        "Rio Tiete ANA Hidroweb vazao nivel chuva dados",
        "Rio Tiete MapBiomas uso da terra cobertura do solo dados",
        "Rio Tiete IBGE SIDRA indicadores territoriais dados",
        "Rio Tiete SNIS agua esgoto saneamento dados",
        "Reservatorio de Jupia hidrologia qualidade da agua dados",
        "Rio Tiete INPE queimadas focos de calor dados",
        "Rio Tiete SciELO artigos bases de dados qualidade da agua",
    )

    def __init__(
        self,
        *,
        limit_per_run: int = 10,
        web_timeout_seconds: float = 5.0,
        max_queries: int = 8,
        queries: list[str] | None = None,
        llm_mode: str = "auto",
        llm_model: str = "gpt-4.1-nano",
        llm_timeout_seconds: float = 60.0,
        llm_temperature: float = 0.2,
        llm_max_output_tokens: int = 1800,
        llm_fail_on_error: bool = False,
        pipeline_factory: Callable[[PipelineSettings], Any] | None = None,
    ) -> None:
        self.limit_per_run = limit_per_run
        self.web_timeout_seconds = web_timeout_seconds
        self.max_queries = max_queries
        self.queries = (queries or list(self.DEFAULT_SEED_QUERIES))[:max_queries]
        self.llm_mode = llm_mode
        self.llm_model = llm_model
        self.llm_timeout_seconds = llm_timeout_seconds
        self.llm_temperature = llm_temperature
        self.llm_max_output_tokens = llm_max_output_tokens
        self.llm_fail_on_error = llm_fail_on_error
        self.pipeline_factory = pipeline_factory or MultiAgentPipeline

    def execute(self) -> dict[str, Any]:
        bootstrap_id = f"real-init-{uuid4().hex[:8]}"
        generated_at = datetime.now(timezone.utc).isoformat()
        bootstrap_dir = Path("data") / "initializations" / bootstrap_id
        bootstrap_json_path = bootstrap_dir / "bootstrap.json"
        manual_guides_path = bootstrap_dir / "manual_research_guides.json"
        report_path = Path("reports") / f"{bootstrap_id}.md"
        export_path = Path("reports") / f"{bootstrap_id}.csv"
        manual_guides_report_path = Path("reports") / f"{bootstrap_id}-manual-guide.md"

        run_summaries: list[dict[str, Any]] = []
        failed_queries: list[dict[str, str]] = []
        buckets: dict[str, dict[str, Any]] = {}

        for query in self.queries:
            try:
                settings = PipelineSettings(
                    query=query,
                    limit=self.limit_per_run,
                    dry_run=False,
                    web_research_mode="real",
                    web_timeout_seconds=self.web_timeout_seconds,
                    llm_mode=self.llm_mode,
                    llm_model=self.llm_model,
                    llm_timeout_seconds=self.llm_timeout_seconds,
                    llm_temperature=self.llm_temperature,
                    llm_max_output_tokens=self.llm_max_output_tokens,
                    llm_fail_on_error=self.llm_fail_on_error,
                )
                result = self.pipeline_factory(settings).execute()
                catalog_payload = json.loads(Path(result["catalog_path"]).read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                failed_queries.append(
                    {
                        "query": query,
                        "error_type": type(exc).__name__,
                        "error_message": str(exc) or "no detail",
                    }
                )
                continue

            run_summaries.append(
                {
                    "run_id": result["run_id"],
                    "query": query,
                    "dataset_count": result["dataset_count"],
                    "report_path": result["report_path"],
                    "catalog_path": result["catalog_path"],
                    "export_path": result["export_path"],
                }
            )

            for dataset in catalog_payload.get("datasets", []):
                key = self._dataset_key(dataset)
                if key not in buckets:
                    buckets[key] = {
                        "dataset": dataset,
                        "occurrences": 0,
                        "run_ids": [],
                        "queries": [],
                    }

                bucket = buckets[key]
                bucket["occurrences"] += 1
                if result["run_id"] not in bucket["run_ids"]:
                    bucket["run_ids"].append(result["run_id"])
                if query not in bucket["queries"]:
                    bucket["queries"].append(query)

                best_dataset = bucket["dataset"]
                if float(dataset.get("relevance_score", 0.0)) > float(best_dataset.get("relevance_score", 0.0)):
                    bucket["dataset"] = dataset

        aggregated_datasets: list[dict[str, Any]] = []
        for idx, bucket in enumerate(
            sorted(
                buckets.values(),
                key=lambda item: (
                    float(item["dataset"].get("relevance_score", 0.0)),
                    item["occurrences"],
                ),
                reverse=True,
            ),
            start=1,
        ):
            dataset = dict(bucket["dataset"])
            dataset["dataset_id"] = f"boot-{idx:03d}"
            dataset["bootstrap_occurrences"] = bucket["occurrences"]
            dataset["bootstrap_run_ids"] = bucket["run_ids"]
            dataset["bootstrap_queries"] = bucket["queries"]
            aggregated_datasets.append(dataset)

        manual_guides_mode = "discovered_datasets"
        manual_guides = build_manual_research_guides(aggregated_datasets)
        if not manual_guides:
            manual_guides = build_default_manual_research_guides()
            manual_guides_mode = "validated_seed_portals"
        write_json(manual_guides_path, manual_guides)
        write_markdown(
            manual_guides_report_path,
            render_manual_research_guides_markdown(
                bootstrap_id=bootstrap_id,
                guides=manual_guides,
            ),
        )

        bootstrap_payload = {
            "bootstrap_id": bootstrap_id,
            "generated_at": generated_at,
            "mode": "real-init",
            "limit_per_run": self.limit_per_run,
            "web_timeout_seconds": self.web_timeout_seconds,
            "llm_mode": self.llm_mode,
            "llm_model": self.llm_model,
            "llm_timeout_seconds": self.llm_timeout_seconds,
            "llm_temperature": self.llm_temperature,
            "llm_max_output_tokens": self.llm_max_output_tokens,
            "llm_fail_on_error": self.llm_fail_on_error,
            "seed_queries": self.queries,
            "attempted_query_count": len(self.queries),
            "run_count": len(run_summaries),
            "failed_query_count": len(failed_queries),
            "dataset_count": len(aggregated_datasets),
            "manual_guides_count": len(manual_guides),
            "manual_guides_mode": manual_guides_mode,
            "manual_guides_path": str(manual_guides_path),
            "manual_guides_report_path": str(manual_guides_report_path),
            "runs": run_summaries,
            "failed_queries": failed_queries,
            "datasets": aggregated_datasets,
        }
        write_json(bootstrap_json_path, bootstrap_payload)

        csv_rows = [
            {
                "dataset_id": item["dataset_id"],
                "title": item.get("title", ""),
                "canonical_url": item.get("canonical_url", ""),
                "source_name": item.get("source_name", ""),
                "relevance_score": item.get("relevance_score", 0.0),
                "priority": item.get("priority", ""),
                "access_level": item.get("access_level", ""),
                "bootstrap_occurrences": item.get("bootstrap_occurrences", 0),
                "bootstrap_run_ids": ",".join(item.get("bootstrap_run_ids", [])),
            }
            for item in aggregated_datasets
        ]
        write_catalog_csv(
            export_path,
            csv_rows,
            fieldnames=[
                "dataset_id",
                "title",
                "canonical_url",
                "source_name",
                "relevance_score",
                "priority",
                "access_level",
                "bootstrap_occurrences",
                "bootstrap_run_ids",
            ],
        )

        write_markdown(
            report_path,
            self._build_report(
                bootstrap_id=bootstrap_id,
                generated_at=generated_at,
                run_summaries=run_summaries,
                failed_queries=failed_queries,
                datasets=aggregated_datasets,
                bootstrap_path=str(bootstrap_json_path),
                manual_guides_count=len(manual_guides),
                manual_guides_mode=manual_guides_mode,
                manual_guides_path=str(manual_guides_path),
                manual_guides_report_path=str(manual_guides_report_path),
                llm_mode=self.llm_mode,
                llm_model=self.llm_model,
            ),
        )

        return {
            "bootstrap_id": bootstrap_id,
            "report_path": str(report_path),
            "bootstrap_path": str(bootstrap_json_path),
            "export_path": str(export_path),
            "manual_guides_path": str(manual_guides_path),
            "manual_guides_report_path": str(manual_guides_report_path),
            "run_count": len(run_summaries),
            "failed_query_count": len(failed_queries),
            "dataset_count": len(aggregated_datasets),
        }

    @staticmethod
    def _dataset_key(dataset: dict[str, Any]) -> str:
        canonical_url = str(dataset.get("canonical_url", "")).strip().lower()
        if canonical_url:
            return f"url::{canonical_url}"
        title = str(dataset.get("title", "")).strip().lower()
        return f"title::{title}"

    @staticmethod
    def _build_report(
        *,
        bootstrap_id: str,
        generated_at: str,
        run_summaries: list[dict[str, Any]],
        failed_queries: list[dict[str, str]],
        datasets: list[dict[str, Any]],
        bootstrap_path: str,
        manual_guides_count: int,
        manual_guides_mode: str,
        manual_guides_path: str,
        manual_guides_report_path: str,
        llm_mode: str,
        llm_model: str,
    ) -> str:
        lines = [
            f"# Inicializacao Real em Larga Escala - {bootstrap_id}",
            "",
            f"- Gerado em: `{generated_at}`",
            f"- Queries tentadas: `{len(run_summaries) + len(failed_queries)}`",
            f"- Runs executados: `{len(run_summaries)}`",
            f"- Queries com falha: `{len(failed_queries)}`",
            f"- Datasets agregados: `{len(datasets)}`",
            f"- Guias manuais consolidados: `{manual_guides_count}`",
            f"- Modo dos guias manuais: `{manual_guides_mode}`",
            f"- Modo LLM configurado: `{llm_mode}`",
            f"- Modelo LLM configurado: `{llm_model}`",
            "",
            "## Artefatos",
            "",
            f"- Bootstrap JSON: `{bootstrap_path}`",
            f"- Consolidado manual JSON: `{manual_guides_path}`",
            f"- Consolidado manual Markdown: `{manual_guides_report_path}`",
            "",
            "## Runs",
        ]

        for item in run_summaries:
            lines.append(
                f"- `{item['run_id']}` | datasets={item['dataset_count']} | query=`{item['query']}`"
            )

        lines.extend(["", "## Falhas"])
        if not failed_queries:
            lines.append("- Nenhuma falha de query nesta inicializacao.")
        else:
            for item in failed_queries:
                lines.append(
                    f"- query=`{item['query']}` | erro={item['error_type']} | detalhe=`{item['error_message']}`"
                )

        lines.extend(["", "## Datasets agregados"])
        if not datasets:
            lines.append("- Nenhum dataset agregado nesta inicializacao.")
        else:
            for item in datasets[:15]:
                lines.append(
                    f"- `{item['dataset_id']}` | **{item.get('title', 'sem titulo')}** "
                    f"| score={item.get('relevance_score', 0.0)} "
                    f"| ocorrencias={item.get('bootstrap_occurrences', 0)}"
                )

        return "\n".join(lines)
