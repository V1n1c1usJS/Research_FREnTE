from src.agents.relevance_agent import RelevanceAgent
from src.schemas.records import DatasetRecord, PerplexityResearchContextRecord


def _build_dataset(
    title: str,
    variables: list[str],
    themes: list[str],
    spatial: str,
    confidence: float,
    source_class: str = "analytical_data_source",
) -> DatasetRecord:
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
        provenance=[
            {
                "source_id": "src-test",
                "source_type": "primary_data_portal",
                "source_url": "https://example.org",
                "evidence": "ok",
            }
        ],
        source_class=source_class,
        source_roles=["data_provider"] if source_class == "analytical_data_source" else ["scientific_evidence"],
        data_extractability="high" if source_class == "analytical_data_source" else "low",
        historical_records_available=True if source_class == "analytical_data_source" else None,
        structured_export_available=True if source_class == "analytical_data_source" else None,
        scientific_value="medium" if source_class == "analytical_data_source" else "high",
        recommended_pipeline_use=(
            ["direct_analytics_ingestion"]
            if source_class == "analytical_data_source"
            else ["methodological_grounding", "dataset_discovery_from_citations"]
        ),
    )


def _master_context() -> PerplexityResearchContextRecord:
    return PerplexityResearchContextRecord(
        context_id="ctx-test",
        article_goal="Estudar impactos antropicos em sistema aquatico.",
        geographic_scope=["Rio Tiete", "Reservatorio de Jupia", "Sao Paulo", "Tres Lagoas"],
        thematic_axes=["hydrology", "water quality", "sanitation", "environmental response"],
        preferred_sources=[],
        expected_outputs=[],
        exclusions=[],
        notes=[],
    )


def test_relevance_agent_weighted_score_and_priority() -> None:
    agent = RelevanceAgent()
    strong = _build_dataset(
        title="Series hidrologicas Rio Tiete Reservatorio de Jupia",
        variables=["streamflow", "water quality", "wastewater"],
        themes=["hydrology-water-quality", "sanitation-waste"],
        spatial="Rio Tiete e conexao com Reservatorio de Jupia (Sao Paulo -> Tres Lagoas)",
        confidence=0.9,
    )
    weak = _build_dataset(
        title="Indicadores genericos",
        variables=["demografia"],
        themes=["unclassified"],
        spatial="Brasil",
        confidence=0.3,
    )

    result = agent.run({"datasets": [strong, weak], "perplexity_master_context": _master_context()})
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


def test_relevance_agent_scientific_source_methodological_value() -> None:
    agent = RelevanceAgent()
    scientific = _build_dataset(
        title="Revisao sistematica sobre qualidade da agua no Rio Tiete",
        variables=["water quality", "organic matter"],
        themes=["hydrology-water-quality"],
        spatial="Rio Tiete",
        confidence=0.8,
        source_class="scientific_knowledge_source",
    )
    analytical = _build_dataset(
        title="Painel analitico geral",
        variables=["streamflow"],
        themes=["hydrology-water-quality"],
        spatial="Rio Tiete",
        confidence=0.8,
        source_class="analytical_data_source",
    )

    result = agent.run({"datasets": [scientific, analytical], "perplexity_master_context": _master_context()})["datasets"]
    scientific_scored = [d for d in result if d.source_class == "scientific_knowledge_source"][0]
    assert scientific_scored.relevance_breakdown["criterion_scores"]["data_readiness"] >= 0.6
