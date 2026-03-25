"""Coleta operacional de fontes ambientais para acoplamento na EDA."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

from src.schemas.records import CollectionArtifactRecord, OperationalCollectionTargetRecord
from src.utils.io import ensure_dir, write_bytes, write_json

DEFAULT_TIETE_BBOX = (-52.2, -24.0, -45.8, -20.5)

AVAILABLE_OPERATIONAL_TARGETS = (
    "infoaguas_qualidade_agua",
    "bdqueimadas_focos_calor",
    "snis_agua_esgoto",
    "cetesb_inventario_residuos",
)

INFOAGUAS_PORTAL_URL = "https://sistemainfoaguas.cetesb.sp.gov.br/"
INFOAGUAS_REGISTER_URL = "https://seguranca.cetesb.sp.gov.br/Home/CadastrarUsuario"

BDQUEIMADAS_CAPABILITIES_URL = (
    "https://terrabrasilis.dpi.inpe.br/queimadas/geoserver/ows"
    "?SERVICE=WFS&VERSION=1.0.0&REQUEST=GetCapabilities"
)
BDQUEIMADAS_WFS_URL = "https://terrabrasilis.dpi.inpe.br/queimadas/geoserver/wfs"

SNIS_AE_INDEX_URL = (
    "https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/"
    "saneamento/snis/diagnosticos-anteriores-do-snis/agua-e-esgotos-1"
)

CETESB_REPOSITORIO_URL = "https://repositorio.cetesb.sp.gov.br"
CETESB_RESIDUOS_ITEM_PAGES = {
    2017: f"{CETESB_REPOSITORIO_URL}/handle/123456789/2879",
    2018: f"{CETESB_REPOSITORIO_URL}/handle/123456789/2459",
    2019: f"{CETESB_REPOSITORIO_URL}/handle/123456789/2429",
    2020: f"{CETESB_REPOSITORIO_URL}/handle/123456789/2460",
    2021: f"{CETESB_REPOSITORIO_URL}/handle/123456789/2493",
}

_TARGET_LAYOUTS = {
    "infoaguas_qualidade_agua": {
        "source_name": "CETESB InfoAguas",
        "dataset_name": "Qualidade da Agua Interior",
        "raw_dirname": "qualidade_agua",
        "staging_outputs": [
            "data/staging/qualidade_agua/qualidade_agua_ponto_amostra.parquet",
            "data/staging/qualidade_agua/pontos_monitoramento_tiete.parquet",
        ],
        "analytic_outputs": [
            "data/analytic/reservatorio_mes/qualidade_agua_reservatorio_mes.parquet",
            "data/analytic/reservatorio_ano/qualidade_agua_reservatorio_ano.parquet",
        ],
        "join_keys": ["cod_ponto", "id_reservatorio", "ano_mes", "ano"],
    },
    "bdqueimadas_focos_calor": {
        "source_name": "INPE BDQueimadas",
        "dataset_name": "Focos de Calor",
        "raw_dirname": "queimadas",
        "staging_outputs": ["data/staging/queimadas/focos_calor_evento.parquet"],
        "analytic_outputs": [
            "data/analytic/subbacia_ano/queimadas_subbacia_ano.parquet",
            "data/analytic/reservatorio_ano/queimadas_reservatorio_ano.parquet",
        ],
        "join_keys": ["id_subbacia", "id_reservatorio", "ano"],
    },
    "snis_agua_esgoto": {
        "source_name": "SNIS Agua e Esgoto",
        "dataset_name": "Serie Historica SNIS Agua e Esgoto",
        "raw_dirname": "snis",
        "staging_outputs": ["data/staging/snis/snis_municipios_serie.parquet"],
        "analytic_outputs": [
            "data/analytic/municipio_ano/snis_municipio_ano.parquet",
            "data/analytic/reservatorio_ano/snis_reservatorio_ano.parquet",
        ],
        "join_keys": ["cod_ibge", "id_reservatorio", "ano"],
    },
    "cetesb_inventario_residuos": {
        "source_name": "CETESB Inventario de Residuos Solidos Urbanos",
        "dataset_name": "Inventario Estadual de Residuos Solidos Urbanos",
        "raw_dirname": "residuos",
        "staging_outputs": ["data/staging/residuos/residuos_municipio_ano.parquet"],
        "analytic_outputs": [
            "data/analytic/municipio_ano/residuos_municipio_ano.parquet",
            "data/analytic/reservatorio_ano/residuos_reservatorio_ano.parquet",
        ],
        "join_keys": ["cod_ibge", "id_reservatorio", "ano"],
    },
}


@dataclass(slots=True)
class DownloadedResource:
    """Resposta HTTP persistivel."""

    url: str
    content: bytes
    status_code: int = 200
    headers: dict[str, str] | None = None

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")


class OperationalDatasetCollector:
    """Baixa arquivos brutos e registra bloqueios para fontes operacionais."""

    def __init__(
        self,
        *,
        fetcher: Callable[[str], DownloadedResource] | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.fetcher = fetcher or self._build_default_fetcher()

    def collect(
        self,
        *,
        run_dir: Path,
        target_ids: Sequence[str],
        year_start: int,
        year_end: int,
        bbox: tuple[float, float, float, float],
        bdqueimadas_series: str,
    ) -> list[OperationalCollectionTargetRecord]:
        handlers = {
            "infoaguas_qualidade_agua": self._collect_infoaguas,
            "bdqueimadas_focos_calor": self._collect_bdqueimadas,
            "snis_agua_esgoto": self._collect_snis_agua_esgoto,
            "cetesb_inventario_residuos": self._collect_cetesb_residuos,
        }

        records: list[OperationalCollectionTargetRecord] = []
        for target_id in target_ids:
            handler = handlers.get(target_id)
            if handler is None:
                raise ValueError(f"Target operacional desconhecido: {target_id}")
            records.append(
                handler(
                    run_dir=run_dir,
                    year_start=year_start,
                    year_end=year_end,
                    bbox=bbox,
                    bdqueimadas_series=bdqueimadas_series,
                )
            )
        return records

    def _collect_infoaguas(
        self,
        *,
        run_dir: Path,
        year_start: int,
        year_end: int,
        bbox: tuple[float, float, float, float],
        bdqueimadas_series: str,
    ) -> OperationalCollectionTargetRecord:
        del bdqueimadas_series
        layout = _TARGET_LAYOUTS["infoaguas_qualidade_agua"]
        target_dir = run_dir / "collection" / layout["raw_dirname"]
        ensure_dir(target_dir)

        payload = {
            "collection_status": "blocked",
            "portal_url": INFOAGUAS_PORTAL_URL,
            "register_url": INFOAGUAS_REGISTER_URL,
            "notes": [
                "Portal atual exige autenticacao para consulta interativa e exportacao.",
                "A coleta automatica fica pendente de credenciais validas da CETESB.",
            ],
        }
        note_path = target_dir / "portal_access_note.json"
        write_json(note_path, payload)
        artifact = self._artifact_from_bytes(
            run_dir=run_dir,
            path=note_path,
            target_id="infoaguas_qualidade_agua",
            source_name=layout["source_name"],
            download_url=INFOAGUAS_PORTAL_URL,
            payload=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
            file_format="json",
            media_type="application/json",
            status="blocked",
            notes=["Bloqueio registrado para futura coleta autenticada."],
        )

        return OperationalCollectionTargetRecord(
            target_id="infoaguas_qualidade_agua",
            source_name=layout["source_name"],
            dataset_name=layout["dataset_name"],
            collection_status="blocked",
            access_type="restricted",
            collection_method="portal_login",
            requires_auth=True,
            year_start=year_start,
            year_end=year_end,
            bbox=self._format_bbox_value(bbox),
            provenance_urls=[INFOAGUAS_PORTAL_URL, INFOAGUAS_REGISTER_URL],
            blockers=["Portal exige login e senha."],
            notes=[
                "Armazenar apenas o registro de bloqueio agora.",
                "Quando houver acesso, normalizar por cod_ponto, id_reservatorio, ano_mes e ano.",
            ],
            join_keys=list(layout["join_keys"]),
            staging_outputs=list(layout["staging_outputs"]),
            analytic_outputs=list(layout["analytic_outputs"]),
            raw_artifacts=[artifact],
        )

    def _collect_bdqueimadas(
        self,
        *,
        run_dir: Path,
        year_start: int,
        year_end: int,
        bbox: tuple[float, float, float, float],
        bdqueimadas_series: str,
    ) -> OperationalCollectionTargetRecord:
        layout = _TARGET_LAYOUTS["bdqueimadas_focos_calor"]
        target_dir = run_dir / "collection" / layout["raw_dirname"]
        ensure_dir(target_dir)

        artifacts: list[CollectionArtifactRecord] = []
        notes = [
            "Usa exportacao WFS aberta do TerraBrasilis/INPE, sem formulario por e-mail.",
            "Os CSVs brutos devem ser agregados depois para subbacia_ano e reservatorio_ano.",
        ]
        blockers: list[str] = []
        available_layers: set[str] = set()

        try:
            capabilities = self.fetcher(BDQUEIMADAS_CAPABILITIES_URL)
            capabilities_path = target_dir / "bdqueimadas_capabilities.xml"
            write_bytes(capabilities_path, capabilities.content)
            artifacts.append(
                self._artifact_from_resource(
                    run_dir=run_dir,
                    path=capabilities_path,
                    target_id="bdqueimadas_focos_calor",
                    source_name=layout["source_name"],
                    resource=capabilities,
                    file_format="xml",
                    notes=["Capabilities WFS usada para descobrir camadas anuais disponiveis."],
                )
            )
            available_layers = self._extract_bdqueimadas_layers(capabilities.text)
        except Exception as exc:  # pragma: no cover - fallback de rede
            return OperationalCollectionTargetRecord(
                target_id="bdqueimadas_focos_calor",
                source_name=layout["source_name"],
                dataset_name=layout["dataset_name"],
                collection_status="error",
                access_type="api_access",
                collection_method="wfs",
                requires_auth=False,
                year_start=year_start,
                year_end=year_end,
                bbox=self._format_bbox_value(bbox),
                provenance_urls=[BDQUEIMADAS_CAPABILITIES_URL, BDQUEIMADAS_WFS_URL],
                blockers=[f"Falha ao ler capabilities: {exc}"],
                notes=notes,
                join_keys=list(layout["join_keys"]),
                staging_outputs=list(layout["staging_outputs"]),
                analytic_outputs=list(layout["analytic_outputs"]),
                raw_artifacts=artifacts,
            )

        downloaded_years: list[int] = []
        missing_years: list[int] = []
        failed_years: list[int] = []
        for year in range(year_start, year_end + 1):
            layer_name = f"dados_abertos:focos_{year}_br_{bdqueimadas_series}"
            if layer_name not in available_layers:
                missing_years.append(year)
                continue

            export_url = self._build_bdqueimadas_export_url(layer_name, bbox)
            try:
                resource = self.fetcher(export_url)
                filename = f"focos_{year}_{bdqueimadas_series}.csv"
                file_path = target_dir / filename
                write_bytes(file_path, resource.content)
                artifacts.append(
                    self._artifact_from_resource(
                        run_dir=run_dir,
                        path=file_path,
                        target_id="bdqueimadas_focos_calor",
                        source_name=layout["source_name"],
                        resource=resource,
                        file_format="csv",
                        notes=[f"Camada WFS: {layer_name}"],
                    )
                )
                downloaded_years.append(year)
            except Exception:
                failed_years.append(year)

        if missing_years:
            notes.append(f"Anos sem camada WFS identificada: {self._format_year_scope(missing_years)}.")
        if failed_years:
            blockers.append(f"Falha ao baixar os anos: {self._format_year_scope(failed_years)}.")

        status = "collected"
        if failed_years or missing_years:
            status = "partial" if downloaded_years else "error"
        elif not downloaded_years:
            status = "error"

        return OperationalCollectionTargetRecord(
            target_id="bdqueimadas_focos_calor",
            source_name=layout["source_name"],
            dataset_name=layout["dataset_name"],
            collection_status=status,
            access_type="api_access",
            collection_method="wfs",
            requires_auth=False,
            year_start=year_start,
            year_end=year_end,
            bbox=self._format_bbox_value(bbox),
            provenance_urls=[BDQUEIMADAS_CAPABILITIES_URL, BDQUEIMADAS_WFS_URL],
            blockers=blockers,
            notes=notes,
            join_keys=list(layout["join_keys"]),
            staging_outputs=list(layout["staging_outputs"]),
            analytic_outputs=list(layout["analytic_outputs"]),
            raw_artifacts=artifacts,
        )

    def _collect_snis_agua_esgoto(
        self,
        *,
        run_dir: Path,
        year_start: int,
        year_end: int,
        bbox: tuple[float, float, float, float],
        bdqueimadas_series: str,
    ) -> OperationalCollectionTargetRecord:
        del bbox, bdqueimadas_series
        layout = _TARGET_LAYOUTS["snis_agua_esgoto"]
        target_dir = run_dir / "collection" / layout["raw_dirname"]
        ensure_dir(target_dir)

        artifacts: list[CollectionArtifactRecord] = []
        blockers: list[str] = []
        notes = [
            "A coleta usa as paginas oficiais do gov.br em vez do fluxo antigo do app4.mdr.gov.br.",
            "Os arquivos baixados permanecem brutos para posterior consolidacao municipio_ano e reservatorio_ano.",
        ]

        try:
            index_page = self.fetcher(SNIS_AE_INDEX_URL)
        except Exception as exc:  # pragma: no cover - fallback de rede
            return OperationalCollectionTargetRecord(
                target_id="snis_agua_esgoto",
                source_name=layout["source_name"],
                dataset_name=layout["dataset_name"],
                collection_status="error",
                access_type="direct_download",
                collection_method="html_discovery",
                requires_auth=False,
                year_start=year_start,
                year_end=year_end,
                provenance_urls=[SNIS_AE_INDEX_URL],
                blockers=[f"Falha ao acessar indice do SNIS: {exc}"],
                notes=notes,
                join_keys=list(layout["join_keys"]),
                staging_outputs=list(layout["staging_outputs"]),
                analytic_outputs=list(layout["analytic_outputs"]),
                raw_artifacts=artifacts,
            )

        index_path = target_dir / "index.html"
        write_bytes(index_path, index_page.content)
        artifacts.append(
            self._artifact_from_resource(
                run_dir=run_dir,
                path=index_path,
                target_id="snis_agua_esgoto",
                source_name=layout["source_name"],
                resource=index_page,
                file_format="html",
                notes=["Pagina indice oficial para descoberta dos anos disponiveis."],
            )
        )

        year_pages = self._extract_snis_year_pages(index_page.text)
        requested_years = range(year_start, year_end + 1)
        downloaded_attachments = 0
        missing_years: list[int] = []
        failed_years: list[int] = []
        provenance_urls = [SNIS_AE_INDEX_URL]

        for year in requested_years:
            year_url = year_pages.get(year) or f"{SNIS_AE_INDEX_URL}/{year}"

            provenance_urls.append(year_url)
            try:
                year_page = self.fetcher(year_url)
                year_page_path = target_dir / "years" / f"{year}.html"
                write_bytes(year_page_path, year_page.content)
                artifacts.append(
                    self._artifact_from_resource(
                        run_dir=run_dir,
                        path=year_page_path,
                        target_id="snis_agua_esgoto",
                        source_name=layout["source_name"],
                        resource=year_page,
                        file_format="html",
                        notes=[f"Pagina do ano {year} com anexos oficiais."],
                    )
                )
                attachment_urls = self._select_snis_attachment_urls(
                    self._extract_attachment_urls(
                        year_page.text,
                        base_url=year_url,
                        extensions=(".zip", ".xls", ".xlsx", ".ods", ".csv"),
                    ),
                    year=year,
                )
                if not attachment_urls:
                    missing_years.append(year)
                    continue

                downloaded_this_year = 0
                failed_this_year = 0
                for index, attachment_url in enumerate(attachment_urls, start=1):
                    try:
                        attachment = self.fetcher(attachment_url)
                        filename = self._resource_filename(
                            url=attachment_url,
                            headers=attachment.headers or {},
                            fallback=f"snis_ae_{year}_{index}",
                        )
                        file_path = target_dir / "attachments" / str(year) / filename
                        write_bytes(file_path, attachment.content)
                        artifacts.append(
                            self._artifact_from_resource(
                                run_dir=run_dir,
                                path=file_path,
                                target_id="snis_agua_esgoto",
                                source_name=layout["source_name"],
                                resource=attachment,
                                notes=[f"Anexo oficial do SNIS {year}."],
                            )
                        )
                        downloaded_attachments += 1
                        downloaded_this_year += 1
                    except Exception:
                        failed_this_year += 1
                if downloaded_this_year == 0 and failed_this_year > 0:
                    failed_years.append(year)
                elif failed_this_year > 0:
                    notes.append(f"Alguns anexos do ano {year} falharam, mas a coleta parcial do ano foi preservada.")
            except Exception:
                if year in year_pages:
                    failed_years.append(year)
                else:
                    missing_years.append(year)

        if missing_years:
            notes.append(f"Anos sem pagina/anexo identificado: {self._format_year_scope(missing_years)}.")
        if failed_years:
            blockers.append(f"Falha ao baixar anos do SNIS: {self._format_year_scope(failed_years)}.")

        status = "collected"
        if failed_years or missing_years:
            status = "partial" if downloaded_attachments else "error"
        elif downloaded_attachments == 0:
            status = "error"

        return OperationalCollectionTargetRecord(
            target_id="snis_agua_esgoto",
            source_name=layout["source_name"],
            dataset_name=layout["dataset_name"],
            collection_status=status,
            access_type="direct_download",
            collection_method="html_discovery",
            requires_auth=False,
            year_start=year_start,
            year_end=year_end,
            provenance_urls=provenance_urls,
            blockers=blockers,
            notes=notes,
            join_keys=list(layout["join_keys"]),
            staging_outputs=list(layout["staging_outputs"]),
            analytic_outputs=list(layout["analytic_outputs"]),
            raw_artifacts=artifacts,
        )

    def _collect_cetesb_residuos(
        self,
        *,
        run_dir: Path,
        year_start: int,
        year_end: int,
        bbox: tuple[float, float, float, float],
        bdqueimadas_series: str,
    ) -> OperationalCollectionTargetRecord:
        del bbox, bdqueimadas_series
        layout = _TARGET_LAYOUTS["cetesb_inventario_residuos"]
        target_dir = run_dir / "collection" / layout["raw_dirname"]
        ensure_dir(target_dir)

        artifacts: list[CollectionArtifactRecord] = []
        blockers: list[str] = []
        notes = [
            "Os relatorios sao PDFs anuais, com tabelas para extracao posterior.",
            "A normalizacao deve produzir municipio_ano e a derivacao para reservatorio_ano.",
        ]

        downloaded_years: list[int] = []
        missing_years: list[int] = []
        failed_years: list[int] = []
        provenance_urls: list[str] = []

        for year in range(year_start, year_end + 1):
            page_url = CETESB_RESIDUOS_ITEM_PAGES.get(year)
            if not page_url:
                missing_years.append(year)
                continue

            provenance_urls.append(page_url)
            try:
                page = self.fetcher(page_url)
                page_path = target_dir / "pages" / f"{year}.html"
                write_bytes(page_path, page.content)
                artifacts.append(
                    self._artifact_from_resource(
                        run_dir=run_dir,
                        path=page_path,
                        target_id="cetesb_inventario_residuos",
                        source_name=layout["source_name"],
                        resource=page,
                        file_format="html",
                        notes=[f"Pagina do repositorio CETESB para o ano {year}."],
                    )
                )
                download_urls = self._extract_cetesb_download_urls(page.text, base_url=page_url)
                if not download_urls:
                    missing_years.append(year)
                    continue

                pdf_downloaded = False
                for download_url in download_urls:
                    try:
                        download = self.fetcher(download_url)
                    except Exception:
                        continue
                    if not self._looks_like_pdf(download):
                        continue

                    pdf_path = target_dir / "downloads" / f"inventario_residuos_{year}.pdf"
                    write_bytes(pdf_path, download.content)
                    artifacts.append(
                        self._artifact_from_resource(
                            run_dir=run_dir,
                            path=pdf_path,
                            target_id="cetesb_inventario_residuos",
                            source_name=layout["source_name"],
                            resource=download,
                            file_format="pdf",
                            notes=[f"Relatorio anual de residuos urbanos {year}."],
                        )
                    )
                    downloaded_years.append(year)
                    pdf_downloaded = True
                    break
                if not pdf_downloaded:
                    failed_years.append(year)
            except Exception:
                failed_years.append(year)

        if missing_years:
            notes.append(f"Anos sem pagina publica mapeada ou sem PDF localizado: {self._format_year_scope(missing_years)}.")
        if failed_years:
            blockers.append(f"Falha ao baixar PDFs CETESB: {self._format_year_scope(failed_years)}.")

        status = "collected"
        if failed_years or missing_years:
            status = "partial" if downloaded_years else "error"
        elif not downloaded_years:
            status = "error"

        return OperationalCollectionTargetRecord(
            target_id="cetesb_inventario_residuos",
            source_name=layout["source_name"],
            dataset_name=layout["dataset_name"],
            collection_status=status,
            access_type="pdf_extraction",
            collection_method="html_discovery",
            requires_auth=False,
            year_start=year_start,
            year_end=year_end,
            provenance_urls=provenance_urls,
            blockers=blockers,
            notes=notes,
            join_keys=list(layout["join_keys"]),
            staging_outputs=list(layout["staging_outputs"]),
            analytic_outputs=list(layout["analytic_outputs"]),
            raw_artifacts=artifacts,
        )

    def _build_default_fetcher(self) -> Callable[[str], DownloadedResource]:
        def _fetch(url: str) -> DownloadedResource:
            request = Request(
                url,
                headers={
                    "User-Agent": "Research-FREnTE/operational-collector",
                    "Accept": "*/*",
                },
            )
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    headers = {key: value for key, value in response.headers.items()}
                    status_code = getattr(response, "status", 200)
                    return DownloadedResource(
                        url=response.geturl(),
                        content=response.read(),
                        status_code=status_code,
                        headers=headers,
                    )
            except HTTPError as exc:  # pragma: no cover - depende de rede real
                raise RuntimeError(f"HTTP {exc.code} ao acessar {url}") from exc
            except URLError as exc:  # pragma: no cover - depende de rede real
                raise RuntimeError(f"Falha de rede ao acessar {url}: {exc.reason}") from exc

        return _fetch

    @staticmethod
    def _extract_bdqueimadas_layers(capabilities_text: str) -> set[str]:
        return {
            match.group(0)
            for match in re.finditer(
                r"dados_abertos:focos_\d{4}_br_(?:satref|todosats)",
                capabilities_text,
                flags=re.IGNORECASE,
            )
        }

    @staticmethod
    def _extract_snis_year_pages(index_html: str) -> dict[int, str]:
        year_pages: dict[int, str] = {}
        pattern = re.compile(r"""href=["']([^"']*?/agua-e-esgotos-1/(\d{4})[^"']*)["']""", re.IGNORECASE)
        for href, year_text in pattern.findall(index_html):
            year = int(year_text)
            year_pages[year] = urljoin(SNIS_AE_INDEX_URL, href)
        return year_pages

    @staticmethod
    def _extract_attachment_urls(html_text: str, *, base_url: str, extensions: tuple[str, ...]) -> list[str]:
        urls: list[str] = []
        seen: set[str] = set()
        href_pattern = re.compile(r"""href=["']([^"']+)["']""", re.IGNORECASE)
        for href in href_pattern.findall(html_text):
            resolved = urljoin(base_url, href)
            path = urlparse(resolved).path.lower()
            if not path.endswith(extensions):
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            urls.append(resolved)
        return urls

    @staticmethod
    def _select_snis_attachment_urls(urls: Sequence[str], *, year: int) -> list[str]:
        preferred: list[str] = []
        seen: set[str] = set()
        year_token = str(year)
        for url in urls:
            lower = url.lower()
            if year_token not in lower and f"ae{year}" not in lower:
                continue
            if not any(keyword in lower for keyword in ("planilhas", "diagnostico", "glossario", "atestado")):
                continue
            if url in seen:
                continue
            seen.add(url)
            preferred.append(url)
        return preferred or list(urls)

    @staticmethod
    def _extract_cetesb_download_urls(html_text: str, *, base_url: str) -> list[str]:
        urls: list[str] = []
        seen: set[str] = set()
        patterns = [
            re.compile(r"""href=["']([^"']*/bitstreams/[^"']+/download[^"']*)["']""", re.IGNORECASE),
            re.compile(r"""href=["']([^"']+\.pdf(?:\?[^"']*)?)["']""", re.IGNORECASE),
        ]
        for pattern in patterns:
            for href in pattern.findall(html_text):
                resolved = urljoin(base_url, href)
                if resolved in seen:
                    continue
                seen.add(resolved)
                urls.append(resolved)
        return urls

    @staticmethod
    def _resource_filename(*, url: str, headers: dict[str, str], fallback: str) -> str:
        disposition = headers.get("Content-Disposition", "") or headers.get("content-disposition", "")
        filename_match = re.search(r"""filename="?([^";]+)"?""", disposition, flags=re.IGNORECASE)
        if filename_match:
            return filename_match.group(1)

        parsed = urlparse(url)
        path_name = Path(parsed.path).name
        if path_name:
            return path_name

        content_type = headers.get("Content-Type", "") or headers.get("content-type", "")
        if "pdf" in content_type.lower():
            return f"{fallback}.pdf"
        if "csv" in content_type.lower():
            return f"{fallback}.csv"
        if "zip" in content_type.lower():
            return f"{fallback}.zip"
        return f"{fallback}.bin"

    @staticmethod
    def _build_bdqueimadas_export_url(
        layer_name: str,
        bbox: tuple[float, float, float, float],
    ) -> str:
        params = {
            "service": "WFS",
            "version": "1.0.0",
            "request": "GetFeature",
            "typeName": layer_name,
            "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},EPSG:4326",
            "srsName": "EPSG:4326",
            "outputFormat": "CSV",
        }
        return f"{BDQUEIMADAS_WFS_URL}?{urlencode(params)}"

    @staticmethod
    def _format_bbox_value(bbox: tuple[float, float, float, float]) -> str:
        return f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"

    @staticmethod
    def _format_year_scope(years: Sequence[int]) -> str:
        ordered = sorted(set(years))
        return ",".join(str(year) for year in ordered)

    @staticmethod
    def _looks_like_pdf(resource: DownloadedResource) -> bool:
        content_type = (resource.headers or {}).get("Content-Type", "")
        return "pdf" in content_type.lower() or resource.content.startswith(b"%PDF")

    def _artifact_from_resource(
        self,
        *,
        run_dir: Path,
        path: Path,
        target_id: str,
        source_name: str,
        resource: DownloadedResource,
        file_format: str | None = None,
        notes: list[str] | None = None,
    ) -> CollectionArtifactRecord:
        media_type = (resource.headers or {}).get("Content-Type", "")
        return self._artifact_from_bytes(
            run_dir=run_dir,
            path=path,
            target_id=target_id,
            source_name=source_name,
            download_url=resource.url,
            payload=resource.content,
            file_format=file_format or path.suffix.lstrip(".") or "bin",
            media_type=media_type,
            status="collected",
            notes=notes or [],
        )

    @staticmethod
    def _artifact_from_bytes(
        *,
        run_dir: Path,
        path: Path,
        target_id: str,
        source_name: str,
        download_url: str,
        payload: bytes,
        file_format: str,
        media_type: str,
        status: str,
        notes: list[str],
    ) -> CollectionArtifactRecord:
        checksum = hashlib.sha256(payload).hexdigest()
        relative_path = path.relative_to(run_dir).as_posix()
        return CollectionArtifactRecord(
            artifact_id=f"{target_id}-{path.stem}",
            target_id=target_id,
            source_name=source_name,
            status=status,
            relative_path=relative_path,
            download_url=download_url,
            media_type=media_type,
            file_format=file_format,
            content_length=len(payload),
            checksum_sha256=checksum,
            notes=notes,
        )
