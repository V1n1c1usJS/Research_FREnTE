"""Agente para classificar formas de acesso e viabilidade de extração dos datasets."""

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
                f"Classificação={classification}; links_acesso={len(links)}; "
                f"links_docs={len(documentation_links)}; requires_auth={requires_auth}."
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
        lowered_name = dataset.source_name.lower()
        lowered_url = dataset.source_url.lower()
        lowered_title = dataset.title.lower()

        if any(token in lowered_url for token in ["api", "arcgis", "ckan"]):
            return "api"
        if any(token in lowered_url for token in ["wms", "wfs", "wmts", "ows"]) or "ogc" in lowered_title:
            return "ogc"
        if dataset.entity_type in {"documentation", "academic_source"}:
            return "documentation"
        if any(token in lowered_name for token in ["hidroweb", "mapbiomas", "ibge", "inpe", "snis", "ana"]):
            return "portal"
        if any(fmt in {"csv", "xlsx", "json", "geojson", "shp"} for fmt in dataset.formats):
            return "download_manual"
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
        url = dataset.source_url.lower()
        if any(token in url for token in ["login", "auth", "token", "signin"]):
            return True
        if classification in {"portal", "api", "ogc", "download_manual"}:
            return False
        if classification in {"documentation", "unknown"}:
            return None
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
            notes.append("Priorizar cliente HTTP com paginação e retries.")
        elif classification == "ogc":
            notes.append("Preparar cliente OGC (WMS/WFS/WMTS) e controle de CRS.")
        elif classification == "portal":
            notes.append("Extração inicial via navegação de portal e download assistido.")
        elif classification == "download_manual":
            notes.append("Download manual previsto para arquivos tabulares/geoespaciais.")
        elif classification == "documentation":
            notes.append("Dataset não diretamente acessível; exige mineração de referências.")
        else:
            notes.append("Fallback mock: acesso desconhecido, requer inspeção manual.")

        if requires_auth is True:
            notes.append("Detectado potencial requisito de autenticação.")
        elif requires_auth is False:
            notes.append("Sem evidência de autenticação obrigatória no modo mock.")

        if documentation_links:
            notes.append("Links de documentação coletados para apoiar plano de extração.")

        if not dataset.formats:
            notes.append("Formato não identificado; confirmar no conector real.")

        return notes
