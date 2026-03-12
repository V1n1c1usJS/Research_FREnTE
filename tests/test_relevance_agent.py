from src.agents.relevance_agent import RelevanceAgent
from src.schemas.records import DatasetRecord


def _build_dataset(title: str, variables: list[str], themes: list[str], spatial: str, confidence: float) -> DatasetRecord:
    return DatasetRecord(
        dataset_id="norm-x",
        title=title,
        description="Dataset de teste",
        source_id="src-test",
        source_name="TEST",
        source_url="https://example.org/dataset",
        canonical_url="https://example.org/dataset",
        entity_type="dataset",
        spatial_coverage=spatial,
        update_frequency="mensal",
        formats=["csv"],
        variables_normalized=variables,
        themes_normalized=themes,
        confidence=confidence,
        evidence_origin=["https://example.org/dataset"],
        methodological_notes=["nota 1", "nota 2"],
        provenance=[{"source_id": "src-test", "source_type": "primary_data_portal", "source_url": "https://example.org", "evidence": "ok"}],
    )


def test_relevance_agent_weighted_score_and_priority() -> None:
    agent = RelevanceAgent()
    strong = _build_dataset(
        title="Séries Hidrológicas Rio Tietê Reservatório de Jupiá",
        variables=["streamflow", "water quality", "wastewater"],
        themes=["hydrology-water-quality", "sanitation-waste"],
        spatial="Rio Tietê e conexão com Reservatório de Jupiá (São Paulo -> Três Lagoas)",
        confidence=0.9,
    )
    weak = _build_dataset(
        title="Indicadores genéricos",
        variables=["demografia"],
        themes=["unclassified"],
        spatial="Brasil",
        confidence=0.3,
    )

    result = agent.run({"datasets": [strong, weak]})
    scored = result["datasets"]

    assert scored[0].relevance_score > scored[1].relevance_score
    assert scored[0].priority in {"critical", "high"}
    assert scored[1].priority in {"low", "discard", "medium"}

    for item in scored:
        breakdown = item.relevance_breakdown
        assert "weights" in breakdown
        assert "criterion_scores" in breakdown
        assert "category_scores" in breakdown
        assert set(breakdown["category_scores"].keys()) == {
            "anthropic_pressure",
            "physical_context",
            "environmental_response",
        }
