from src.agents.dataset_discovery_agent import DatasetDiscoveryAgent
from src.schemas.records import WebResearchResultRecord
from src.schemas.settings import PipelineSettings


def test_dataset_discovery_consolidates_duplicates_with_evidence() -> None:
    agent = DatasetDiscoveryAgent()
    context = {
        "settings": PipelineSettings(query="rio tiete", limit=10),
        "expanded_queries": [{"query": "hidrologia rio tiete"}],
        "web_research_results": [
            WebResearchResultRecord(
                source_id="src-hidroweb",
                source_title="Hidroweb",
                source_type="primary_data_portal",
                source_url="https://www.snirh.gov.br/hidroweb",
                publisher_or_org="ANA",
                dataset_names_mentioned=["Series historicas hidrologicas", "Series historicas hidrologicas"],
                variables_mentioned=["vazao"],
                geographic_scope="Brasil",
                relevance_to_100k="alto",
                evidence_notes="Series por estacao.",
                search_terms_extracted=["hidrologia"],
                search_profiles=["monitoring_sources"],
                research_tracks=["n1_clima_hidrologia"],
                target_intent="dataset_discovery",
                citations=["https://www.snirh.gov.br/hidroweb"],
                confidence=0.9,
            ),
            WebResearchResultRecord(
                source_id="src-paper",
                source_title="Artigo academico",
                source_type="academic_literature",
                source_url="https://example.org/paper",
                publisher_or_org="Revista X",
                dataset_names_mentioned=["Series historicas hidrologicas"],
                variables_mentioned=["vazao", "chuva"],
                geographic_scope="Tiete",
                relevance_to_100k="alto",
                evidence_notes="Cita o uso de series hidrologicas.",
                search_terms_extracted=["series historicas"],
                search_profiles=["academic_knowledge"],
                research_tracks=["n4_series_temporais_tendencias"],
                target_intent="academic_knowledge",
                citations=["https://example.org/paper"],
                confidence=0.7,
            ),
        ],
    }

    result = agent.run(context)
    candidates = result["dataset_candidates"]

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.evidence_count == 3
    assert set(candidate.source_ids) == {"src-hidroweb", "src-paper"}
    assert candidate.accessibility == "mixed"
    assert candidate.verifiability_status == "partially_verifiable"
    assert "academic" in candidate.mention_origins
    assert "primary" in candidate.mention_origins
    assert len(candidate.source_mentions) == 3
    assert set(candidate.research_tracks) == {"n1_clima_hidrologia", "n4_series_temporais_tendencias"}
    assert set(candidate.target_intents) == {"dataset_discovery", "academic_knowledge"}


def test_dataset_discovery_marks_literature_only_as_cited() -> None:
    agent = DatasetDiscoveryAgent()
    context = {
        "settings": PipelineSettings(query="rio tiete", limit=10),
        "expanded_queries": [],
        "web_research_results": [
            WebResearchResultRecord(
                source_id="src-academic",
                source_title="Revisao sistematica",
                source_type="academic_literature",
                source_url="https://example.org/review",
                publisher_or_org="Universidade",
                dataset_names_mentioned=["Base de sedimentos do Medio Tiete"],
                variables_mentioned=["sedimentos"],
                geographic_scope="Tiete",
                relevance_to_100k="medio",
                evidence_notes="Base mencionada sem link direto de download.",
                search_terms_extracted=["sedimentos"],
                search_profiles=["academic_knowledge"],
                research_tracks=["n4_materia_organica_cdom"],
                target_intent="academic_knowledge",
                citations=["https://example.org/review"],
                confidence=0.6,
            )
        ],
    }

    result = agent.run(context)
    candidate = result["dataset_candidates"][0]

    assert candidate.accessibility == "literature_citation"
    assert candidate.verifiability_status == "cited_not_directly_accessible"
    assert candidate.source_mentions[0]["mention_type"] == "literature_citation"
    assert result["preliminary_catalog"][0]["verifiability_status"] == "cited_not_directly_accessible"
