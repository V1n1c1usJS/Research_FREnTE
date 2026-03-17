import json
from pathlib import Path

from src.pipelines.real_initialization_pipeline import RealInitializationPipeline
from src.schemas.settings import PipelineSettings


def test_real_initialization_pipeline_aggregates_runs_and_writes_outputs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    class FakePipeline:
        counter = 0

        def __init__(self, settings: PipelineSettings) -> None:
            self.settings = settings

        def execute(self) -> dict[str, str | int]:
            FakePipeline.counter += 1
            run_id = f"run-fake-{FakePipeline.counter:02d}"
            run_dir = tmp_path / "data" / "runs" / run_id
            run_dir.mkdir(parents=True, exist_ok=True)

            datasets = [
                {
                    "dataset_id": f"norm-{FakePipeline.counter:03d}",
                    "title": "Hidroweb",
                    "canonical_url": "https://www.snirh.gov.br/hidroweb",
                    "source_name": "ANA",
                    "source_url": "https://www.snirh.gov.br/hidroweb",
                    "relevance_score": 0.9 - (FakePipeline.counter * 0.1),
                    "priority": "high",
                    "access_level": "portal",
                }
            ]
            if FakePipeline.counter == 2:
                datasets.append(
                    {
                        "dataset_id": "norm-999",
                        "title": "MapBiomas",
                        "canonical_url": "https://mapbiomas.org",
                        "source_name": "MapBiomas",
                        "source_url": "https://mapbiomas.org",
                        "relevance_score": 0.88,
                        "priority": "high",
                        "access_level": "download_manual",
                    }
                )

            catalog_payload = {
                "run_id": run_id,
                "dataset_count": len(datasets),
                "datasets": datasets,
                "sources": [],
            }
            (run_dir / "catalog.json").write_text(
                json.dumps(catalog_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            reports_dir = tmp_path / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            (reports_dir / f"{run_id}.md").write_text("# report", encoding="utf-8")

            return {
                "run_id": run_id,
                "report_path": str(reports_dir / f"{run_id}.md"),
                "catalog_path": str(run_dir / "catalog.json"),
                "export_path": str(reports_dir / f"{run_id}.csv"),
                "dataset_count": len(datasets),
            }

    pipeline = RealInitializationPipeline(
        limit_per_run=3,
        web_timeout_seconds=4.0,
        max_queries=2,
        queries=["query-1", "query-2"],
        pipeline_factory=FakePipeline,
    )

    result = pipeline.execute()

    assert result["run_count"] == 2
    assert result["dataset_count"] == 2
    assert Path(result["bootstrap_path"]).exists()
    assert Path(result["report_path"]).exists()
    assert Path(result["export_path"]).exists()
    assert Path(result["manual_guides_path"]).exists()
    assert Path(result["manual_guides_report_path"]).exists()

    payload = json.loads(Path(result["bootstrap_path"]).read_text(encoding="utf-8"))
    assert payload["dataset_count"] == 2
    assert payload["run_count"] == 2
    assert payload["manual_guides_count"] == 2
    assert payload["manual_guides_mode"] == "discovered_datasets"

    hidroweb = [item for item in payload["datasets"] if item["canonical_url"] == "https://www.snirh.gov.br/hidroweb"][0]
    assert hidroweb["bootstrap_occurrences"] == 2
    assert hidroweb["bootstrap_queries"] == ["query-1", "query-2"]

    manual_guides = json.loads(Path(result["manual_guides_path"]).read_text(encoding="utf-8"))
    guide_keys = {item["guide_key"] for item in manual_guides}
    assert {"hidroweb", "mapbiomas"}.issubset(guide_keys)
    hidroweb_guide = [item for item in manual_guides if item["guide_key"] == "hidroweb"][0]
    assert hidroweb_guide["validated_via_browser"] is True
    assert hidroweb_guide["validated_via_mcp"] is False
    assert "download_or_export_path" in hidroweb_guide
    assert "available_formats" in hidroweb_guide
    manual_guide_md = Path(result["manual_guides_report_path"]).read_text(encoding="utf-8")
    assert "Consolidado de Pesquisa Manual" in manual_guide_md
    assert "Passo a passo validado" in manual_guide_md
    assert "Validado em browser real" in manual_guide_md


def test_real_initialization_pipeline_continues_after_query_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    class FlakyPipeline:
        counter = 0

        def __init__(self, settings: PipelineSettings) -> None:
            self.settings = settings

        def execute(self) -> dict[str, str | int]:
            FlakyPipeline.counter += 1
            if FlakyPipeline.counter == 1:
                raise RuntimeError("temporary upstream failure")

            run_id = "run-ok-02"
            run_dir = tmp_path / "data" / "runs" / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            catalog_payload = {
                "run_id": run_id,
                "dataset_count": 1,
                "datasets": [
                    {
                        "dataset_id": "norm-002",
                        "title": "MapBiomas",
                        "canonical_url": "https://mapbiomas.org",
                        "source_name": "MapBiomas",
                        "source_url": "https://mapbiomas.org",
                        "relevance_score": 0.88,
                        "priority": "high",
                        "access_level": "download_manual",
                    }
                ],
                "sources": [],
            }
            (run_dir / "catalog.json").write_text(
                json.dumps(catalog_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            reports_dir = tmp_path / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            (reports_dir / f"{run_id}.md").write_text("# report", encoding="utf-8")

            return {
                "run_id": run_id,
                "report_path": str(reports_dir / f"{run_id}.md"),
                "catalog_path": str(run_dir / "catalog.json"),
                "export_path": str(reports_dir / f"{run_id}.csv"),
                "dataset_count": 1,
            }

    pipeline = RealInitializationPipeline(
        max_queries=2,
        queries=["query-1", "query-2"],
        pipeline_factory=FlakyPipeline,
    )

    result = pipeline.execute()

    assert result["run_count"] == 1
    assert result["failed_query_count"] == 1
    payload = json.loads(Path(result["bootstrap_path"]).read_text(encoding="utf-8"))
    assert payload["attempted_query_count"] == 2
    assert payload["failed_query_count"] == 1
    assert payload["failed_queries"][0]["query"] == "query-1"
    assert Path(result["manual_guides_path"]).exists()
    report = Path(result["report_path"]).read_text(encoding="utf-8")
    assert "temporary upstream failure" in report


def test_real_initialization_pipeline_writes_header_only_csv_when_empty(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    class EmptyPipeline:
        counter = 0

        def __init__(self, settings: PipelineSettings) -> None:
            self.settings = settings

        def execute(self) -> dict[str, str | int]:
            EmptyPipeline.counter += 1
            run_id = f"run-empty-{EmptyPipeline.counter:02d}"
            run_dir = tmp_path / "data" / "runs" / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            catalog_payload = {
                "run_id": run_id,
                "dataset_count": 0,
                "datasets": [],
                "sources": [],
            }
            (run_dir / "catalog.json").write_text(
                json.dumps(catalog_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            reports_dir = tmp_path / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            (reports_dir / f"{run_id}.md").write_text("# report", encoding="utf-8")

            return {
                "run_id": run_id,
                "report_path": str(reports_dir / f"{run_id}.md"),
                "catalog_path": str(run_dir / "catalog.json"),
                "export_path": str(reports_dir / f"{run_id}.csv"),
                "dataset_count": 0,
            }

    pipeline = RealInitializationPipeline(
        max_queries=1,
        queries=["query-1"],
        pipeline_factory=EmptyPipeline,
    )

    result = pipeline.execute()

    export_path = Path(result["export_path"])
    assert export_path.exists()
    csv_text = export_path.read_text(encoding="utf-8")
    assert csv_text.startswith("dataset_id,title,canonical_url")

    manual_guides = json.loads(Path(result["manual_guides_path"]).read_text(encoding="utf-8"))
    assert len(manual_guides) == 6
    guide_keys = {item["guide_key"] for item in manual_guides}
    assert {"hidroweb", "mapbiomas", "sidra", "snis", "inpe_queimadas", "scielo"} == guide_keys

    payload = json.loads(Path(result["bootstrap_path"]).read_text(encoding="utf-8"))
    assert payload["manual_guides_mode"] == "validated_seed_portals"
