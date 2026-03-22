"""Etapa 2 - enriquece fontes com metadados e guia de coleta opcional."""

from __future__ import annotations

from typing import Any

from src.agents.base import BaseLLMAgent
from src.connectors.firecrawl_collector import FirecrawlCollector
from src.schemas.records import (
    DOMAIN_CATEGORY_OVERRIDES,
    INTENT_TO_CATEGORY,
    TRACK_TO_AXIS,
    TRACK_TO_LEVEL,
    EnrichedDataset,
    FilteredSource,
)

_SYSTEM_PROMPT = """\
Voce e um agente de extracao de metadados de datasets para pesquisa ambiental.

Sua tarefa e analisar o titulo e snippet de uma fonte web e extrair
informacoes estruturadas sobre o dataset que ela oferece.

EXTRAIA APENAS:
1. dataset_name: nome descritivo e curto do dataset (nao o titulo da pagina)
2. dataset_description: o que contem, em 1-2 frases objetivas
3. data_format: o formato dos dados disponiveis
4. temporal_coverage: periodo que os dados cobrem (se mencionado)
5. spatial_coverage: area geografica que os dados cobrem (se mencionado)
6. key_parameters: lista de parametros/variaveis medidas (se mencionados)

NAO FACA:
- Nao classifique o tipo de fonte (ja foi feito)
- Nao atribua scores de relevancia
- Nao invente informacoes que nao estao no titulo ou snippet
- Se uma informacao nao estiver disponivel, use null

REGRAS PARA data_format:
- "structured": CSV, XLSX, Shapefile, GeoTIFF, GeoPackage, NetCDF, API JSON
- "semi_structured": tabelas em HTML, dados em portal interativo (QUALAR, HidroWeb)
- "pdf_report": relatorios em PDF, fichas tecnicas, mapas em PDF
- "academic_paper": artigo cientifico com dados em tabelas/figuras
- "geospatial_platform": Google Earth Engine, plataformas de geoprocessamento
- "unknown": nao e possivel determinar pelo snippet

Responda APENAS com JSON valido, sem markdown, sem texto antes ou depois.
Campos obrigatorios: dataset_name, dataset_description, data_format,
temporal_coverage, spatial_coverage, key_parameters."""

_USER_TEMPLATE = """\
Analise esta fonte e extraia os metadados do dataset.

Titulo: {title}
URL: {url}
Snippet: {snippet}

JSON:"""

_ALLOWED_FORMATS = {
    "structured",
    "semi_structured",
    "pdf_report",
    "academic_paper",
    "geospatial_platform",
    "unknown",
}


class EnrichAgent(BaseLLMAgent):
    name = "enrich"
    prompt_filename = "enrich_agent.yaml"

    def __init__(
        self,
        *,
        llm_connector=None,
        fail_on_error: bool = False,
        firecrawl_api_key: str | None = None,
        firecrawl_timeout_seconds: float = 60.0,
        firecrawl_collector: FirecrawlCollector | None = None,
        skip_collection_guides: bool = False,
    ) -> None:
        super().__init__(llm_connector=llm_connector, fail_on_error=fail_on_error)
        self.skip_collection_guides = skip_collection_guides
        self.firecrawl_error: str | None = None

        if firecrawl_collector is not None:
            self.firecrawl = firecrawl_collector
        else:
            self.firecrawl = None
            if firecrawl_api_key and not skip_collection_guides:
                try:
                    self.firecrawl = FirecrawlCollector(
                        api_key=firecrawl_api_key,
                        timeout_seconds=firecrawl_timeout_seconds,
                    )
                except Exception as exc:  # noqa: BLE001
                    self.firecrawl_error = str(exc)

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        sources: list[FilteredSource] = context.get("filtered_sources", [])
        enriched: list[EnrichedDataset] = []
        llm_count = 0
        error_count = 0
        guide_requested_count = 0
        guide_extracted_count = 0
        guide_fallback_count = 0
        guide_skipped_count = 0

        for source in sources:
            hierarchy_level = self._hierarchy_from_track(source.track_origin)
            thematic_axis = self._axis_from_track(source.track_origin)
            source_category = self._category_from_source(source)

            if self.has_llm:
                try:
                    payload = self.llm_connector.generate_json(
                        system_prompt=_SYSTEM_PROMPT,
                        user_prompt=_USER_TEMPLATE.format(
                            title=source.title,
                            url=source.url,
                            snippet=source.snippet,
                        ),
                        max_output_tokens=400,
                        temperature=0.0,
                    )
                    extracted = self._sanitize_llm_payload(payload, source)
                    llm_count += 1
                    method = "llm"
                    model = self.llm_connector.model
                except Exception:  # noqa: BLE001
                    if self.fail_on_error:
                        raise
                    extracted = self._heuristic_extraction(source)
                    error_count += 1
                    method = "heuristic"
                    model = None
            else:
                extracted = self._heuristic_extraction(source)
                method = "heuristic"
                model = None

            dataset = EnrichedDataset(
                **source.model_dump(),
                hierarchy_level=hierarchy_level,
                thematic_axis=thematic_axis,
                source_category=source_category,
                dataset_name=extracted["dataset_name"],
                dataset_description=extracted["dataset_description"],
                data_format=extracted["data_format"],
                temporal_coverage=extracted["temporal_coverage"],
                spatial_coverage=extracted["spatial_coverage"],
                key_parameters=extracted["key_parameters"],
                enrichment_method=method,
                llm_model=model,
            )

            if self.firecrawl:
                guide_requested_count += 1
                dataset.collection_guide = self.firecrawl.extract_collection_guide(
                    url=source.url,
                    dataset=dataset,
                )
                if any("Extracao automatica falhou" in note for note in dataset.collection_guide.caveats):
                    guide_fallback_count += 1
                else:
                    guide_extracted_count += 1
            else:
                guide_skipped_count += 1

            enriched.append(dataset)

        execution_mode = "heuristic"
        if self.has_llm and llm_count == len(sources):
            execution_mode = "llm"
        elif self.has_llm and llm_count > 0:
            execution_mode = "hybrid"

        return {
            "enriched_datasets": enriched,
            "enrich_meta": {
                "enriched_count": len(enriched),
                "llm_count": llm_count,
                "heuristic_count": len(sources) - llm_count,
                "error_count": error_count,
                "execution_mode": execution_mode,
                "provider": self.llm_connector.provider if self.has_llm else None,
                "model": self.llm_connector.model if self.has_llm else None,
                "collection_guides_enabled": self.firecrawl is not None,
                "collection_guide_requested_count": guide_requested_count,
                "collection_guide_extracted_count": guide_extracted_count,
                "collection_guide_fallback_count": guide_fallback_count,
                "collection_guide_skipped_count": guide_skipped_count,
                "collection_guide_error": self.firecrawl_error,
            },
        }

    @staticmethod
    def _hierarchy_from_track(track: str) -> str:
        for prefix, level in TRACK_TO_LEVEL.items():
            if track.startswith(prefix):
                return level
        return "macro"

    @staticmethod
    def _axis_from_track(track: str) -> str:
        if track in TRACK_TO_AXIS:
            return TRACK_TO_AXIS[track]
        return track.replace("_", " ")

    @staticmethod
    def _category_from_source(source: FilteredSource) -> str:
        domain = source.source_domain.lower()
        for key, cat in DOMAIN_CATEGORY_OVERRIDES.items():
            if key in domain:
                return cat
        return INTENT_TO_CATEGORY.get(source.track_intent, "contextual")

    @staticmethod
    def _sanitize_llm_payload(payload: Any, source: FilteredSource) -> dict[str, Any]:
        if not isinstance(payload, dict):
            return EnrichAgent._heuristic_extraction(source)

        raw_format = str(payload.get("data_format") or "unknown").strip().lower()
        data_format = raw_format if raw_format in _ALLOWED_FORMATS else "unknown"

        def _str(val: Any) -> str:
            return " ".join(str(val or "").split()).strip()

        def _str_or_none(val: Any) -> str | None:
            cleaned = _str(val)
            return cleaned if cleaned else None

        def _list(val: Any) -> list[str]:
            if not isinstance(val, list):
                return []
            return [_str(item) for item in val if _str(item)]

        return {
            "dataset_name": _str(payload.get("dataset_name")) or source.title,
            "dataset_description": _str(payload.get("dataset_description")) or source.snippet[:200],
            "data_format": data_format,
            "temporal_coverage": _str_or_none(payload.get("temporal_coverage")),
            "spatial_coverage": _str_or_none(payload.get("spatial_coverage")),
            "key_parameters": _list(payload.get("key_parameters")),
        }

    @staticmethod
    def _heuristic_extraction(source: FilteredSource) -> dict[str, Any]:
        text = f"{source.url} {source.title} {source.snippet}".lower()

        if any(ext in text for ext in (".csv", ".xlsx", ".xls", ".shp", ".geojson", ".gpkg", ".nc", ".tif")):
            data_format = "structured"
        elif any(kw in text for kw in ("api", "download", "json", "dados abertos", "open data", "series")):
            data_format = "structured"
        elif any(kw in text for kw in ("qualar", "hidroweb", "portal", "painel", "dashboard", "tabela")):
            data_format = "semi_structured"
        elif any(kw in text for kw in (".pdf", "relatorio", "relatorio", "boletim")):
            data_format = "pdf_report"
        elif any(kw in text for kw in ("artigo", "article", "tese", "dissertacao", "doi.org", "scielo", "repositorio")):
            data_format = "academic_paper"
        elif any(kw in text for kw in ("earth engine", "gee", "sentinel", "landsat", "copernicus")):
            data_format = "geospatial_platform"
        else:
            data_format = "unknown"

        return {
            "dataset_name": source.title,
            "dataset_description": source.snippet[:200] if source.snippet else "",
            "data_format": data_format,
            "temporal_coverage": None,
            "spatial_coverage": None,
            "key_parameters": [],
        }
