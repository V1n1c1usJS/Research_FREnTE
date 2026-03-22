"""Etapa 3 — classifica acesso e ordena os datasets por prioridade (sem LLM)."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from src.agents.base import BaseAgent
from src.schemas.records import EnrichedDataset, RankedDataset

_PRIORITY_ORDER: dict[str, int] = {"high": 0, "medium": 1, "low": 2}

_FORMAT_ORDER: dict[str, int] = {
    "structured": 0,
    "semi_structured": 1,
    "geospatial_platform": 2,
    "academic_paper": 3,
    "pdf_report": 4,
    "unknown": 5,
}

# Regras de acesso: extensão ou fragmento de domínio/path → access_type
_EXT_ACCESS: dict[str, str] = {
    ".csv": "direct_download",
    ".xlsx": "direct_download",
    ".xls": "direct_download",
    ".shp": "direct_download",
    ".zip": "direct_download",
    ".tif": "direct_download",
    ".geotiff": "direct_download",
    ".gpkg": "direct_download",
    ".nc": "direct_download",
    ".pdf": "pdf_extraction",
}

_DOMAIN_ACCESS: dict[str, str] = {
    "qualar.cetesb.sp.gov.br": "web_portal",
    "snirh.gov.br": "web_portal",
    "hidroweb.ana.gov.br": "web_portal",
    "app4.mdr.gov.br": "web_portal",
    "sidra.ibge.gov.br": "api_access",
    "earthengine.google.com": "geospatial_platform",
    "dataspace.copernicus.eu": "geospatial_platform",
    "earthexplorer.usgs.gov": "web_portal",
    "firms.modaps.eosdis.nasa.gov": "api_access",
    "data.chc.ucsb.edu": "direct_download",
    "cds.climate.copernicus.eu": "api_access",
    "mapbiomas.org": "geospatial_platform",
    "terrabrasilis.dpi.inpe.br": "web_portal",
    "ana.gov.br": "web_portal",
    "cetesb.sp.gov.br": "web_portal",
    "ibge.gov.br": "web_portal",
    "ons.org.br": "web_portal",
}

_FORMAT_TO_ACCESS: dict[str, str] = {
    "structured": "direct_download",
    "semi_structured": "web_portal",
    "geospatial_platform": "geospatial_platform",
    "pdf_report": "pdf_extraction",
    "academic_paper": "pdf_extraction",
    "unknown": "unknown",
}


class RankAccessAgent(BaseAgent):
    name = "rank-access"

    def __init__(self, *, limit: int = 40) -> None:
        self.limit = limit

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        datasets: list[EnrichedDataset] = context.get("enriched_datasets", [])

        sorted_datasets = sorted(
            datasets,
            key=lambda d: (
                _PRIORITY_ORDER.get(d.track_priority, 9),
                _FORMAT_ORDER.get(d.data_format, 9),
            ),
        )

        if self.limit:
            sorted_datasets = sorted_datasets[: self.limit]

        ranked: list[RankedDataset] = []
        for rank, dataset in enumerate(sorted_datasets, start=1):
            access_type, access_notes = self._classify_access(dataset)
            ranked.append(
                RankedDataset(
                    **dataset.model_dump(),
                    rank=rank,
                    access_type=access_type,
                    access_notes=access_notes,
                )
            )

        format_summary: dict[str, int] = {}
        access_summary: dict[str, int] = {}
        level_summary: dict[str, int] = {}
        for item in ranked:
            format_summary[item.data_format] = format_summary.get(item.data_format, 0) + 1
            access_summary[item.access_type] = access_summary.get(item.access_type, 0) + 1
            level_summary[item.hierarchy_level] = level_summary.get(item.hierarchy_level, 0) + 1

        return {
            "ranked_datasets": ranked,
            "rank_meta": {
                "ranked_count": len(ranked),
                "format_summary": format_summary,
                "access_summary": access_summary,
                "level_summary": level_summary,
            },
        }

    def _classify_access(self, dataset: EnrichedDataset) -> tuple[str, str]:
        if dataset.collection_guide:
            notes: list[str] = []
            if dataset.collection_guide.requires_login:
                notes.append("guia de coleta indica login/cadastro")
            if dataset.collection_guide.estimated_effort:
                notes.append(f"esforco estimado: {dataset.collection_guide.estimated_effort}")

            if dataset.collection_guide.direct_download_urls:
                notes.append("guia de coleta encontrou download direto")
                return "direct_download", "; ".join(notes)

            if dataset.collection_guide.estimated_effort == "requires_contact":
                notes.append("coleta depende de contato institucional")
                return "restricted", "; ".join(notes)

        url_lower = dataset.url.lower()

        # Por extensão de arquivo
        for ext, access in _EXT_ACCESS.items():
            if url_lower.endswith(ext) or f"{ext}?" in url_lower:
                return access, ""

        # Por domínio conhecido
        domain = dataset.source_domain.lower()
        for key, access in _DOMAIN_ACCESS.items():
            if key in domain:
                notes = self._access_notes(domain, access)
                return access, notes

        # Por formato inferido
        access = _FORMAT_TO_ACCESS.get(dataset.data_format, "unknown")
        return access, ""

    @staticmethod
    def _access_notes(domain: str, access_type: str) -> str:
        if "earthengine" in domain:
            return "usar GEE com autenticação OAuth"
        if "copernicus" in domain and "cds" in domain:
            return "requer registro no CDS e cliente cdsapi"
        if "firms" in domain:
            return "API FIRMS — chave gratuita disponível"
        if access_type == "web_portal":
            return "acesso via portal interativo — exportação manual necessária"
        return ""
