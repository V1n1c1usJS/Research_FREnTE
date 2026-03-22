"""Agente para classificar formas de acesso e viabilidade de extracao dos datasets."""

from __future__ import annotations

from typing import Any

from src.agents.base import BaseAgent


class AccessAgent(BaseAgent):
    name = "access"
    prompt_filename = "access_agent.yaml"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.get_system_prompt()

        updated = []
        for dataset in context["datasets"]:
            classification = self._classify_access(dataset)
            links = self._collect_links(dataset)
            documentation_links = self._collect_documentation_links(dataset)
            requires_auth = self._infer_requires_auth(dataset, classification)
            extraction_observations = self._build_extraction_observations(
                dataset=dataset,
                classification=classification,
                requires_auth=requires_auth,
                documentation_links=documentation_links,
            )

            access_notes = (
                f"classification={classification}; access_links={len(links)}; "
                f"documentation_links={len(documentation_links)}; requires_auth={requires_auth}."
            )

            updated.append(
                dataset.model_copy(
                    update={
                        "access_level": classification,
                        "access_notes": access_notes,
                        "access_links": links,
                        "documentation_links": documentation_links,
                        "requires_auth": requires_auth,
                        "formats": sorted(set(dataset.formats)),
                        "extraction_observations": extraction_observations,
                    }
                )
            )

        return {"datasets": updated}

    @staticmethod
    def _classify_access(dataset: Any) -> str:
        lowered_url = str(dataset.source_url).lower()
        lowered_title = str(dataset.title).lower()
        formats = {str(fmt).lower() for fmt in dataset.formats}
        structured_formats = {"csv", "xlsx", "json", "geojson", "shp", "parquet", "netcdf", "geotiff", "zip", "xml"}
        recommended_use = {str(item).lower() for item in getattr(dataset, "recommended_pipeline_use", [])}

        if any(token in lowered_url for token in ["graphql", "/api", "api.", "rest/"]) or "api" in recommended_use:
            return "api"
        if any(token in lowered_url for token in ["wms", "wfs", "wmts", "ows"]) or "ogc" in lowered_title:
            return "ogc"
        if dataset.entity_type in {"documentation", "academic_source"}:
            return "documentation"
        if dataset.source_class == "scientific_knowledge_source":
            return "documentation"
        if dataset.structured_export_available is True or formats & structured_formats:
            return "download_manual"
        if dataset.data_extractability in {"high", "medium"} or dataset.source_class == "analytical_data_source":
            return "portal"
        return "unknown"

    @staticmethod
    def _collect_links(dataset: Any) -> list[str]:
        links = [dataset.source_url, dataset.canonical_url, *dataset.evidence_origin]
        deduped: list[str] = []
        for link in links:
            if isinstance(link, str) and link.startswith("http") and link not in deduped:
                deduped.append(link)
        return deduped

    @staticmethod
    def _collect_documentation_links(dataset: Any) -> list[str]:
        docs: list[str] = []
        for item in dataset.provenance:
            source_type = str(item.get("source_type", ""))
            source_url = str(item.get("source_url", ""))
            if source_type in {"institutional_documentation", "academic_literature", "documentation"}:
                if source_url.startswith("http") and source_url not in docs:
                    docs.append(source_url)
        if dataset.entity_type in {"documentation", "academic_source"} and dataset.source_url.startswith("http"):
            if dataset.source_url not in docs:
                docs.append(dataset.source_url)
        return docs

    @staticmethod
    def _infer_requires_auth(dataset: Any, classification: str) -> bool | None:
        url = str(dataset.source_url).lower()
        if any(token in url for token in ["login", "auth", "token", "signin"]):
            return True
        if classification in {"portal", "api", "ogc", "download_manual"}:
            return False
        return None

    @staticmethod
    def _build_extraction_observations(
        dataset: Any,
        classification: str,
        requires_auth: bool | None,
        documentation_links: list[str],
    ) -> list[str]:
        notes: list[str] = []

        if classification == "api":
            notes.append("Prioritize an HTTP client with pagination, limits and retries.")
        elif classification == "ogc":
            notes.append("Prepare an OGC client (WMS/WFS/WMTS) and validate CRS handling.")
        elif classification == "portal":
            notes.append("Use guided portal navigation and confirm the exact download path manually.")
        elif classification == "download_manual":
            notes.append("Expect manual download of tabular or geospatial files.")
        elif classification == "documentation":
            notes.append("Treat as documentation or scientific evidence and mine citations or linked sources.")
        else:
            notes.append("Access path remains inconclusive and needs manual inspection.")

        if requires_auth is True:
            notes.append("Potential authentication requirement detected from collected links.")
        elif requires_auth is False:
            notes.append("No authentication requirement detected from collected links.")

        if documentation_links:
            notes.append("Supporting documentation links were preserved for manual validation.")

        if not dataset.formats:
            notes.append("No format was inferred; confirm available exports at the source.")

        return notes
