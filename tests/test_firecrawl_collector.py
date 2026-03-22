from src.connectors.firecrawl_collector import FirecrawlCollector, build_collection_prompt
from src.schemas.records import CollectionGuide, EnrichedDataset


class FakeFirecrawlResult:
    def __init__(self, payload):
        self.json = payload


class FakeFirecrawlClient:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def scrape(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return FakeFirecrawlResult(self.payload)


class FakeFirecrawlScrapeUrlClient:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def scrape_url(self, url, params=None):
        self.calls.append({"url": url, "params": params or {}})
        return {"json": self.payload}


def _dataset(**overrides):
    base = EnrichedDataset(
        url="https://qualar.cetesb.sp.gov.br/",
        title="QUALAR CETESB",
        snippet="Portal com dados de qualidade da agua em reservatorios.",
        source_domain="qualar.cetesb.sp.gov.br",
        track_origin="n3_qualidade_agua_reservatorios",
        track_priority="high",
        track_intent="dataset_discovery",
        hierarchy_level="bridge",
        thematic_axis="qualidade da agua nos reservatorios",
        source_category="official_portal",
        dataset_name="Rede CETESB reservatorios",
        dataset_description="Series historicas de monitoramento em reservatorios.",
        data_format="semi_structured",
        temporal_coverage="1978-2024",
        spatial_coverage="reservatorios da bacia do Tiete",
        key_parameters=["IQA", "IET", "OD", "DBO"],
        enrichment_method="llm",
        llm_model="gpt-4.1-nano",
    )
    return base.model_copy(update=overrides)


def test_build_collection_prompt_uses_contextual_dataset_fields() -> None:
    prompt = build_collection_prompt(_dataset())

    assert "Tema: qualidade da agua nos reservatorios" in prompt
    assert "Dataset: Rede CETESB reservatorios" in prompt
    assert "Parametros de interesse: IQA, IET, OD, DBO" in prompt
    assert "Periodo desejado: 1978-2024" in prompt
    assert "Regiao: reservatorios da bacia do Tiete" in prompt


def test_firecrawl_collector_returns_structured_collection_guide() -> None:
    client = FakeFirecrawlClient(
        {
            "steps": ["Abrir portal", "Selecionar reservatorio", "Exportar CSV"],
            "filters_available": {"ponto": "TIBB02900 = Barra Bonita"},
            "download_format": "CSV",
            "estimated_effort": "minutes",
            "caveats": ["Sessao expira rapido"],
            "requires_login": False,
            "direct_download_urls": ["https://qualar.cetesb.sp.gov.br/export.csv"],
        }
    )
    collector = FirecrawlCollector(api_key="fc-test", client=client)

    guide = collector.extract_collection_guide(
        url="https://qualar.cetesb.sp.gov.br/",
        dataset=_dataset(),
    )

    assert isinstance(guide, CollectionGuide)
    assert guide.download_format == "CSV"
    assert guide.estimated_effort == "minutes"
    assert "TIBB02900 = Barra Bonita" in guide.filters_available["ponto"]
    assert client.calls
    assert client.calls[0]["formats"] == ["json"]
    assert "qualidade da agua nos reservatorios" in client.calls[0]["json_options"]["prompt"]


def test_firecrawl_collector_uses_json_options_with_scrape_url_clients() -> None:
    client = FakeFirecrawlScrapeUrlClient(
        {
            "steps": ["Abrir portal", "Selecionar recorte", "Exportar GeoTIFF"],
            "filters_available": {"colecao": "Colecao 9"},
            "download_format": "GeoTIFF",
            "estimated_effort": "hours",
            "caveats": [],
            "requires_login": False,
            "direct_download_urls": ["https://mapbiomas.org/download.tif"],
        }
    )
    collector = FirecrawlCollector(api_key="fc-test", client=client)

    guide = collector.extract_collection_guide(
        url="https://mapbiomas.org/",
        dataset=_dataset(
            url="https://mapbiomas.org/",
            source_domain="mapbiomas.org",
            thematic_axis="uso e cobertura do solo",
            dataset_name="MapBiomas colecao 9",
            key_parameters=["LULC classes"],
            temporal_coverage="1985-2023",
            spatial_coverage="bacia do Rio Tiete, Sao Paulo",
        ),
    )

    assert guide.download_format == "GeoTIFF"
    assert client.calls
    assert client.calls[0]["params"]["formats"] == ["json"]
    assert client.calls[0]["params"]["jsonOptions"]["schema"]["title"] == "CollectionGuide"
    assert "uso e cobertura do solo" in client.calls[0]["params"]["jsonOptions"]["prompt"]


def test_firecrawl_collector_falls_back_when_payload_is_empty() -> None:
    client = FakeFirecrawlClient(None)
    collector = FirecrawlCollector(api_key="fc-test", client=client)

    guide = collector.extract_collection_guide(
        url="https://mapbiomas.org/",
        dataset=_dataset(
            url="https://mapbiomas.org/",
            source_domain="mapbiomas.org",
            thematic_axis="uso e cobertura do solo",
            dataset_name="MapBiomas colecao 9",
            key_parameters=["LULC classes"],
            temporal_coverage="1985-2023",
            spatial_coverage="bacia do Rio Tiete, Sao Paulo",
        ),
    )

    assert guide.estimated_effort == "hours"
    assert any("Extracao automatica falhou" in note for note in guide.caveats)
