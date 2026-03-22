from src.agents.perplexity_source_categorization_agent import PerplexitySourceCategorizationAgent
from src.schemas.records import (
    PerplexityLinkRecord,
    PerplexityResearchContextRecord,
    PerplexitySearchSessionRecord,
)


class FakeCategorizationLLM:
    provider = "openai"
    model = "gpt-4.1-nano"

    def generate_json(self, *, system_prompt: str, user_prompt: str, max_output_tokens=None, temperature=None):
        assert system_prompt
        assert "Classifique UMA fonte coletada via Perplexity" in user_prompt
        return {
            "canonical_title": "Portal Nacional de Monitoramento Ambiental",
            "category": "official_data_portal",
            "publisher_or_org": "Instituto Nacional de Monitoramento",
            "dataset_signal": True,
            "academic_signal": False,
            "official_signal": True,
            "priority": "high",
            "dataset_names_mentioned": ["Serie historica de monitoramento ambiental"],
            "variables_mentioned": ["temperatura da agua", "turbidez"],
            "source_roles": ["data_provider", "institutional_context"],
            "data_extractability": "high",
            "scientific_value": "medium",
            "recommended_pipeline_use": ["direct_analytics_ingestion"],
            "article_value": "high",
            "historical_records_available": True,
            "structured_export_available": True,
            "rationale": "Fonte institucional primaria com oferta de series historicas e exportacao estruturada.",
        }


def test_source_categorization_can_classify_unknown_domain_via_llm() -> None:
    agent = PerplexitySourceCategorizationAgent(llm_connector=FakeCategorizationLLM())
    sessions = [
        PerplexitySearchSessionRecord(
            query_id="q-01",
            query_text="monitoramento ambiental e series historicas",
            search_profile="official_portals",
            target_intent="dataset_discovery",
            research_track="monitoring_and_measurements",
            chat_label="chat-monitoramento",
            research_question="Quais fontes trazem monitoramento recorrente?",
            answer_text="Portal novo citado com exportacao e series historicas.",
            links=[
                PerplexityLinkRecord(
                    title="Plataforma de monitoramento",
                    url="https://dados.monitoramento-ambiental.example/portal",
                    domain="dados.monitoramento-ambiental.example",
                    snippet="Portal institucional com serie historica, exportacao e API.",
                )
            ],
        )
    ]
    context = {
        "perplexity_master_context": PerplexityResearchContextRecord(
            context_id="ctx-001",
            article_goal="Estudar fontes ambientais para um artigo.",
            geographic_scope=["Area de estudo"],
            thematic_axes=["monitoramento ambiental", "series temporais"],
            preferred_sources=["portais oficiais"],
            expected_outputs=["links diretos", "datasets"],
            exclusions=[],
            notes=[],
        ),
        "perplexity_sessions": sessions,
    }

    result = agent.run(context)
    source = result["categorized_sources"][0]
    finding = result["web_research_results"][0]

    assert result["perplexity_categorization_meta"]["execution_mode"] == "llm"
    assert source.category == "official_data_portal"
    assert source.official_signal is True
    assert source.dataset_signal is True
    assert source.title == "Portal Nacional de Monitoramento Ambiental"
    assert result["sources"][0].research_tracks == ["monitoring_and_measurements"]
    assert result["sources"][0].target_intent == "dataset_discovery"
    assert finding.source_class == "analytical_data_source"
    assert finding.research_tracks == ["monitoring_and_measurements"]
    assert "temperatura da agua" in finding.variables_mentioned
