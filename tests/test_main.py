import json
from pathlib import Path

import src.main as main_module
from src.main import run


class FakePerplexityPipeline:
    last_instance = None

    def __init__(
        self,
        *,
        base_query: str,
        limit: int,
        max_searches: int,
        perplexity_api_key: str = "",
        perplexity_max_results: int = 20,
        perplexity_timeout_seconds: float = 60.0,
        master_context_payload=None,
        research_tracks_payload=None,
        llm_mode: str = "auto",
        llm_model: str = "gpt-4.1-nano",
        llm_timeout_seconds: float = 60.0,
        llm_fail_on_error: bool = False,
        firecrawl_api_key: str = "",
        firecrawl_timeout_seconds: float = 60.0,
        skip_collection_guides: bool = False,
    ) -> None:
        FakePerplexityPipeline.last_instance = self
        self.base_query = base_query
        self.limit = limit
        self.max_searches = max_searches
        self.perplexity_api_key = perplexity_api_key
        self.perplexity_max_results = perplexity_max_results
        self.perplexity_timeout_seconds = perplexity_timeout_seconds
        self.master_context_payload = master_context_payload
        self.research_tracks_payload = research_tracks_payload
        self.llm_mode = llm_mode
        self.llm_model = llm_model
        self.llm_timeout_seconds = llm_timeout_seconds
        self.llm_fail_on_error = llm_fail_on_error
        self.firecrawl_api_key = firecrawl_api_key
        self.firecrawl_timeout_seconds = firecrawl_timeout_seconds
        self.skip_collection_guides = skip_collection_guides

    def execute(self) -> dict[str, str | int]:
        run_dir = Path("data/runs/perplexity-intel-test")
        for subdir in ("config", "collection", "processing", "reports"):
            (run_dir / subdir).mkdir(parents=True, exist_ok=True)
        report_path = run_dir / "reports" / "perplexity-intel-test.md"
        report_path.write_text("# report", encoding="utf-8")
        manifest_path = run_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "research_id": "perplexity-intel-test",
                    "ranked_datasets": [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        master_context_path = run_dir / "master-context.json"
        master_context_path.write_text(
            json.dumps({"article_goal": self.base_query}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        sources_csv_path = run_dir / "reports" / "sources.csv"
        sources_csv_path.write_text("rank,url,title\n", encoding="utf-8")
        datasets_csv_path = run_dir / "reports" / "datasets.csv"
        datasets_csv_path.write_text("rank,dataset_name,title\n", encoding="utf-8")

        return {
            "research_id": "perplexity-intel-test",
            "master_context_path": str(master_context_path),
            "report_path": str(report_path),
            "sources_csv_path": str(sources_csv_path),
            "datasets_csv_path": str(datasets_csv_path),
            "intelligence_path": str(manifest_path),
            "filtered_source_count": 3,
            "enriched_dataset_count": 3,
            "ranked_dataset_count": 3,
            "collection_guide_count": 0,
        }


class FakeOperationalCollectionPipeline:
    last_instance = None

    def __init__(
        self,
        *,
        target_ids,
        year_start: int,
        year_end: int,
        bbox,
        bdqueimadas_series: str,
        collector=None,
    ) -> None:
        FakeOperationalCollectionPipeline.last_instance = self
        self.target_ids = list(target_ids)
        self.year_start = year_start
        self.year_end = year_end
        self.bbox = bbox
        self.bdqueimadas_series = bdqueimadas_series
        self.collector = collector

    def execute(self) -> dict[str, str | int]:
        run_dir = Path("data/runs/operational-collect-test")
        for subdir in ("config", "collection", "processing", "reports"):
            (run_dir / subdir).mkdir(parents=True, exist_ok=True)

        manifest_path = run_dir / "manifest.json"
        manifest_path.write_text("{}", encoding="utf-8")
        processing_path = run_dir / "processing" / "01-collection-targets.json"
        processing_path.write_text("[]", encoding="utf-8")
        report_path = run_dir / "reports" / "operational-collect-test.md"
        report_path.write_text("# report", encoding="utf-8")
        report_csv_path = run_dir / "reports" / "collection_targets.csv"
        report_csv_path.write_text("target_id,collection_status\n", encoding="utf-8")

        return {
            "run_id": "operational-collect-test",
            "run_dir": str(run_dir),
            "manifest_path": str(manifest_path),
            "processing_path": str(processing_path),
            "report_path": str(report_path),
            "report_csv_path": str(report_csv_path),
            "target_count": 1,
            "collected_count": 1,
            "partial_count": 0,
            "blocked_count": 0,
            "error_count": 0,
        }


def test_cli_run_executes_perplexity_flow(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "PerplexityIntelligencePipeline", FakePerplexityPipeline)
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")

    exit_code = run(
        [
            "run",
            "--query",
            "fontes de dados oficiais e estudos academicos sobre rio tiete e jupia",
        ]
    )

    assert exit_code == 0
    assert FakePerplexityPipeline.last_instance is not None
    assert FakePerplexityPipeline.last_instance.master_context_payload is not None
    assert FakePerplexityPipeline.last_instance.research_tracks_payload is not None
    assert len(FakePerplexityPipeline.last_instance.research_tracks_payload) >= 5


def test_cli_alias_perplexity_intel_executes(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "PerplexityIntelligencePipeline", FakePerplexityPipeline)
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")

    exit_code = run(
        [
            "perplexity-intel",
            "--query",
            "fontes de dados oficiais e estudos academicos sobre rio tiete e jupia",
            "--max-searches",
            "3",
            "--perplexity-max-results",
            "15",
        ]
    )

    assert exit_code == 0


def test_cli_passes_firecrawl_configuration(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "PerplexityIntelligencePipeline", FakePerplexityPipeline)
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test-key")

    exit_code = run(
        [
            "run",
            "--query",
            "fontes de dados oficiais e estudos academicos sobre rio tiete e jupia",
            "--skip-collection-guides",
        ]
    )

    assert exit_code == 0
    assert FakePerplexityPipeline.last_instance is not None
    assert FakePerplexityPipeline.last_instance.firecrawl_api_key == "fc-test-key"
    assert FakePerplexityPipeline.last_instance.skip_collection_guides is True


def test_cli_export_from_generated_catalog(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(
        json.dumps(
            {
                "datasets": [
                    {
                        "dataset_id": "norm-001",
                        "title": "Hidroweb",
                        "source_name": "ANA",
                        "source_url": "https://www.snirh.gov.br/hidroweb",
                        "relevance_score": 0.9,
                        "access_level": "portal",
                        "priority": "high",
                        "dataset_kind": "dataset",
                        "methodological_notes": ["fonte oficial"],
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    output_csv = tmp_path / "catalog.csv"
    exit_code = run(["export", "--catalog", str(catalog_path), "--output", str(output_csv)])

    assert exit_code == 0
    assert output_csv.exists()


def test_cli_loads_context_and_tracks_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(main_module, "PerplexityIntelligencePipeline", FakePerplexityPipeline)
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")

    context_path = tmp_path / "context.yaml"
    context_path.write_text(
        "\n".join(
            [
                "context_id: ctx-custom",
                "article_goal: Investigar pressao antropica em sistema aquatico costeiro",
                "geographic_scope:",
                "  - Costa norte",
                "thematic_axes:",
                "  - monitoramento ambiental",
                "preferred_sources:",
                "  - portais institucionais",
            ]
        ),
        encoding="utf-8",
    )
    tracks_path = tmp_path / "tracks.json"
    tracks_path.write_text(
        json.dumps(
            [
                {
                    "research_track": "custom_track",
                    "chat_label": "chat-custom",
                    "search_profile": "custom_profile",
                    "target_intent": "dataset_discovery",
                    "research_question": "Quais fontes monitoram a costa norte?",
                    "task_prompt": "Busque datasets e literatura aplicada.",
                    "priority": "high",
                }
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    exit_code = run(
        [
            "run",
            "--query",
            "monitoramento costeiro",
            "--context-file",
            str(context_path),
            "--tracks-file",
            str(tracks_path),
        ]
    )

    assert exit_code == 0
    assert FakePerplexityPipeline.last_instance is not None
    assert FakePerplexityPipeline.last_instance.master_context_payload["context_id"] == "ctx-custom"
    assert FakePerplexityPipeline.last_instance.research_tracks_payload[0]["research_track"] == "custom_track"


def test_cli_collect_operational_executes(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "OperationalDatasetCollectionPipeline", FakeOperationalCollectionPipeline)

    exit_code = run(
        [
            "collect-operational",
            "--target",
            "bdqueimadas_focos_calor",
            "--year-start",
            "2023",
            "--year-end",
            "2024",
            "--bbox",
            "-52.2,-24.0,-45.8,-20.5",
            "--bdqueimadas-series",
            "satref",
        ]
    )

    assert exit_code == 0
    assert FakeOperationalCollectionPipeline.last_instance is not None
    assert FakeOperationalCollectionPipeline.last_instance.target_ids == ["bdqueimadas_focos_calor"]
    assert FakeOperationalCollectionPipeline.last_instance.year_start == 2023
    assert FakeOperationalCollectionPipeline.last_instance.year_end == 2024
    assert FakeOperationalCollectionPipeline.last_instance.bbox == (-52.2, -24.0, -45.8, -20.5)
    assert FakeOperationalCollectionPipeline.last_instance.bdqueimadas_series == "satref"
