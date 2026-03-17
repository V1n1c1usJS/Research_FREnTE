from datetime import datetime, timezone

import src.agents.orchestrator_agent as orchestrator_module
from src.agents.orchestrator_agent import OrchestratorAgent
from src.agents.query_expansion_agent import QueryExpansionAgent
from src.agents.report_agent import ReportAgent
from src.agents.research_scout_agent import ResearchScoutAgent
from src.schemas.records import PipelineRunMetadata, WebResearchResultRecord
from src.schemas.settings import PipelineSettings


class FakeJSONLLMConnector:
    provider = "openai"
    model = "gpt-4.1-nano"

    def generate_json(self, *, system_prompt: str, user_prompt: str, max_output_tokens=None, temperature=None):
        assert system_prompt
        return {
            "variables": ["vazao", "qualidade da agua"],
            "generated_queries": ["rio tiete vazao historica", "rio tiete qualidade da agua dataset"],
            "expansions": [
                {
                    "base_term": "hidrologia",
                    "synonyms": ["streamflow", "river flow"],
                    "technical_terms": ["discharge"],
                    "variable_aliases": ["vazao"],
                    "methodological_expressions": ["time-series hydrology"],
                    "generated_queries": ["hidrologia rio tiete series historicas"],
                }
            ],
        }


class FakeScoutLLMConnector:
    provider = "openai"
    model = "gpt-4.1-nano"

    def generate_json(self, *, system_prompt: str, user_prompt: str, max_output_tokens=None, temperature=None):
        assert system_prompt
        assert "triagem de links e fontes" in user_prompt
        return {
            "follow_up_terms": ["rio tiete hidrologia portal oficial"],
            "evaluations": [
                {
                    "source_id": "src-001",
                    "keep": True,
                    "dataset_names_mentioned": ["Series hidrologicas oficiais"],
                    "variables_mentioned": ["vazao", "nivel"],
                    "publisher_or_org": "ANA",
                    "rationale": "Portal oficial com forte aderencia hidrologica.",
                }
            ],
        }


class FakeGroqConnector:
    provider = "groq"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float,
        max_output_tokens: int,
        temperature: float,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature


def test_query_expansion_agent_uses_llm_when_available() -> None:
    settings = PipelineSettings(query="rio tiete", limit=10, dry_run=False)
    findings = [
        WebResearchResultRecord(
            source_id="src-001",
            source_title="Hidroweb",
            source_type="primary_data_portal",
            source_url="https://www.snirh.gov.br/hidroweb",
            publisher_or_org="ANA",
            dataset_names_mentioned=["Series hidrologicas"],
            variables_mentioned=["vazao", "nivel"],
            geographic_scope="Brasil",
            relevance_to_100k="alta",
            evidence_notes="fonte oficial",
        )
    ]

    result = QueryExpansionAgent(llm_connector=FakeJSONLLMConnector()).run(
        {
            "settings": settings,
            "web_research_results": findings,
        }
    )

    assert result["query_expansion_meta"]["execution_mode"] == "llm"
    assert result["query_expansion_meta"]["provider"] == "openai"
    assert result["query_expansions"][0].base_term == "hidrologia"
    assert "rio tiete qualidade da agua dataset" in [item["query"] for item in result["expanded_queries"]]


def test_research_scout_agent_uses_llm_for_source_triage() -> None:
    settings = PipelineSettings(query="rio tiete", limit=10, dry_run=False, web_research_mode="real")
    findings = [
        WebResearchResultRecord(
            source_id="src-001",
            source_title="Hidroweb",
            source_type="web_result",
            source_url="https://www.snirh.gov.br/hidroweb",
            publisher_or_org="",
            dataset_names_mentioned=[],
            variables_mentioned=[],
            geographic_scope="Brasil",
            relevance_to_100k="alta",
            evidence_notes="portal oficial hidrologia rio tiete",
            confidence=0.32,
        )
    ]

    class StaticConnector:
        def search(self, query: str, search_terms: list[str], limit: int = 20):
            return findings

    result = ResearchScoutAgent(
        connector=StaticConnector(),
        web_research_mode="real",
        llm_connector=FakeScoutLLMConnector(),
    ).run({"settings": settings})

    assert result["research_scout_triage_meta"]["execution_mode"] == "llm"
    assert result["research_scout_triage_meta"]["follow_up_terms"] == ["rio tiete hidrologia portal oficial"]
    assert result["web_research_meta"]["triage_execution_mode"] == "llm"
    assert result["web_research_results"]
    first = result["web_research_results"][0]
    assert first.publisher_or_org == "ANA"
    assert "Series hidrologicas oficiais" in first.dataset_names_mentioned
    assert "llm_triage=keep" in first.relevance_to_100k


def test_report_agent_stays_deterministic_even_with_llm_runtime_context() -> None:
    settings = PipelineSettings(query="rio tiete", limit=10, dry_run=False)
    metadata = PipelineRunMetadata(
        run_id="run-test-001",
        mode="run",
        query=settings.query,
        started_at=datetime.now(timezone.utc),
    )

    result = ReportAgent().run(
        {
            "settings": settings,
            "run_metadata": metadata,
            "datasets": [],
            "sources": [],
            "extraction_plan": [],
            "web_research_meta": {},
            "research_scout_triage_meta": {"execution_mode": "llm", "error": None},
            "query_expansion_meta": {"execution_mode": "llm", "error": None},
            "llm_runtime": {
                "requested_mode": "openai",
                "active_provider": "openai",
                "active_model": "gpt-4.1-nano",
                "setup_error": None,
            },
        }
    )

    assert result["report_meta"]["execution_mode"] == "heuristic"
    assert "Scout triage via" in result["report_markdown"]
    assert "relatorio final permanece deterministico" in result["report_markdown"].lower()


def test_orchestrator_uses_groq_connector_when_requested(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(orchestrator_module, "GroqResponsesConnector", FakeGroqConnector)

    orchestrator = OrchestratorAgent(
        PipelineSettings(
            query="rio tiete",
            limit=10,
            dry_run=False,
            llm_mode="groq",
        )
    )

    assert orchestrator.llm_connector is not None
    assert orchestrator.llm_connector.provider == "groq"
    assert orchestrator.llm_connector.model == "groq/compound-mini"
    llm_agents = [agent.name for agent in orchestrator.agents if getattr(agent, "has_llm", False)]
    assert llm_agents == ["research-scout", "query-expansion"]


def test_orchestrator_auto_mode_falls_back_to_groq_when_only_groq_key_exists(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(orchestrator_module, "GroqResponsesConnector", FakeGroqConnector)

    orchestrator = OrchestratorAgent(
        PipelineSettings(
            query="rio tiete",
            limit=10,
            dry_run=False,
            llm_mode="auto",
        )
    )

    assert orchestrator.llm_connector is not None
    assert orchestrator.llm_connector.provider == "groq"
    assert orchestrator.llm_connector.model == "groq/compound-mini"
