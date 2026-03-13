from src.agents.dataset_discovery_agent import DatasetDiscoveryAgent
from src.schemas.records import WebResearchResultRecord
from src.schemas.settings import PipelineSettings


def test_dataset_discovery_consolidates_duplicates_with_evidence() -> None:
    agent = DatasetDiscoveryAgent()
    context = {
        "settings": PipelineSettings(query="rio tietê", limit=10, dry_run=True),
        "expanded_queries": [{"query": "hidrologia rio tietê"}],
        "web_research_results": [
            WebResearchResultRecord(
                source_id="src-hidroweb",
                source_title="Hidroweb",
                source_type="primary_data_portal",
                source_url="https://www.snirh.gov.br/hidroweb",
                publisher_or_org="ANA",
                dataset_names_mentioned=["Séries históricas hidrológicas", "Series Historicas Hidrologicas"],
                variables_mentioned=["vazão"],
                geographic_scope="Brasil",
                relevance_to_100k="alto",
                evidence_notes="Séries por estação.",
                search_terms_extracted=["hidrologia"],
                citations=["https://www.snirh.gov.br/hidroweb"],
                confidence=0.9,
            ),
            WebResearchResultRecord(
                source_id="src-paper",
                source_title="Artigo acadêmico",
                source_type="academic_literature",
                source_url="https://example.org/paper",
                publisher_or_org="Revista X",
                dataset_names_mentioned=["Séries históricas hidrológicas"],
                variables_mentioned=["vazão", "chuva"],
                geographic_scope="Tietê",
                relevance_to_100k="alto",
                evidence_notes="Cita o uso de séries hidrológicas.",
                search_terms_extracted=["séries históricas"],
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


def test_dataset_discovery_marks_literature_only_as_cited() -> None:
    agent = DatasetDiscoveryAgent()
    context = {
        "settings": PipelineSettings(query="rio tietê", limit=10, dry_run=True),
        "expanded_queries": [],
        "web_research_results": [
            WebResearchResultRecord(
                source_id="src-academic",
                source_title="Revisão sistemática",
                source_type="academic_literature",
                source_url="https://example.org/review",
                publisher_or_org="Universidade",
                dataset_names_mentioned=["Base de sedimentos do Médio Tietê"],
                variables_mentioned=["sedimentos"],
                geographic_scope="Tietê",
                relevance_to_100k="médio",
                evidence_notes="Base mencionada sem link direto de download.",
                search_terms_extracted=["sedimentos"],
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
