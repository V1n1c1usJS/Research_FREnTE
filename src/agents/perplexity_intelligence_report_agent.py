"""Agente para consolidar inteligencia de pesquisa coletada no Perplexity."""

from __future__ import annotations

from typing import Any

from src.agents.base import BaseAgent


class PerplexityIntelligenceReportAgent(BaseAgent):
    name = "perplexity-intelligence"
    prompt_filename = "perplexity_intelligence_report_agent.yaml"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.get_system_prompt()
        base_query = context["base_query"]
        master_context = context.get("perplexity_master_context")
        query_plan = context.get("perplexity_search_plan", [])
        sessions = context.get("perplexity_sessions", [])
        categorized_sources = context.get("categorized_sources", [])
        datasets = context.get("datasets", [])
        dataset_candidates = context.get("dataset_candidates", [])
        categorization_meta = context.get("perplexity_categorization_meta", {})
        source_validation_log = context.get("source_validation_log", [])
        source_validation_meta = context.get("source_validation_meta", {})

        official_portals = [
            source for source in categorized_sources if source.category == "official_data_portal"
        ]
        academic_sources = [
            source for source in categorized_sources if source.category in {"academic_source", "repository"}
        ]
        contextual_sources = [
            source
            for source in categorized_sources
            if source.category not in {"official_data_portal", "academic_source", "repository"}
        ]

        top_sessions = [
            {
                "query_id": session.query_id,
                "chat_label": session.chat_label,
                "research_track": session.research_track,
                "research_question": session.research_question,
                "search_profile": session.search_profile,
                "target_intent": session.target_intent,
                "status": session.collection_status,
                "collection_method": session.collection_method,
                "visible_source_count": session.visible_source_count,
                "blockers": session.blockers,
                "notes": session.notes,
            }
            for session in sessions
        ]
        track_coverage = self._build_track_coverage(
            query_plan=query_plan,
            sessions=sessions,
            categorized_sources=categorized_sources,
            dataset_candidates=dataset_candidates,
            datasets=datasets,
        )

        intelligence_payload = {
            "base_query": base_query,
            "master_context": master_context.model_dump(mode="json") if hasattr(master_context, "model_dump") else master_context,
            "search_plan": [
                {
                    "query_id": item.query_id,
                    "chat_label": item.chat_label,
                    "research_track": item.research_track,
                    "research_question": item.research_question,
                    "search_profile": item.search_profile,
                    "target_intent": item.target_intent,
                    "query_text": item.query_text,
                }
                for item in query_plan
            ],
            "collection_summary": {
                "session_count": len(sessions),
                "categorized_source_count": len(categorized_sources),
                "validated_source_count": len(source_validation_log),
                "dataset_candidate_count": len(dataset_candidates),
                "dataset_count": len(datasets),
                "categorization_meta": categorization_meta,
                "source_validation_meta": source_validation_meta,
            },
            "official_portals": [self._source_payload(item) for item in official_portals[:15]],
            "academic_sources": [self._source_payload(item) for item in academic_sources[:15]],
            "contextual_sources": [self._source_payload(item) for item in contextual_sources[:15]],
            "dataset_catalog": [self._dataset_payload(item) for item in datasets[:20]],
            "dataset_candidates": [self._candidate_payload(item) for item in dataset_candidates[:20]],
            "session_diagnostics": top_sessions,
            "track_coverage": track_coverage,
            "source_validation_summary": {
                "validated_source_count": len(source_validation_log),
                "status_summary": source_validation_meta.get("status_summary", {}),
                "manual_validation_required_count": source_validation_meta.get("manual_validation_required_count", 0),
                "adjusted_source_count": source_validation_meta.get("adjusted_source_count", 0),
                "issue_summary": source_validation_meta.get("issue_summary", {}),
            },
            "validation_diagnostics": [
                self._validation_payload(item) for item in source_validation_log[:20]
            ],
            "recommended_next_steps": self._recommended_next_steps(
                official_portals=official_portals,
                academic_sources=academic_sources,
                datasets=datasets,
                source_validation_meta=source_validation_meta,
            ),
        }

        lines = [
            "# Consolidado de Inteligencia - Perplexity Search API",
            "",
            "## Contexto Mestre",
            f"- Query base: `{base_query}`",
        ]
        if master_context:
            lines.extend(
                [
                    f"- Objetivo do artigo: `{master_context.article_goal}`",
                    f"- Escopo geografico: `{', '.join(master_context.geographic_scope)}`",
                    f"- Eixos tematicos: `{', '.join(master_context.thematic_axes)}`",
                    f"- Fontes preferidas: `{', '.join(master_context.preferred_sources)}`",
                ]
            )

        lines.extend(
            [
                "",
                "## Chats Planejados",
                f"- Total de chats tematicos: `{len(query_plan)}`",
            ]
        )
        for item in intelligence_payload["search_plan"]:
            lines.append(
                f"- `{item['query_id']}` | chat={item['chat_label']} | trilha={item['research_track']} "
                f"| alvo={item['target_intent']} | pergunta=`{item['research_question']}`"
            )

        lines.extend(
            [
                "",
                "## Coleta",
                f"- Sessoes coletadas: `{len(sessions)}`",
                f"- Fontes categorizadas: `{len(categorized_sources)}`",
                f"- Fontes validadas: `{len(source_validation_log)}`",
                f"- Candidatos a dataset: `{len(dataset_candidates)}`",
                f"- Datasets normalizados: `{len(datasets)}`",
                "",
                "## Diagnostico da coleta",
            ]
        )

        if not top_sessions:
            lines.append("- Nenhuma sessao coletada.")
        else:
            for item in top_sessions:
                lines.append(
                    f"- `{item['query_id']}` | chat={item['chat_label']} | trilha={item['research_track']} "
                    f"| perfil={item['search_profile']} | alvo={item['target_intent']} "
                    f"| metodo={item['collection_method']} | status={item['status']} "
                    f"| fontes_visiveis={item['visible_source_count']}"
                )
                if item["blockers"]:
                    lines.append(f"  bloqueios: {', '.join(item['blockers'])}")
                if item["notes"]:
                    lines.append(f"  notas: {', '.join(item['notes'][:2])}")

        lines.extend(["", "## Cobertura por trilha"])
        for item in track_coverage:
            lines.append(
                f"- `{item['research_track']}` | chat={item['chat_label']} | alvo={item['target_intent']} "
                f"| sessao={item['session_status']} | fontes={item['categorized_source_count']} "
                f"| candidatos={item['dataset_candidate_count']} | datasets={item['dataset_count']}"
            )

        lines.extend(["", "## Validacao das fontes"])
        if source_validation_log:
            lines.append(f"- Fontes auditadas: `{len(source_validation_log)}`")
            lines.append(
                f"- Ajustadas: `{source_validation_meta.get('adjusted_source_count', 0)}` | "
                f"validacao manual requerida: `{source_validation_meta.get('manual_validation_required_count', 0)}`"
            )
            status_summary = source_validation_meta.get("status_summary", {})
            if status_summary:
                lines.append(
                    "- Status: "
                    + ", ".join(f"{status}={count}" for status, count in sorted(status_summary.items()))
                )
            issue_summary = source_validation_meta.get("issue_summary", {})
            if issue_summary:
                top_issues = sorted(issue_summary.items(), key=lambda item: (-item[1], item[0]))[:5]
                lines.append(
                    "- Principais sinais de alerta: "
                    + ", ".join(f"{issue}={count}" for issue, count in top_issues)
                )
        else:
            lines.append("- Nenhum registro de validacao de fonte foi produzido.")

        lines.extend(["", "## Portais e fontes com sinal de dataset"])
        if official_portals:
            for item in official_portals[:12]:
                lines.append(
                    f"- **{item.title}** | dominio={item.domain} | prioridade={item.priority} "
                    f"| evidencias={item.evidence_count} | trilhas={', '.join(item.research_tracks[:2]) or 'n/a'} "
                    f"| datasets={', '.join(item.dataset_names_mentioned[:2]) or 'n/a'}"
                )
        else:
            lines.append("- Nenhuma fonte com categoria de portal oficial consolidada.")

        lines.extend(["", "## Conhecimento academico e repositorios"])
        if academic_sources:
            for item in academic_sources[:12]:
                lines.append(
                    f"- **{item.title}** | dominio={item.domain} | article_value={item.article_value} "
                    f"| trilhas={', '.join(item.research_tracks[:2]) or 'n/a'} "
                    f"| snippets={item.snippets[0] if item.snippets else 'n/a'}"
                )
        else:
            lines.append("- Nenhuma fonte academica consolidada.")

        lines.extend(["", "## Catalogo sintetico de datasets"])
        if datasets:
            for item in datasets[:12]:
                lines.append(
                    f"- `{item.dataset_id}` | **{item.title}** | score={item.relevance_score} "
                    f"| acesso={item.access_level} | fonte={item.source_name}"
                )
        else:
            lines.append("- A coleta gerou inteligencia de fontes, mas ainda sem datasets normalizados.")

        lines.extend(["", "## Proximos passos sugeridos"])
        for step in intelligence_payload["recommended_next_steps"]:
            lines.append(f"- {step}")

        return {
            "intelligence_payload": intelligence_payload,
            "intelligence_markdown": "\n".join(lines),
            "intelligence_meta": {
                "execution_mode": "heuristic",
                "provider": None,
                "model": None,
                "error": None,
            },
        }

    @staticmethod
    def _source_payload(item: Any) -> dict[str, Any]:
        return {
            "source_id": item.source_id,
            "title": item.title,
            "url": item.url,
            "domain": item.domain,
            "category": item.category,
            "target_intent": item.target_intent,
            "priority": item.priority,
            "dataset_signal": item.dataset_signal,
            "academic_signal": item.academic_signal,
            "official_signal": item.official_signal,
            "evidence_count": item.evidence_count,
            "search_profiles": item.search_profiles,
            "research_tracks": item.research_tracks,
            "dataset_names_mentioned": item.dataset_names_mentioned,
            "variables_mentioned": item.variables_mentioned,
            "snippets": item.snippets[:2],
            "rationale": item.rationale,
        }

    @staticmethod
    def _dataset_payload(item: Any) -> dict[str, Any]:
        return {
            "dataset_id": item.dataset_id,
            "title": item.title,
            "source_name": item.source_name,
            "source_url": item.source_url,
            "relevance_score": item.relevance_score,
            "priority": item.priority,
            "access_level": item.access_level,
            "research_tracks": item.research_tracks,
            "search_profiles": item.search_profiles,
            "target_intents": item.target_intents,
            "variables_normalized": item.variables_normalized,
        }

    @staticmethod
    def _candidate_payload(item: Any) -> dict[str, Any]:
        return {
            "candidate_id": item.candidate_id,
            "dataset_name": item.dataset_name,
            "candidate_role": item.candidate_role,
            "canonical_url": item.canonical_url,
            "accessibility": item.accessibility,
            "verifiability_status": item.verifiability_status,
            "confidence_hint": item.confidence_hint,
            "research_tracks": item.research_tracks,
            "search_profiles": item.search_profiles,
            "target_intents": item.target_intents,
        }

    @staticmethod
    def _validation_payload(item: Any) -> dict[str, Any]:
        return {
            "source_id": item.source_id,
            "title": item.title,
            "validation_status": item.validation_status,
            "validation_score": item.validation_score,
            "manual_validation_required": item.manual_validation_required,
            "issues": item.issues,
            "adjustments": item.adjustments,
        }

    @staticmethod
    def _build_track_coverage(
        *,
        query_plan: list[Any],
        sessions: list[Any],
        categorized_sources: list[Any],
        dataset_candidates: list[Any],
        datasets: list[Any],
    ) -> list[dict[str, Any]]:
        coverage: list[dict[str, Any]] = []
        session_by_track = {session.research_track: session for session in sessions}

        for track in query_plan:
            coverage.append(
                {
                    "research_track": track.research_track,
                    "chat_label": track.chat_label,
                    "target_intent": track.target_intent,
                    "session_status": session_by_track.get(track.research_track).collection_status
                    if session_by_track.get(track.research_track)
                    else "not_collected",
                    "categorized_source_count": sum(
                        1 for source in categorized_sources if track.research_track in getattr(source, "research_tracks", [])
                    ),
                    "dataset_candidate_count": sum(
                        1
                        for candidate in dataset_candidates
                        if track.research_track in getattr(candidate, "research_tracks", [])
                    ),
                    "dataset_count": sum(
                        1 for dataset in datasets if track.research_track in getattr(dataset, "research_tracks", [])
                    ),
                }
            )

        return coverage

    @staticmethod
    def _recommended_next_steps(
        *,
        official_portals: list[Any],
        academic_sources: list[Any],
        datasets: list[Any],
        source_validation_meta: dict[str, Any],
    ) -> list[str]:
        steps: list[str] = []
        if official_portals:
            steps.append("Abrir manualmente as fontes com maior sinal de dado e confirmar filtros, formatos e caminhos de exportacao.")
        if academic_sources:
            steps.append("Usar as fontes academicas para levantar variaveis, recortes e bases citadas que merecem nova rodada de busca.")
        if source_validation_meta.get("manual_validation_required_count", 0):
            steps.append("Revisar manualmente as fontes com evidencia fraca ou ajustes aplicados antes de promover novos candidatos a dataset.")
        if datasets:
            steps.append("Priorizar os datasets com maior score para documentacao metodologica e verificacao manual de acesso.")
        else:
            steps.append("Refinar o contexto mestre e as trilhas tematicas para abrir novas buscas mais especificas e menos ruidosas.")
        steps.append("Revisar fontes recorrentes, remover redundancias e registrar quais trilhas geraram os melhores resultados.")
        return steps
