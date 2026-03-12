"""Agente para descoberta simulada de datasets."""

from __future__ import annotations

from typing import Any

from src.agents.base import BaseAgent


class DatasetDiscoveryAgent(BaseAgent):
    name = "dataset-discovery"
    prompt_filename = "dataset_discovery_agent.txt"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.get_system_prompt()
        sources = context["sources"]
        query_tracks = context["expanded_queries"]
        limit = context["settings"].limit

        source_index = {source.source_id: source for source in sources}
        mock_blueprints = [
            {
                "dataset_id": "mock-ana-qualidade-agua",
                "source_id": "src-ana",
                "title": "Série Histórica de Qualidade da Água em Pontos do Rio Tietê",
                "description": "Registros simulados de parâmetros físico-químicos em pontos de monitoramento.",
                "dataset_kind": "water-quality",
                "temporal_coverage": "2010-2023",
                "spatial_coverage": "Trecho médio e baixo do Rio Tietê",
                "update_frequency": "mensal",
                "formats": ["csv", "xlsx"],
                "tags": ["qualidade da água", "rio tietê", "monitoramento"],
                "priority_hint": "high",
                "methodological_notes": [
                    "Dataset mock inspirado em estruturas de monitoramento hidrológico.",
                    "Não representa consulta direta à base oficial.",
                ],
            },
            {
                "dataset_id": "mock-hidroweb-vazao",
                "source_id": "src-hidroweb",
                "title": "Séries de Vazão e Nível em Estações Hidrométricas do Corredor Tietê",
                "description": "Série simulada de vazão e cotas para análise hidrológica de impacto.",
                "dataset_kind": "hydrology",
                "temporal_coverage": "1995-2023",
                "spatial_coverage": "Bacia do Tietê até conexão com Jupiá",
                "update_frequency": "diária",
                "formats": ["csv"],
                "tags": ["hidrologia", "vazão", "nível"],
                "priority_hint": "high",
                "methodological_notes": [
                    "Compatível com análise temporal de extremos hidrológicos.",
                ],
            },
            {
                "dataset_id": "mock-mapbiomas-uso-solo",
                "source_id": "src-mapbiomas",
                "title": "Cobertura e Uso do Solo na Bacia do Tietê",
                "description": "Recortes simulados de classes de uso do solo por ano para análise de pressão antrópica.",
                "dataset_kind": "land-use",
                "temporal_coverage": "1985-2022",
                "spatial_coverage": "São Paulo a Três Lagoas",
                "update_frequency": "anual",
                "formats": ["geotiff", "csv"],
                "tags": ["uso do solo", "mapbiomas", "pressão antrópica"],
                "priority_hint": "high",
                "methodological_notes": [
                    "Relevante para relacionar mudanças de cobertura com qualidade da água.",
                ],
            },
            {
                "dataset_id": "mock-inpe-clima",
                "source_id": "src-inpe",
                "title": "Indicadores Climáticos e Eventos Extremos no Centro-Sul",
                "description": "Série simulada de precipitação e temperatura para contextualizar variabilidade hidrológica.",
                "dataset_kind": "climate",
                "temporal_coverage": "2000-2023",
                "spatial_coverage": "Centro-Sul com recorte para bacia do Tietê",
                "update_frequency": "mensal",
                "formats": ["csv", "netcdf"],
                "tags": ["clima", "precipitação", "eventos extremos"],
                "priority_hint": "medium",
                "methodological_notes": [
                    "Complementar para explicar variabilidade de séries de água e vazão.",
                ],
            },
            {
                "dataset_id": "mock-ibge-municipal",
                "source_id": "src-ibge",
                "title": "Indicadores Municipais no Eixo São Paulo-Três Lagoas",
                "description": "Conjunto simulado de população, urbanização e atividade econômica por município.",
                "dataset_kind": "socioeconomic",
                "temporal_coverage": "2010-2022",
                "spatial_coverage": "Municípios do corredor São Paulo-Três Lagoas",
                "update_frequency": "anual",
                "formats": ["csv"],
                "tags": ["municípios", "demografia", "pressão urbana"],
                "priority_hint": "medium",
                "methodological_notes": [
                    "Base de apoio para contextualização de impactos antrópicos.",
                ],
            },
            {
                "dataset_id": "mock-snis-saneamento",
                "source_id": "src-snis",
                "title": "Indicadores de Saneamento e Esgotamento Sanitário",
                "description": "Série simulada de cobertura de coleta e tratamento de esgoto em municípios-chave.",
                "dataset_kind": "sanitation",
                "temporal_coverage": "2012-2022",
                "spatial_coverage": "Municípios com influência no Rio Tietê",
                "update_frequency": "anual",
                "formats": ["csv", "pdf"],
                "tags": ["snis", "saneamento", "esgoto"],
                "priority_hint": "high",
                "methodological_notes": [
                    "Importante para inferir pressão sobre qualidade hídrica.",
                ],
            },
            {
                "dataset_id": "mock-academic-relatorios",
                "source_id": "src-academic",
                "title": "Relatórios Técnicos e Estudos Acadêmicos sobre Tietê-Jupiá",
                "description": "Inventário simulado de literatura técnica com métodos e evidências relevantes.",
                "dataset_kind": "literature",
                "temporal_coverage": "2015-2024",
                "spatial_coverage": "Rio Tietê e Reservatório de Jupiá",
                "update_frequency": "irregular",
                "formats": ["pdf", "bibtex"],
                "tags": ["literatura", "relatório técnico", "metodologia"],
                "priority_hint": "medium",
                "methodological_notes": [
                    "Usado para triangulação de hipóteses e limitações de dados.",
                ],
            },
        ]

        raw_datasets: list[dict[str, Any]] = []
        for idx in range(limit):
            blueprint = mock_blueprints[idx % len(mock_blueprints)]
            source = source_index[blueprint["source_id"]]
            query_track = query_tracks[idx % len(query_tracks)]

            raw_datasets.append(
                {
                    **blueprint,
                    "dataset_id": f"{blueprint['dataset_id']}-{idx + 1:02d}",
                    "source_name": source.name,
                    "source_url": f"{source.base_url}/mock-datasets/{idx + 1}",
                    "query_used": query_track["query"],
                    "query_focus": query_track["focus"],
                    "discovery_stage": query_track["stage"],
                    "evidence_origin": [
                        f"Fonte inspiradora: {source.name}",
                        f"Consulta simulada: {query_track['query']}",
                    ],
                }
            )

        return {"raw_datasets": raw_datasets}
