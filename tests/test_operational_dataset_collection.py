from pathlib import Path

from src.connectors.operational_dataset_collector import (
    BDQUEIMADAS_CAPABILITIES_URL,
    CETESB_RESIDUOS_ITEM_PAGES,
    DEFAULT_TIETE_BBOX,
    INFOAGUAS_PORTAL_URL,
    OperationalDatasetCollector,
    SNIS_AE_INDEX_URL,
    DownloadedResource,
)
from src.pipelines.operational_dataset_collection_pipeline import OperationalDatasetCollectionPipeline
from src.schemas.records import OperationalCollectionTargetRecord


def _resource(url: str, *, text: str | None = None, content: bytes | None = None, headers=None) -> DownloadedResource:
    payload = content if content is not None else (text or "").encode("utf-8")
    return DownloadedResource(url=url, content=payload, headers=headers or {})


def _mapping_fetcher(mapping: dict[str, DownloadedResource]):
    def _fetch(url: str) -> DownloadedResource:
        if url not in mapping:
            raise AssertionError(f"URL nao mapeada no teste: {url}")
        return mapping[url]

    return _fetch


def test_collect_infoaguas_registers_blocked_note(tmp_path: Path) -> None:
    collector = OperationalDatasetCollector(fetcher=_mapping_fetcher({}))
    run_dir = tmp_path / "run"

    targets = collector.collect(
        run_dir=run_dir,
        target_ids=["infoaguas_qualidade_agua"],
        year_start=2000,
        year_end=2024,
        bbox=DEFAULT_TIETE_BBOX,
        bdqueimadas_series="todosats",
    )

    target = targets[0]
    assert target.collection_status == "blocked"
    assert target.requires_auth is True
    assert INFOAGUAS_PORTAL_URL in target.provenance_urls
    assert (run_dir / "collection" / "qualidade_agua" / "portal_access_note.json").exists()


def test_collect_bdqueimadas_saves_capabilities_and_csvs(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    capabilities_text = """
    <Name>dados_abertos:focos_2023_br_todosats</Name>
    <Name>dados_abertos:focos_2024_br_todosats</Name>
    """
    url_2023 = OperationalDatasetCollector._build_bdqueimadas_export_url(
        "dados_abertos:focos_2023_br_todosats",
        DEFAULT_TIETE_BBOX,
    )
    url_2024 = OperationalDatasetCollector._build_bdqueimadas_export_url(
        "dados_abertos:focos_2024_br_todosats",
        DEFAULT_TIETE_BBOX,
    )
    collector = OperationalDatasetCollector(
        fetcher=_mapping_fetcher(
            {
                BDQUEIMADAS_CAPABILITIES_URL: _resource(
                    BDQUEIMADAS_CAPABILITIES_URL,
                    text=capabilities_text,
                    headers={"Content-Type": "application/xml"},
                ),
                url_2023: _resource(url_2023, text="latitude,longitude\n-22.1,-49.1\n", headers={"Content-Type": "text/csv"}),
                url_2024: _resource(url_2024, text="latitude,longitude\n-22.2,-49.2\n", headers={"Content-Type": "text/csv"}),
            }
        )
    )

    targets = collector.collect(
        run_dir=run_dir,
        target_ids=["bdqueimadas_focos_calor"],
        year_start=2023,
        year_end=2024,
        bbox=DEFAULT_TIETE_BBOX,
        bdqueimadas_series="todosats",
    )

    target = targets[0]
    assert target.collection_status == "collected"
    assert len(target.raw_artifacts) == 3
    assert (run_dir / "collection" / "queimadas" / "bdqueimadas_capabilities.xml").exists()
    assert (run_dir / "collection" / "queimadas" / "focos_2023_todosats.csv").exists()
    assert (run_dir / "collection" / "queimadas" / "focos_2024_todosats.csv").exists()


def test_collect_snis_downloads_year_attachments(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    year_2018_url = f"{SNIS_AE_INDEX_URL}/2018"
    year_2019_url = f"{SNIS_AE_INDEX_URL}/2019"
    zip_2018_url = f"{year_2018_url}/Planilhas_AE2018.zip"
    csv_2019_url = f"{year_2019_url}/indicadores_2019.csv"
    index_html = f"""
    <a href="{year_2018_url}">2018</a>
    <a href="{year_2019_url}">2019</a>
    """
    year_2018_html = f"""<a href="{zip_2018_url}">Planilhas 2018</a>"""
    year_2019_html = f"""<a href="{csv_2019_url}">CSV 2019</a>"""
    collector = OperationalDatasetCollector(
        fetcher=_mapping_fetcher(
            {
                SNIS_AE_INDEX_URL: _resource(SNIS_AE_INDEX_URL, text=index_html, headers={"Content-Type": "text/html"}),
                year_2018_url: _resource(year_2018_url, text=year_2018_html, headers={"Content-Type": "text/html"}),
                year_2019_url: _resource(year_2019_url, text=year_2019_html, headers={"Content-Type": "text/html"}),
                zip_2018_url: _resource(zip_2018_url, content=b"PK\x03\x04test", headers={"Content-Type": "application/zip"}),
                csv_2019_url: _resource(csv_2019_url, text="municipio,valor\n1,10\n", headers={"Content-Type": "text/csv"}),
            }
        )
    )

    targets = collector.collect(
        run_dir=run_dir,
        target_ids=["snis_agua_esgoto"],
        year_start=2018,
        year_end=2019,
        bbox=DEFAULT_TIETE_BBOX,
        bdqueimadas_series="todosats",
    )

    target = targets[0]
    assert target.collection_status == "collected"
    assert (run_dir / "collection" / "snis" / "attachments" / "2018" / "Planilhas_AE2018.zip").exists()
    assert (run_dir / "collection" / "snis" / "attachments" / "2019" / "indicadores_2019.csv").exists()


def test_collect_cetesb_residuos_downloads_pdf(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    page_url = CETESB_RESIDUOS_ITEM_PAGES[2020]
    pdf_url = "https://repositorio.cetesb.sp.gov.br/bitstreams/teste/download"
    page_html = f"""<a href="{pdf_url}">Download</a>"""
    collector = OperationalDatasetCollector(
        fetcher=_mapping_fetcher(
            {
                page_url: _resource(page_url, text=page_html, headers={"Content-Type": "text/html"}),
                pdf_url: _resource(pdf_url, content=b"%PDF-1.4 fake pdf", headers={"Content-Type": "application/pdf"}),
            }
        )
    )

    targets = collector.collect(
        run_dir=run_dir,
        target_ids=["cetesb_inventario_residuos"],
        year_start=2020,
        year_end=2020,
        bbox=DEFAULT_TIETE_BBOX,
        bdqueimadas_series="todosats",
    )

    target = targets[0]
    assert target.collection_status == "collected"
    assert (run_dir / "collection" / "residuos" / "downloads" / "inventario_residuos_2020.pdf").exists()


class FakeCollector:
    def collect(
        self,
        *,
        run_dir: Path,
        target_ids,
        year_start: int,
        year_end: int,
        bbox,
        bdqueimadas_series: str,
    ) -> list[OperationalCollectionTargetRecord]:
        assert run_dir.name.startswith("operational-collect-")
        assert target_ids == ["bdqueimadas_focos_calor"]
        assert year_start == 2023
        assert year_end == 2024
        assert bdqueimadas_series == "satref"
        assert bbox == DEFAULT_TIETE_BBOX
        return [
            OperationalCollectionTargetRecord(
                target_id="bdqueimadas_focos_calor",
                source_name="INPE BDQueimadas",
                dataset_name="Focos de Calor",
                collection_status="collected",
                access_type="api_access",
                collection_method="wfs",
                staging_outputs=["data/staging/queimadas/focos_calor_evento.parquet"],
                analytic_outputs=["data/analytic/subbacia_ano/queimadas_subbacia_ano.parquet"],
                join_keys=["id_subbacia", "ano"],
            )
        ]


def test_operational_collection_pipeline_writes_manifest_and_reports(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    pipeline = OperationalDatasetCollectionPipeline(
        target_ids=["bdqueimadas_focos_calor"],
        year_start=2023,
        year_end=2024,
        bbox=DEFAULT_TIETE_BBOX,
        bdqueimadas_series="satref",
        collector=FakeCollector(),
    )

    result = pipeline.execute()

    manifest_path = Path(result["manifest_path"])
    processing_path = Path(result["processing_path"])
    report_path = Path(result["report_path"])
    report_csv_path = Path(result["report_csv_path"])

    assert manifest_path.exists()
    assert processing_path.exists()
    assert report_path.exists()
    assert report_csv_path.exists()
    assert result["collected_count"] == 1
