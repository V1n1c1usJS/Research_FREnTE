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

    def execute(self) -> dict[str, str | int]:
        init_dir = Path("data/initializations/perplexity-intel-test")
        init_dir.mkdir(parents=True, exist_ok=True)
        report_path = Path("reports/perplexity-intel-test.md")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("# report", encoding="utf-8")
        intelligence_path = init_dir / "10_intelligence_payload.json"
        intelligence_path.write_text(
            json.dumps(
                {
                    "research_id": "perplexity-intel-test",
                    "datasets": [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        master_context_path = init_dir / "00_master-context.json"
        master_context_path.write_text(
            json.dumps({"article_goal": self.base_query}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        sources_csv_path = Path("reports/perplexity-intel-test-sources.csv")
        sources_csv_path.write_text("source_id,title\n", encoding="utf-8")
        datasets_csv_path = Path("reports/perplexity-intel-test-datasets.csv")
        datasets_csv_path.write_text("dataset_id,title\n", encoding="utf-8")

        return {
            "research_id": "perplexity-intel-test",
            "master_context_path": str(master_context_path),
            "report_path": str(report_path),
            "sources_csv_path": str(sources_csv_path),
            "datasets_csv_path": str(datasets_csv_path),
            "intelligence_path": str(intelligence_path),
            "categorized_source_count": 3,
            "dataset_candidate_count": 2,
            "dataset_count": 1,
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
