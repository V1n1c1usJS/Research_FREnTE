from src.agents.access_agent import AccessAgent
from src.schemas.records import DatasetRecord


def _dataset(title: str, source_url: str, entity_type: str = "dataset", formats: list[str] | None = None) -> DatasetRecord:
    return DatasetRecord(
        dataset_id="norm-test",
        title=title,
        description="desc",
        source_id="src-test",
        source_name="TEST",
        source_url=source_url,
        canonical_url=source_url,
        entity_type=entity_type,
        formats=formats or ["csv"],
        provenance=[
            {
                "source_id": "src-doc",
                "source_type": "institutional_documentation",
                "source_url": "https://example.org/docs",
                "evidence": "doc",
            }
        ],
        evidence_origin=[source_url],
    )


def test_access_agent_classifies_api_and_collects_links() -> None:
    agent = AccessAgent()
    ds = _dataset("API Hidrologica", "https://example.org/api/v1/stations", formats=["json"])

    result = agent.run({"datasets": [ds]})["datasets"][0]

    assert result.access_level == "api"
    assert result.requires_auth is False
    assert result.access_links
    assert "https://example.org/docs" in result.documentation_links
    assert result.extraction_observations


def test_access_agent_marks_documentation_when_not_direct_dataset() -> None:
    agent = AccessAgent()
    ds = _dataset("Relatorio tecnico", "https://example.org/report.pdf", entity_type="documentation", formats=["pdf"])

    result = agent.run({"datasets": [ds]})["datasets"][0]

    assert result.access_level == "documentation"
    assert result.requires_auth is None
    assert any("documentation" in note.lower() or "citations" in note.lower() for note in result.extraction_observations)


def test_access_agent_classifies_generic_analytical_source_without_name_whitelist() -> None:
    agent = AccessAgent()
    ds = _dataset("Painel de monitoramento costeiro", "https://example.org/data/portal")
    ds = ds.model_copy(
        update={
            "source_class": "analytical_data_source",
            "structured_export_available": True,
            "recommended_pipeline_use": ["dataset_discovery_from_source"],
            "formats": ["csv", "json"],
        }
    )

    result = agent.run({"datasets": [ds]})["datasets"][0]

    assert result.access_level == "download_manual"
    assert result.requires_auth is False
