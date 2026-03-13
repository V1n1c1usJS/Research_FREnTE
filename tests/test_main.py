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

    scout = json.loads((latest_run / "01_research-scout.json").read_text(encoding="utf-8"))
    expansion = json.loads((latest_run / "02_query-expansion.json").read_text(encoding="utf-8"))
    discovery = json.loads((latest_run / "03_dataset-discovery.json").read_text(encoding="utf-8"))
    normalized = json.loads((latest_run / "04_normalization.json").read_text(encoding="utf-8"))
    scored = json.loads((latest_run / "05_relevance.json").read_text(encoding="utf-8"))
    access = json.loads((latest_run / "06_access.json").read_text(encoding="utf-8"))
    plan = json.loads((latest_run / "07_extraction-plan.json").read_text(encoding="utf-8"))
    catalog = json.loads((latest_run / "catalog.json").read_text(encoding="utf-8"))

    assert scout["web_research_results"]
    source_types = {item["source_type"] for item in scout["web_research_results"]}
    assert {"primary_data_portal", "academic_literature", "institutional_documentation"}.issubset(
        source_types
    )

    assert expansion["query_expansions"]
    use_land = [item for item in expansion["query_expansions"] if item["base_term"] == "uso da terra"]
    assert use_land
    assert "land use" in use_land[0]["synonyms"]
    assert "land use change" in use_land[0]["synonyms"]

    assert discovery["dataset_candidates"]
    assert discovery["preliminary_catalog"]
    assert discovery["dataset_discovery_report"].startswith("# Dataset Discovery")

    candidate_count = len(discovery["dataset_candidates"])
    normalized_count = len(normalized["datasets"])
    assert candidate_count == 7
    assert 1 <= normalized_count <= candidate_count
    assert len(scored["datasets"]) == normalized_count
    assert len(access["datasets"]) == normalized_count
    assert access["datasets"][0]["access_level"] in {"api", "download_manual", "portal", "documentation", "ogc", "unknown"}
    assert "requires_auth" in access["datasets"][0]
    assert "access_links" in access["datasets"][0]
    assert "documentation_links" in access["datasets"][0]
    assert "extraction_observations" in access["datasets"][0]
    assert len(plan["extraction_plan"]) == normalized_count
    assert catalog["dataset_count"] == normalized_count

    source_names = {item["source_name"] for item in catalog["datasets"]}
    assert {"ANA", "Hidroweb", "MapBiomas"}.issubset(source_names)

    for row in catalog["datasets"]:
        assert 0.0 <= row["relevance_score"] <= 1.0
        assert 0.0 <= row["confidence"] <= 1.0
        assert row["priority"] in {"critical", "high", "medium", "low", "discard"}
        assert row["entity_type"] in {"dataset", "portal", "documentation", "academic_source"}
        assert row["provenance"]
        assert row["canonical_url"]
        assert row["organization_normalized"]
        assert row["variables_normalized"]
        assert row["themes_normalized"]
        assert row["provenance"]
        assert row["methodological_notes"]

    first_candidate = discovery["dataset_candidates"][0]
    assert first_candidate["source_mentions"]
    assert first_candidate["verifiability_status"] in {
        "verifiable",
        "partially_verifiable",
        "cited_not_directly_accessible",
        "evidence_only",
        "needs_manual_validation",
        "unverifiable",
    }


def test_cli_run_accepts_web_mode_flag() -> None:
    exit_code = run(["run", "--query", "rio tiete", "--limit", "2", "--web-mode", "mock", "--web-timeout", "5"])
    assert exit_code == 0


def test_dry_run_forces_mock_mode() -> None:
    run(["dry-run", "--query", "rio tiete", "--limit", "2", "--web-mode", "real"])
    latest_run = sorted(Path("data/runs").glob("run-*"), key=lambda p: p.stat().st_mtime)[-1]
    scout = json.loads((latest_run / "01_research-scout.json").read_text(encoding="utf-8"))
    assert scout["web_research_meta"]["requested_mode"] == "mock"
