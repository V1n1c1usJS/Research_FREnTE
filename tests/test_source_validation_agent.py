from src.agents.source_validation_agent import SourceValidationAgent
from src.schemas.records import IntelligenceSourceRecord, ResearchSourceRecord, WebResearchResultRecord


def test_source_validation_adjusts_contextual_source_with_weak_dataset_signal() -> None:
    agent = SourceValidationAgent()
    context = {
        "categorized_sources": [
            IntelligenceSourceRecord(
                source_id="src-001",
                title="Blog de contexto ambiental",
                url="https://example.org/blog/contexto-ambiental",
                domain="example.org",
                category="secondary_reference",
                source_class="analytical_data_source",
                target_intent="dataset_discovery",
                dataset_signal=True,
                academic_signal=False,
                official_signal=False,
                evidence_count=1,
                snippets=["Menciona um suposto portal com dados, sem acesso claro."],
                dataset_names_mentioned=["Base ambiental citada em contexto"],
                rationale="classificacao inicial por indicios fracos",
            )
        ],
        "sources": [
            ResearchSourceRecord(
                source_id="src-001",
                name="Blog de contexto ambiental",
                base_url="https://example.org/blog/contexto-ambiental",
                source_type="web_result",
                citation="https://example.org/blog/contexto-ambiental",
                query="contextual_search",
                source_class="analytical_data_source",
                source_roles=["data_provider", "context_reference"],
                data_extractability="unknown",
                recommended_pipeline_use=["dataset_discovery_from_source"],
                methodological_note="fonte de contexto coletada na busca",
            )
        ],
        "web_research_results": [
            WebResearchResultRecord(
                source_id="src-001",
                source_title="Blog de contexto ambiental",
                source_type="web_result",
                source_url="https://example.org/blog/contexto-ambiental",
                publisher_or_org="Example Org",
                dataset_names_mentioned=["Base ambiental citada em contexto"],
                variables_mentioned=["qualidade da agua"],
                geographic_scope="not specified",
                relevance_to_100k="sinal fraco de dado",
                evidence_notes="sem exportacao estruturada",
                search_terms_extracted=["contextual_search"],
                citations=["https://example.org/blog/contexto-ambiental"],
                confidence=0.64,
                source_class="analytical_data_source",
                source_roles=["data_provider", "context_reference"],
                data_extractability="unknown",
                recommended_pipeline_use=["dataset_discovery_from_source"],
            )
        ],
    }

    result = agent.run(context)

    validated_source = result["categorized_sources"][0]
    validated_finding = result["web_research_results"][0]
    validation = result["source_validation_log"][0]

    assert validated_source.dataset_signal is False
    assert validated_source.source_class == "scientific_knowledge_source"
    assert validated_finding.dataset_names_mentioned == []
    assert validation.validation_status == "adjusted"
    assert validation.manual_validation_required is True
    assert "contextual_source_with_dataset_signal" in validation.issues
    assert "removed_dataset_signal_from_contextual_source" in validation.adjustments


def test_source_validation_preserves_strong_official_dataset_source() -> None:
    agent = SourceValidationAgent()
    context = {
        "categorized_sources": [
            IntelligenceSourceRecord(
                source_id="src-002",
                title="Portal Nacional de Monitoramento",
                url="https://dados.gov.example/portal",
                domain="dados.gov.example",
                category="official_data_portal",
                source_class="analytical_data_source",
                target_intent="dataset_discovery",
                dataset_signal=True,
                academic_signal=False,
                official_signal=True,
                priority="high",
                evidence_count=3,
                snippets=[
                    "Portal institucional com download em CSV.",
                    "Series historicas e API documentada.",
                ],
                dataset_names_mentioned=["Serie historica de monitoramento"],
                variables_mentioned=["temperatura da agua", "turbidez"],
                rationale="fonte primaria com evidencias consistentes",
            )
        ],
        "sources": [
            ResearchSourceRecord(
                source_id="src-002",
                name="Portal Nacional de Monitoramento",
                base_url="https://dados.gov.example/portal",
                source_type="primary_data_portal",
                citation="https://dados.gov.example/portal",
                query="official_portals",
                source_class="analytical_data_source",
                source_roles=["data_provider", "institutional_context"],
                data_extractability="high",
                structured_export_available=True,
                recommended_pipeline_use=["direct_analytics_ingestion"],
                priority="high",
                methodological_note="fonte coletada com boa evidencia",
            )
        ],
        "web_research_results": [
            WebResearchResultRecord(
                source_id="src-002",
                source_title="Portal Nacional de Monitoramento",
                source_type="primary_data_portal",
                source_url="https://dados.gov.example/portal",
                publisher_or_org="Instituto Nacional de Monitoramento",
                dataset_names_mentioned=["Serie historica de monitoramento"],
                variables_mentioned=["temperatura da agua", "turbidez"],
                geographic_scope="Area de estudo",
                relevance_to_100k="fonte primaria relevante",
                evidence_notes="CSV e API documentada",
                search_terms_extracted=["official_portals"],
                citations=["https://dados.gov.example/portal"],
                confidence=0.78,
                source_class="analytical_data_source",
                source_roles=["data_provider", "institutional_context"],
                data_extractability="high",
                structured_export_available=True,
                recommended_pipeline_use=["direct_analytics_ingestion"],
            )
        ],
    }

    result = agent.run(context)

    validated_source = result["categorized_sources"][0]
    validation = result["source_validation_log"][0]

    assert validated_source.category == "official_data_portal"
    assert validated_source.dataset_signal is True
    assert validation.validation_status == "validated"
    assert validation.manual_validation_required is False
    assert validation.adjustments == []
    assert result["source_validation_meta"]["status_summary"]["validated"] == 1
