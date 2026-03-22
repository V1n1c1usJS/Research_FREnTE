"""Etapa 4 — gera relatório analítico com lacunas e próximos passos (LLM opcional)."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from src.agents.base import BaseLLMAgent
from src.schemas.records import RankedDataset

_SYSTEM_PROMPT = """\
Você é o agente de relatórios do projeto 100K.

O projeto 100K investiga como pressões antrópicas na bacia do Rio Tietê
(São Paulo → Três Lagoas) influenciam a dinâmica do material orgânico
nos reservatórios em cascata.

Sua tarefa é sintetizar os datasets descobertos em um relatório que ajude
o pesquisador a agir. O relatório deve conter:

1. COBERTURA POR NÍVEL: quantos datasets foram encontrados em cada nível
   (macro, meso, bridge, micro) e quais eixos temáticos estão cobertos.

2. COBERTURA POR FORMATO: quantos são download direto vs portal vs PDF.
   Isso determina quanto trabalho de ETL o pesquisador vai ter.

3. LACUNAS: quais variáveis ou fontes esperadas NÃO apareceram.
   Comparar com esta lista de fontes prioritárias:
   - ANA HidroWeb (hidrologia)
   - CETESB QUALAR (qualidade água)
   - SNIS (saneamento)
   - MapBiomas (uso do solo)
   - INPE PRODES/DETER (desmatamento)
   - INPE BDQueimadas (queimadas)
   - ONS (operação reservatórios)
   - IBGE SIDRA (demografia, agropecuária)
   - Sentinel-2 / Landsat (sensoriamento remoto)
   - Artigos CDOM/MOD nos reservatórios do Tietê

4. PRÓXIMOS PASSOS: quais buscas adicionais fazer, quais fontes
   acessar manualmente, quais validações cruzadas priorizar:
   - SNIS × CETESB DBO (consistência esgoto)
   - MapBiomas × CETESB turbidez (causa-efeito desmatamento)
   - Clorofila in situ × satélite (calibração SR)
   - Uso do solo × COT reservatórios (hipótese central)

Formato: Markdown, técnico mas legível, máximo 1500 palavras.
Não use bullet points excessivos — prefira parágrafos curtos e diretos."""

_USER_TEMPLATE = """\
Datasets descobertos ({total} no total):

{datasets_json}

Trilhas executadas:
{search_plan_summary}

Gere o relatório analítico."""


class ReportAgent(BaseLLMAgent):
    name = "report"
    prompt_filename = "report_agent.yaml"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        ranked: list[RankedDataset] = context.get("ranked_datasets", [])
        search_plan = context.get("perplexity_search_plan", [])
        sessions = context.get("perplexity_sessions", [])
        filter_meta = context.get("filter_meta", {})
        enrich_meta = context.get("enrich_meta", {})
        rank_meta = context.get("rank_meta", {})
        base_query = context.get("base_query", "")

        intelligence_payload = self._build_payload(
            ranked=ranked,
            search_plan=search_plan,
            sessions=sessions,
            filter_meta=filter_meta,
            enrich_meta=enrich_meta,
            rank_meta=rank_meta,
            base_query=base_query,
        )

        if self.has_llm and ranked:
            try:
                markdown = self._generate_llm_report(ranked=ranked, search_plan=search_plan)
                report_meta = {
                    "execution_mode": "llm",
                    "provider": self.llm_connector.provider,
                    "model": self.llm_connector.model,
                    "error": None,
                }
            except Exception as exc:  # noqa: BLE001
                if self.fail_on_error:
                    raise
                markdown = self._generate_template_report(ranked=ranked, rank_meta=rank_meta)
                report_meta = {
                    "execution_mode": "heuristic_fallback",
                    "provider": None,
                    "model": None,
                    "error": str(exc),
                }
        else:
            markdown = self._generate_template_report(ranked=ranked, rank_meta=rank_meta)
            report_meta = {
                "execution_mode": "heuristic",
                "provider": None,
                "model": None,
                "error": None,
            }

        return {
            "intelligence_payload": intelligence_payload,
            "intelligence_markdown": markdown,
            "report_meta": report_meta,
        }

    def _generate_llm_report(
        self,
        *,
        ranked: list[RankedDataset],
        search_plan: list[Any],
    ) -> str:
        datasets_json = json.dumps(
            [self._dataset_summary(d) for d in ranked[:30]],
            ensure_ascii=False,
            indent=2,
        )
        search_plan_summary = "\n".join(
            f"- {getattr(q, 'research_track', '')} | {getattr(q, 'target_intent', '')} | {getattr(q, 'priority', '')}"
            for q in search_plan
        )
        user_prompt = _USER_TEMPLATE.format(
            total=len(ranked),
            datasets_json=datasets_json,
            search_plan_summary=search_plan_summary,
        )
        return self.llm_connector.generate_text(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_output_tokens=3000,
            temperature=0.3,
        )

    @staticmethod
    def _generate_template_report(
        *,
        ranked: list[RankedDataset],
        rank_meta: dict[str, Any],
    ) -> str:
        level_summary = rank_meta.get("level_summary", {})
        format_summary = rank_meta.get("format_summary", {})
        access_summary = rank_meta.get("access_summary", {})

        axes = sorted({d.thematic_axis for d in ranked if d.thematic_axis})
        tracks_covered = sorted({d.track_origin for d in ranked if d.track_origin})

        lines = [
            "# Relatório de Inteligência — Projeto 100K",
            "",
            "## Cobertura por nível hierárquico",
        ]
        for level in ("macro", "meso", "bridge", "micro"):
            count = level_summary.get(level, 0)
            lines.append(f"- **{level}**: {count} datasets")

        lines += ["", "## Eixos temáticos cobertos"]
        if axes:
            for axis in axes:
                lines.append(f"- {axis}")
        else:
            lines.append("- Nenhum eixo temático identificado.")

        lines += ["", "## Cobertura por formato"]
        for fmt, count in sorted(format_summary.items(), key=lambda x: -x[1]):
            lines.append(f"- **{fmt}**: {count}")

        lines += ["", "## Tipo de acesso"]
        for acc, count in sorted(access_summary.items(), key=lambda x: -x[1]):
            lines.append(f"- **{acc}**: {count}")

        lines += ["", "## Trilhas executadas"]
        for track in tracks_covered:
            lines.append(f"- {track}")

        lines += [
            "",
            "## Próximos passos",
            "- Verificar manualmente as fontes com access_type=web_portal para confirmar filtros e caminhos de exportação.",
            "- Cruzar SNIS × CETESB DBO para validar consistência dos dados de esgoto.",
            "- Priorizar fontes com data_format=structured para ingestão direta no pipeline analítico.",
            "- Refinar as buscas para trilhas com poucos resultados ou ausência de fontes prioritárias.",
        ]

        return "\n".join(lines)

    @staticmethod
    def _build_payload(
        *,
        ranked: list[RankedDataset],
        search_plan: list[Any],
        sessions: list[Any],
        filter_meta: dict[str, Any],
        enrich_meta: dict[str, Any],
        rank_meta: dict[str, Any],
        base_query: str,
    ) -> dict[str, Any]:
        track_coverage = []
        for query in search_plan:
            track = getattr(query, "research_track", "")
            session = next((s for s in sessions if s.research_track == track), None)
            datasets_in_track = [d for d in ranked if d.track_origin == track]
            track_coverage.append(
                {
                    "research_track": track,
                    "chat_label": getattr(query, "chat_label", ""),
                    "target_intent": getattr(query, "target_intent", ""),
                    "session_status": session.collection_status if session else "not_collected",
                    "dataset_count": len(datasets_in_track),
                    "direct_download_count": sum(1 for d in datasets_in_track if d.access_type == "direct_download"),
                }
            )

        return {
            "base_query": base_query,
            "search_plan_count": len(search_plan),
            "session_count": len(sessions),
            "filtered_source_count": filter_meta.get("filtered_source_count", 0),
            "enriched_dataset_count": enrich_meta.get("enriched_count", 0),
            "ranked_dataset_count": rank_meta.get("ranked_count", 0),
            "filter_meta": filter_meta,
            "enrich_meta": enrich_meta,
            "rank_meta": rank_meta,
            "track_coverage": track_coverage,
            "top_datasets": [ReportAgent._dataset_summary(d) for d in ranked[:20]],
        }

    @staticmethod
    def _dataset_summary(d: RankedDataset) -> dict[str, Any]:
        return {
            "rank": d.rank,
            "title": d.title,
            "url": d.url,
            "track_origin": d.track_origin,
            "track_priority": d.track_priority,
            "hierarchy_level": d.hierarchy_level,
            "thematic_axis": d.thematic_axis,
            "source_category": d.source_category,
            "dataset_name": d.dataset_name,
            "data_format": d.data_format,
            "access_type": d.access_type,
            "access_notes": d.access_notes,
            "temporal_coverage": d.temporal_coverage,
            "spatial_coverage": d.spatial_coverage,
            "key_parameters": d.key_parameters,
        }
