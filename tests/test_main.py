import json
from pathlib import Path

from src.main import run


def test_cli_dry_run_executes() -> None:
    exit_code = run(["dry-run", "--query", "rio tiete", "--limit", "3"])
    assert exit_code == 0


def test_cli_export_from_generated_catalog(tmp_path: Path) -> None:
    run(["dry-run", "--query", "rio tiete", "--limit", "3"])
    catalogs = sorted(Path("data/runs").glob("*/catalog.json"), key=lambda p: p.stat().st_mtime)
    assert catalogs

    output_csv = tmp_path / "catalog.csv"
    exit_code = run(["export", "--catalog", str(catalogs[-1]), "--output", str(output_csv)])

    assert exit_code == 0
    assert output_csv.exists()


def test_dry_run_pipeline_outputs_consistent_mock_structure() -> None:
    run(["dry-run", "--query", "impactos humanos rio tiete", "--limit", "7"])
    latest_run = sorted(Path("data/runs").glob("run-*"), key=lambda p: p.stat().st_mtime)[-1]

    discovery = json.loads((latest_run / "03_dataset-discovery.json").read_text(encoding="utf-8"))
    normalized = json.loads((latest_run / "04_normalization.json").read_text(encoding="utf-8"))
    scored = json.loads((latest_run / "05_relevance.json").read_text(encoding="utf-8"))
    access = json.loads((latest_run / "06_access.json").read_text(encoding="utf-8"))
    plan = json.loads((latest_run / "07_extraction-plan.json").read_text(encoding="utf-8"))
    catalog = json.loads((latest_run / "catalog.json").read_text(encoding="utf-8"))

    assert len(discovery["raw_datasets"]) == 7
    assert len(normalized["datasets"]) == 7
    assert len(scored["datasets"]) == 7
    assert len(access["datasets"]) == 7
    assert len(plan["extraction_plan"]) == 7
    assert catalog["dataset_count"] == 7

    source_names = {item["source_name"] for item in catalog["datasets"]}
    assert {"ANA", "Hidroweb", "MapBiomas"}.issubset(source_names)

    for row in catalog["datasets"]:
        assert 0.0 <= row["relevance_score"] <= 1.0
        assert row["priority"] in {"high", "medium", "low"}
        assert row["methodological_notes"]
