"""Pipeline de coleta operacional para dados ambientais priorizados."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence
from uuid import uuid4

from src.connectors.operational_dataset_collector import (
    DEFAULT_TIETE_BBOX,
    OperationalDatasetCollector,
)
from src.schemas.records import OperationalCollectionRunRecord
from src.utils.io import ensure_dir, write_catalog_csv, write_json, write_markdown


class OperationalDatasetCollectionPipeline:
    """Executa a coleta bruta e registra destinos de staging/analytic para EDA."""

    def __init__(
        self,
        *,
        target_ids: Sequence[str],
        year_start: int,
        year_end: int,
        bbox: tuple[float, float, float, float] = DEFAULT_TIETE_BBOX,
        bdqueimadas_series: str = "todosats",
        collector: OperationalDatasetCollector | None = None,
    ) -> None:
        self.target_ids = list(target_ids)
        self.year_start = year_start
        self.year_end = year_end
        self.bbox = bbox
        self.bdqueimadas_series = bdqueimadas_series
        self.collector = collector or OperationalDatasetCollector()

    def execute(self) -> dict[str, Any]:
        run_id = f"operational-collect-{uuid4().hex[:8]}"
        run_dir = Path("data") / "runs" / run_id
        generated_at = datetime.now(timezone.utc)

        for subdir in ("config", "collection", "processing", "reports"):
            ensure_dir(run_dir / subdir)

        options = {
            "target_ids": self.target_ids,
            "year_start": self.year_start,
            "year_end": self.year_end,
            "bbox": {
                "min_lon": self.bbox[0],
                "min_lat": self.bbox[1],
                "max_lon": self.bbox[2],
                "max_lat": self.bbox[3],
            },
            "bdqueimadas_series": self.bdqueimadas_series,
        }
        write_json(run_dir / "config" / "collection-options.json", options)

        targets = self.collector.collect(
            run_dir=run_dir,
            target_ids=self.target_ids,
            year_start=self.year_start,
            year_end=self.year_end,
            bbox=self.bbox,
            bdqueimadas_series=self.bdqueimadas_series,
        )
        write_json(
            run_dir / "processing" / "01-collection-targets.json",
            [target.model_dump(mode="json") for target in targets],
        )

        manifest = OperationalCollectionRunRecord(
            run_id=run_id,
            generated_at=generated_at,
            target_ids=self.target_ids,
            target_count=len(targets),
            collected_count=sum(1 for item in targets if item.collection_status == "collected"),
            partial_count=sum(1 for item in targets if item.collection_status == "partial"),
            blocked_count=sum(1 for item in targets if item.collection_status == "blocked"),
            error_count=sum(1 for item in targets if item.collection_status == "error"),
            targets=targets,
        )
        manifest_path = run_dir / "manifest.json"
        write_json(manifest_path, manifest.model_dump(mode="json"))

        report_path = run_dir / "reports" / f"{run_id}.md"
        write_markdown(report_path, self._build_markdown_report(manifest))

        csv_rows = [
            {
                "target_id": item.target_id,
                "source_name": item.source_name,
                "dataset_name": item.dataset_name,
                "collection_status": item.collection_status,
                "access_type": item.access_type,
                "requires_auth": item.requires_auth,
                "year_start": item.year_start or "",
                "year_end": item.year_end or "",
                "bbox": item.bbox or "",
                "raw_artifact_count": len(item.raw_artifacts),
                "join_keys": "|".join(item.join_keys),
                "staging_outputs": "|".join(item.staging_outputs),
                "analytic_outputs": "|".join(item.analytic_outputs),
                "blockers": " | ".join(item.blockers),
            }
            for item in targets
        ]
        report_csv_path = run_dir / "reports" / "collection_targets.csv"
        write_catalog_csv(
            report_csv_path,
            csv_rows,
            fieldnames=[
                "target_id",
                "source_name",
                "dataset_name",
                "collection_status",
                "access_type",
                "requires_auth",
                "year_start",
                "year_end",
                "bbox",
                "raw_artifact_count",
                "join_keys",
                "staging_outputs",
                "analytic_outputs",
                "blockers",
            ],
        )

        return {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "manifest_path": str(manifest_path),
            "processing_path": str(run_dir / "processing" / "01-collection-targets.json"),
            "report_path": str(report_path),
            "report_csv_path": str(report_csv_path),
            "target_count": manifest.target_count,
            "collected_count": manifest.collected_count,
            "partial_count": manifest.partial_count,
            "blocked_count": manifest.blocked_count,
            "error_count": manifest.error_count,
        }

    @staticmethod
    def _build_markdown_report(manifest: OperationalCollectionRunRecord) -> str:
        lines = [
            f"# Coleta operacional {manifest.run_id}",
            "",
            f"- Gerado em: {manifest.generated_at.isoformat()}",
            f"- Targets: {manifest.target_count}",
            f"- Coletados: {manifest.collected_count}",
            f"- Parciais: {manifest.partial_count}",
            f"- Bloqueados: {manifest.blocked_count}",
            f"- Erros: {manifest.error_count}",
            "",
        ]
        for target in manifest.targets:
            lines.extend(
                [
                    f"## {target.target_id}",
                    "",
                    f"- Status: {target.collection_status}",
                    f"- Fonte: {target.source_name}",
                    f"- Dataset: {target.dataset_name}",
                    f"- Artefatos brutos: {len(target.raw_artifacts)}",
                    f"- Chaves de juncao: {', '.join(target.join_keys)}",
                    "",
                ]
            )
            if target.blockers:
                lines.append(f"- Bloqueios: {' | '.join(target.blockers)}")
            if target.notes:
                lines.append(f"- Notas: {' | '.join(target.notes)}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"
