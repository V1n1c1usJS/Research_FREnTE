import json
from pathlib import Path

from src.pipelines.perplexity_intelligence_pipeline import PerplexityIntelligencePipeline
from src.schemas.records import (
    CollectionGuide,
    PerplexityLinkRecord,
    PerplexityResearchContextRecord,
    PerplexityResearchTrackRecord,
    PerplexitySearchSessionRecord,
)


def test_compose_chat_prompt_is_specific_and_penalizes_aggregators() -> None:
    prompt = PerplexityIntelligencePipeline._compose_chat_prompt(
        master_context=PerplexityResearchContextRecord(
            context_id="ctx-100k",
            article_goal="Investigar o impacto antropico na materia organica dos reservatorios do Tiete.",
            geographic_scope=[
                "Bacia do Rio Tiete entre Sao Paulo e Tres Lagoas.",
                "Reservatorios de Barra Bonita a Jupia.",
            ],
            thematic_axes=["geomorfologia", "geologia", "solos"],
            preferred_sources=[
                "ANA metadados.snirh.gov.br",
                "USGS EarthExplorer",
                "ASF Alaska",
                "CPRM GeoSGB",
                "EMBRAPA solos",
            ],
            expected_outputs=[
                "links diretos para shapefile e GeoTIFF",
                "paginas primarias de catalogo e download",
            ],
            exclusions=[
                "blogs",
                "tutoriais",
                "paginas agregadoras",
            ],
            notes=[],
        ),
        track=PerplexityResearchTrackRecord(
            research_track="n1_bacia_geomorfologia",
            chat_label="bacia_geomorfologia",
            research_question="Quais datasets geoespaciais existem para delimitar a bacia do Tiete e caracterizar relevo, geologia e solos?",
            task_prompt="Busque ANA ottobacias, USGS SRTM 30m, ALOS PALSAR 12.5m, CPRM GeoSGB e EMBRAPA solos com links primarios de dataset.",
            priority="high",
        ),
    )

    assert "Pergunta principal:" in prompt
    assert "Tarefa especifica:" in prompt
    assert "USGS SRTM 30m" in prompt
    assert "CPRM GeoSGB" in prompt
    assert "Priorize paginas primarias de dataset, catalogo, API ou download direto" in prompt
    assert "Evite: blogs; tutoriais; paginas agregadoras." in prompt
    assert "Nao priorize blogs, tutoriais, rankings de sites, curadorias ou paginas agregadoras" in prompt


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
                    research_track=query_plan[0].research_track,
                    collection_method="search_api",
                    request_endpoint="https://api.perplexity.ai/search",
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
                            snippet="Colecoes de uso e cobertura da terra para o Brasil desde 1985.",
                        ),
                        PerplexityLinkRecord(
                            title="Panorama da Qualidade das Aguas",
                            url="https://www.ana.gov.br/portalpnqa/Publicacao/PANORAMA_DA_QUALIDADE_DAS_AGUAS.pdf",
                            domain="www.ana.gov.br",
                            snippet="Relatorio tecnico institucional sobre qualidade das aguas superficiais.",
                        ),
                    ],
                    blockers=[],
                    notes=["source:perplexity_search_api", "max_results:20"],
                ),
                PerplexitySearchSessionRecord(
                    query_id=query_plan[1].query_id,
                    query_text=query_plan[1].query_text,
                    search_profile=query_plan[1].search_profile,
                    target_intent=query_plan[1].target_intent,
                    research_track=query_plan[1].research_track,
                    collection_method="search_api",
                    request_endpoint="https://api.perplexity.ai/search",
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
                            url="https://repositorio.usp.br/bitstream/handle/BDPI/2262/art.pdf",
                            domain="repositorio.usp.br",
                            snippet="Estudo academico aplicado ao eixo Pereira Barreto e Tres Lagoas.",
                        ),
                    ],
                    blockers=[],
                    notes=["source:perplexity_search_api", "max_results:20"],
                ),
                PerplexitySearchSessionRecord(
                    query_id=query_plan[2].query_id,
                    query_text=query_plan[2].query_text,
                    search_profile=query_plan[2].search_profile,
                    target_intent=query_plan[2].target_intent,
                    research_track=query_plan[2].research_track,
                    collection_method="search_api",
                    request_endpoint="https://api.perplexity.ai/search",
                    answer_text="Projeto Tiete e monitoramentos complementam a interpretacao institucional.",
                    visible_source_count=2,
                    links=[
                        PerplexityLinkRecord(
                            title="Projeto Tiete IV",
                            url="https://www.sabesp.com.br/site/uploads/file/projeto_tiete/projetotiete_empd.pdf",
                            domain="www.sabesp.com.br",
                            snippet="Documento institucional do Projeto Tiete com dados de saneamento basico.",
                        ),
                    ],
                    blockers=[],
                    notes=["source:perplexity_search_api", "max_results:20"],
                ),
                PerplexitySearchSessionRecord(
                    query_id=query_plan[3].query_id,
                    query_text=query_plan[3].query_text,
                    search_profile=query_plan[3].search_profile,
                    target_intent=query_plan[3].target_intent,
                    research_track=query_plan[3].research_track,
                    collection_status="error",
                    collection_method="search_api",
                    request_endpoint="https://api.perplexity.ai/search",
                    answer_text="",
                    visible_source_count=0,
                    links=[],
                    blockers=["api_error:TimeoutError"],
                    notes=["tempo esgotado"],
                ),
            ]

    class FakeFirecrawlCollector:
        def extract_collection_guide(self, *, url, dataset):
            return CollectionGuide(
                steps=[f"Abrir {url}", f"Buscar {dataset.dataset_name or dataset.title}", "Exportar CSV"],
                filters_available={"regiao": "Bacia do Tiete", "periodo": "2000-2024"},
                download_format="CSV",
                estimated_effort="minutes",
                caveats=[],
                requires_login=False,
                direct_download_urls=[f"{url.rstrip('/')}/download.csv"],
            )

    pipeline = PerplexityIntelligencePipeline(
        base_query="impactos humanos no Rio Tiete reservatorios Sao Paulo Tres Lagoas qualidade agua",
        limit=10,
        max_searches=4,
        collector_factory=lambda: FakeCollector(),
        firecrawl_api_key="fc-test",
        firecrawl_collector_factory=lambda: FakeFirecrawlCollector(),
    )

    result = pipeline.execute()

    # --- contagens esperadas ---
    # 3 sessões ok × links = 3 + 2 + 1 = 6 fontes filtradas
    assert result["filtered_source_count"] == 6
    assert result["enriched_dataset_count"] == 6
    assert result["ranked_dataset_count"] == 6
    assert result["collection_guide_count"] == 6

    # --- artefatos em disco ---
    assert Path(result["intelligence_path"]).exists()
    assert Path(result["report_path"]).exists()
    assert Path(result["sources_csv_path"]).exists()
    assert Path(result["datasets_csv_path"]).exists()

    # --- raw sessions ---
    raw_sessions = json.loads(
        (tmp_path / "data" / "runs" / result["research_id"] / "collection" / "raw-sessions.json").read_text(
            encoding="utf-8"
        )
    )
    assert raw_sessions[0]["answer_text"].startswith("Hidroweb e MapBiomas")

    # --- processing/02-enriched-datasets.json ---
    enriched = json.loads(
        (tmp_path / "data" / "runs" / result["research_id"] / "processing" / "02-enriched-datasets.json").read_text(
            encoding="utf-8"
        )
    )
    assert "enriched_datasets" in enriched
    assert len(enriched["enriched_datasets"]) == 6
    assert enriched["enriched_datasets"][0]["collection_guide"]["download_format"] == "CSV"

    # --- manifest ---
    manifest = json.loads(Path(result["intelligence_path"]).read_text(encoding="utf-8"))
    assert manifest["session_count"] == 4
    assert manifest["filter_meta"]["error_sessions"] == 1
    assert manifest["filtered_source_count"] == 6
    assert manifest["collection_guide_count"] == 6
    assert len(manifest["intelligence"]["track_coverage"]) == 4

    # --- report ---
    report = Path(result["report_path"]).read_text(encoding="utf-8")
    assert "Relatório" in report or "Cobertura" in report

    # --- sources CSV ---
    sources_csv = Path(result["sources_csv_path"]).read_text(encoding="utf-8")
    assert sources_csv.startswith("rank,url,title")
    assert "hierarchy_level" in sources_csv
    assert "data_format" in sources_csv
    assert "access_type" in sources_csv
    assert "collection_guide_available" in sources_csv
