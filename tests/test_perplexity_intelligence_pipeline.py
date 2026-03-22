import json
from pathlib import Path

from src.pipelines.perplexity_intelligence_pipeline import PerplexityIntelligencePipeline
from src.schemas.records import PerplexityLinkRecord, PerplexitySearchSessionRecord


def test_perplexity_intelligence_pipeline_writes_artifacts_and_consolidates_sources(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    class FakeCollector:
        def collect(self, query_plan):
            assert len(query_plan) == 4
            return [
                PerplexitySearchSessionRecord(
                    query_id=query_plan[0].query_id,
                    query_text=query_plan[0].query_text,
                    search_profile=query_plan[0].search_profile,
                    target_intent=query_plan[0].target_intent,
                    page_url="https://www.perplexity.ai/search/mock-1",
                    preferred_model="Sonar",
                    selected_model=None,
                    model_selection_blocked=True,
                    model_selection_blocker="Entre para escolher um modelo",
                    answer_text="Hidroweb e MapBiomas aparecem como caminhos fortes para hidrologia e uso da terra.",
                    visible_source_count=4,
                    links=[
                        PerplexityLinkRecord(
                            title="Portal Hidroweb (SNIRH)",
                            url="https://www.snirh.gov.br/hidroweb",
                            domain="www.snirh.gov.br",
                            snippet="Portal oficial com series historicas hidrologicas, vazao, nivel e chuva.",
                        ),
                        PerplexityLinkRecord(
                            title="MapBiomas",
                            url="https://mapbiomas.org/",
                            domain="mapbiomas.org",
                            snippet="Colecoes de uso e cobertura da terra para o Brasil.",
                        ),
                        PerplexityLinkRecord(
                            title="Panorama da Qualidade das Aguas",
                            url="https://www.ana.gov.br/portalpnqa/Publicacao/PANORAMA_DA_QUALIDADE_DAS_AGUAS.pdf",
                            domain="www.ana.gov.br",
                            snippet="Relatorio tecnico institucional sobre qualidade das aguas superficiais.",
                        ),
                    ],
                    blockers=["model_selection:Entre para escolher um modelo"],
                    notes=["links_tab_opened"],
                ),
                PerplexitySearchSessionRecord(
                    query_id=query_plan[1].query_id,
                    query_text=query_plan[1].query_text,
                    search_profile=query_plan[1].search_profile,
                    target_intent=query_plan[1].target_intent,
                    page_url="https://www.perplexity.ai/search/mock-2",
                    preferred_model="Sonar",
                    selected_model=None,
                    model_selection_blocked=False,
                    answer_text="SciELO e Repositorio USP trazem conhecimento academico e estudos aplicados ao Tiete.",
                    visible_source_count=3,
                    links=[
                        PerplexityLinkRecord(
                            title="SciELO Brasil",
                            url="https://www.scielo.br/",
                            domain="www.scielo.br",
                            snippet="Base academica para artigos e estudos sobre qualidade da agua.",
                        ),
                        PerplexityLinkRecord(
                            title="Toxicidade das aguas do Rio Tiete",
                            url="https://repositorio.usp.br/bitstream/handle/BDPI/2262/art.BERNARDI_toxidade_das_aguas_rio_tiete.pdf",
                            domain="repositorio.usp.br",
                            snippet="Estudo academico aplicado ao eixo Pereira Barreto e Tres Lagoas.",
                        ),
                    ],
                    blockers=[],
                    notes=["links_tab_opened"],
                ),
                PerplexitySearchSessionRecord(
                    query_id=query_plan[2].query_id,
                    query_text=query_plan[2].query_text,
                    search_profile=query_plan[2].search_profile,
                    target_intent=query_plan[2].target_intent,
                    page_url="https://www.perplexity.ai/search/mock-3",
                    preferred_model="Sonar",
                    selected_model=None,
                    model_selection_blocked=False,
                    answer_text="Projeto Tiete e monitoramentos complementam a interpretacao institucional.",
                    visible_source_count=2,
                    links=[
                        PerplexityLinkRecord(
                            title="Projeto Tiete IV",
                            url="https://www.sabesp.com.br/site/uploads/file/projeto_tiete/projetotiete_empd.pdf",
                            domain="www.sabesp.com.br",
                            snippet="Documento institucional do Projeto Tiete.",
                        ),
                    ],
                    blockers=[],
                    notes=["links_tab_opened"],
                ),
                PerplexitySearchSessionRecord(
                    query_id=query_plan[3].query_id,
                    query_text=query_plan[3].query_text,
                    search_profile=query_plan[3].search_profile,
                    target_intent=query_plan[3].target_intent,
                    collection_status="error",
                    preferred_model="Sonar",
                    selected_model=None,
                    model_selection_blocked=False,
                    answer_text="",
                    visible_source_count=0,
                    links=[],
                    blockers=["collector_error:TimeoutError"],
                    notes=["tempo esgotado"],
                ),
            ]

    pipeline = PerplexityIntelligencePipeline(
        base_query="impactos humanos no Rio Tiete reservatorios Sao Paulo Tres Lagoas qualidade agua",
        limit=10,
        max_searches=4,
        collector_factory=lambda: FakeCollector(),
    )

    result = pipeline.execute()

    assert result["categorized_source_count"] >= 5
    assert result["validated_source_count"] >= 5
    assert result["dataset_candidate_count"] >= 2
    assert Path(result["intelligence_path"]).exists()
    assert Path(result["report_path"]).exists()
    assert Path(result["sources_csv_path"]).exists()
    assert Path(result["datasets_csv_path"]).exists()

    intelligence_payload = json.loads(Path(result["intelligence_path"]).read_text(encoding="utf-8"))
    assert intelligence_payload["session_count"] == 4
    assert intelligence_payload["collection_meta"]["error_session_count"] == 1
    assert intelligence_payload["collection_meta"]["source_validation_meta"]["validated_source_count"] >= 5
    assert len(intelligence_payload["intelligence"]["track_coverage"]) == 4
    official_titles = {item["title"] for item in intelligence_payload["intelligence"]["official_portals"]}
    assert "Portal Hidroweb (SNIRH)" in official_titles
    academic_titles = {item["title"] for item in intelligence_payload["intelligence"]["academic_sources"]}
    assert "SciELO Brasil" in academic_titles

    raw_sessions = json.loads(
        (tmp_path / "data" / "initializations" / result["research_id"] / "02_raw-sessions.json").read_text(
            encoding="utf-8"
        )
    )
    assert raw_sessions[0]["answer_text"].startswith("Hidroweb e MapBiomas")
    validation_stage = json.loads(
        (tmp_path / "data" / "initializations" / result["research_id"] / "04_source-validation.json").read_text(
            encoding="utf-8"
        )
    )
    assert validation_stage["source_validation_meta"]["validated_source_count"] >= 5

    report = Path(result["report_path"]).read_text(encoding="utf-8")
    assert "Cobertura por trilha" in report
    assert "Validacao das fontes" in report
    assert "Portais e fontes com sinal de dataset" in report
    assert "Conhecimento academico e repositorios" in report

    sources_csv = Path(result["sources_csv_path"]).read_text(encoding="utf-8")
    assert sources_csv.startswith("source_id,title,url,domain")
    assert "validation_status" in sources_csv
