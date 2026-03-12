"""Agente para mapear fontes iniciais de pesquisa."""

from __future__ import annotations

from typing import Any

from src.agents.base import BaseAgent
from src.schemas.records import ResearchSourceRecord


class ResearchScoutAgent(BaseAgent):
    name = "research-scout"
    prompt_filename = "research_scout_agent.txt"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        _prompt = self.get_system_prompt()
        query = context["settings"].query

        sources = [
            ResearchSourceRecord(
                source_id="src-ana",
                name="ANA",
                base_url="https://www.gov.br/ana",
                source_type="official",
                citation="Agência Nacional de Águas e Saneamento Básico",
                query=query,
                priority="high",
                methodological_note="Fonte regulatória para hidrologia, qualidade e usos da água.",
            ),
            ResearchSourceRecord(
                source_id="src-hidroweb",
                name="Hidroweb",
                base_url="https://www.snirh.gov.br/hidroweb",
                source_type="official",
                citation="Plataforma Hidroweb / SNIRH",
                query=query,
                priority="high",
                methodological_note="Séries hidrológicas para contexto do Rio Tietê e afluentes.",
            ),
            ResearchSourceRecord(
                source_id="src-mapbiomas",
                name="MapBiomas",
                base_url="https://mapbiomas.org",
                source_type="scientific",
                citation="Coleções MapBiomas",
                query=query,
                priority="high",
                methodological_note="Cobertura e uso do solo para pressão antrópica na bacia.",
            ),
            ResearchSourceRecord(
                source_id="src-inpe",
                name="INPE",
                base_url="https://www.gov.br/inpe",
                source_type="official",
                citation="Instituto Nacional de Pesquisas Espaciais",
                query=query,
                priority="medium",
                methodological_note="Produtos remotos e séries ambientais complementares.",
            ),
            ResearchSourceRecord(
                source_id="src-ibge",
                name="IBGE",
                base_url="https://www.ibge.gov.br",
                source_type="official",
                citation="Instituto Brasileiro de Geografia e Estatística",
                query=query,
                priority="medium",
                methodological_note="Indicadores territoriais e socioeconômicos de apoio.",
            ),
            ResearchSourceRecord(
                source_id="src-snis",
                name="SNIS",
                base_url="https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/snis",
                source_type="official",
                citation="Sistema Nacional de Informações sobre Saneamento",
                query=query,
                priority="medium",
                methodological_note="Saneamento e infraestrutura com impacto em corpos hídricos.",
            ),
            ResearchSourceRecord(
                source_id="src-academic",
                name="Bases Acadêmicas e Relatórios Técnicos",
                base_url="https://exemplo.local/academic-catalog",
                source_type="academic",
                citation="Repositórios institucionais e literatura técnica (mock)",
                query=query,
                priority="medium",
                methodological_note="Usado para complementar lacunas e triangulação metodológica.",
            ),
        ]
        return {"sources": sources}
