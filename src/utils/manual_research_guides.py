"""Helpers to build manual research guides for discovered sources."""

from __future__ import annotations

from typing import Any
import unicodedata
from urllib.parse import urlparse


def build_manual_research_guides(datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    guides: list[dict[str, Any]] = []
    for dataset in datasets:
        guide = _guide_for_dataset(dataset)
        if guide:
            guides.append(_sanitize_value(guide))

    guides.sort(key=lambda item: (item["category"], item["title"]))
    return guides


def build_default_manual_research_guides() -> list[dict[str, Any]]:
    seed_datasets = [
        {
            "title": "Hidroweb",
            "canonical_url": "https://www.snirh.gov.br/hidroweb",
            "access_level": "portal",
            "source_class": "analytical_data_source",
        },
        {
            "title": "MapBiomas",
            "canonical_url": "https://mapbiomas.org",
            "access_level": "portal",
            "source_class": "analytical_data_source",
        },
        {
            "title": "SIDRA - IBGE",
            "canonical_url": "https://sidra.ibge.gov.br/",
            "access_level": "portal",
            "source_class": "analytical_data_source",
        },
        {
            "title": "SNIS",
            "canonical_url": "https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/snis",
            "access_level": "portal",
            "source_class": "analytical_data_source",
        },
        {
            "title": "Programa Queimadas - INPE",
            "canonical_url": "https://terrabrasilis.dpi.inpe.br/queimadas/portal/",
            "access_level": "portal",
            "source_class": "analytical_data_source",
        },
        {
            "title": "SciELO",
            "canonical_url": "https://www.scielo.br/",
            "access_level": "documentation",
            "source_class": "scientific_knowledge_source",
        },
    ]
    return build_manual_research_guides(seed_datasets)


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sanitize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, str):
        return _clean_text(value)
    return value


def _clean_text(value: str) -> str:
    text = str(value).strip()
    if not text:
        return text

    repaired = text
    if any(marker in repaired for marker in ("Ãƒ", "Ã‚", "Ã¢", "ï¿½")):
        try:
            repaired = repaired.encode("latin-1").decode("utf-8")
        except UnicodeError:
            repaired = text

    normalized = unicodedata.normalize("NFKD", repaired)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_text or repaired


def render_manual_research_guides_markdown(
    *,
    bootstrap_id: str,
    guides: list[dict[str, Any]],
) -> str:
    lines = [
        f"# Consolidado de Pesquisa Manual - {bootstrap_id}",
        "",
        "Este consolidado prioriza o caminho para chegar ao dado no portal, com foco em navegacao, filtros e estrategia de pesquisa.",
        "",
        "Nota de validacao: a confirmacao pratica desta rodada foi feita em navegador real via Playwright CLI Skill.",
        "Por isso, `validated_via_browser` pode ser `true` mesmo quando `validated_via_mcp` for `false`.",
        "",
    ]

    grouped = {
        "dados_analiticos": [item for item in guides if item["category"] == "dados_analiticos"],
        "literatura_documentacao": [item for item in guides if item["category"] == "literatura_documentacao"],
    }

    for category, items in grouped.items():
        if not items:
            continue

        title = "Dados Analiticos" if category == "dados_analiticos" else "Literatura e Documentacao"
        lines.extend([f"## {title}", ""])

        for item in items:
            lines.extend(
                [
                    f"### {item['title']}",
                    "",
                    f"- Tipo: `{item['category']}`",
                    f"- Entrada principal: `{item['entrypoint_url']}`",
                    f"- Link direto util: `{item['direct_access_url']}`",
                    f"- Modo de acesso: `{item['access_mode']}`",
                    f"- Validado via MCP: `{item['validated_via_mcp']}`",
                    f"- Validado em browser real: `{item['validated_via_browser']}`",
                    f"- Metodo de validacao: `{item['validation_method']}`",
                    f"- Exige autenticacao: `{item['requires_auth']}`",
                    "",
                    "Passo a passo:",
                ]
            )
            for step in item["navigation_steps"]:
                lines.append(f"- {step}")
            lines.extend(["", "Passo a passo validado:"])
            for step in item["exact_navigation_steps"]:
                lines.append(f"- {step}")
            lines.extend(["", "Labels visiveis na interface:"])
            for label in item["visible_ui_labels"]:
                lines.append(f"- {label}")
            lines.extend(["", "Filtros do portal:"])
            for step in item["portal_filters"]:
                lines.append(f"- {step}")
            lines.extend(["", "Filtros do estudo:"])
            for step in item["study_filters"]:
                lines.append(f"- {step}")
            lines.extend(["", "Valores recomendados para o estudo 100K:"])
            for field_name, values in item["recommended_filter_values_for_100k"].items():
                lines.append(f"- {field_name}: {', '.join(values)}")
            lines.extend(["", "Caminho de download ou exportacao:"])
            lines.append(f"- Resumo: {item['download_or_export_path'].get('summary', '')}")
            for step in item["download_or_export_path"].get("steps", []):
                lines.append(f"- {step}")
            for label in item["download_or_export_path"].get("observed_controls", []):
                lines.append(f"- Controle observado: {label}")
            for url in item["download_or_export_path"].get("observed_urls", []):
                lines.append(f"- URL observada: `{url}`")
            lines.extend(["", "Formatos observados:"])
            for fmt in item["available_formats"]:
                lines.append(f"- {fmt}")
            lines.extend(["", "Termos de busca recomendados:"])
            for term in item["search_terms"]:
                lines.append(f"- `{term}`")
            lines.extend(["", "Saidas esperadas:"])
            for output in item["expected_outputs"]:
                lines.append(f"- {output}")
            lines.extend(["", "Referencias oficiais:"])
            for ref in item["official_reference_urls"]:
                lines.append(f"- `{ref}`")
            lines.extend(["", "Bloqueios:"])
            if item["blockers"]:
                for blocker in item["blockers"]:
                    lines.append(f"- {blocker}")
            else:
                lines.append("- Nenhum bloqueio publico relevante observado nesta rodada.")
            lines.extend(["", "Observacoes:"])
            for note in item["notes"]:
                lines.append(f"- {note}")
            lines.append("")

    if not guides:
        lines.append("Nenhum guia manual foi gerado para esta inicializacao.")

    return "\n".join(lines)


def _guide_for_dataset(dataset: dict[str, Any]) -> dict[str, Any] | None:
    url = str(dataset.get("canonical_url", "")).lower()
    title = str(dataset.get("title", "")).lower()
    source_class = str(dataset.get("source_class", ""))

    if "hidroweb" in url or "hidroweb" in title:
        return _build_hidroweb_guide(dataset)
    if "mapbiomas" in url or "mapbiomas" in title:
        return _build_mapbiomas_guide(dataset)
    if "sidra" in url or "sidra" in title:
        return _build_sidra_guide(dataset)
    if "/snis" in url or title == "snis":
        return _build_snis_guide(dataset)
    if "terrabrasilis" in url or "queimadas" in title or "inpe" in title:
        return _build_inpe_guide(dataset)
    if "scielo" in url or source_class == "scientific_knowledge_source":
        return _build_scielo_guide(dataset)
    return _build_generic_guide(dataset)


def _common_study_filters() -> list[str]:
    return [
        "Priorizar recortes do corredor Sao Paulo -> Tres Lagoas.",
        "Quando o portal exigir territorio administrativo, priorizar SP, MS e municipios associados ao Tiete/Jupia.",
        "Favorecer series historicas, indicadores anuais ou mensais e tabelas exportaveis.",
    ]


def _base_guide(
    *,
    guide_key: str,
    dataset: dict[str, Any],
    title: str,
    category: str,
    entrypoint_url: str,
    direct_access_url: str,
    navigation_steps: list[str],
    portal_filters: list[str],
    study_filters: list[str],
    search_terms: list[str],
    expected_outputs: list[str],
    official_reference_urls: list[str],
    notes: list[str],
) -> dict[str, Any]:
    return {
        "guide_key": guide_key,
        "title": dataset.get("title", title),
        "category": category,
        "entrypoint_url": entrypoint_url,
        "direct_access_url": direct_access_url,
        "access_mode": dataset.get("access_level", "portal"),
        "navigation_steps": navigation_steps,
        "portal_filters": portal_filters,
        "study_filters": study_filters,
        "search_terms": search_terms,
        "expected_outputs": expected_outputs,
        "official_reference_urls": official_reference_urls,
        "notes": notes,
    }


def _with_validation(
    guide: dict[str, Any],
    *,
    validated_via_browser: bool,
    exact_navigation_steps: list[str],
    visible_ui_labels: list[str],
    recommended_filter_values_for_100k: dict[str, list[str]],
    download_or_export_path: dict[str, Any],
    available_formats: list[str],
    requires_auth: bool,
    blockers: list[str] | None = None,
    validated_via_mcp: bool = False,
    validation_method: str = "playwright_cli_skill",
) -> dict[str, Any]:
    enriched = dict(guide)
    enriched["validated_via_mcp"] = validated_via_mcp
    enriched["validated_via_browser"] = validated_via_browser
    enriched["validation_method"] = validation_method if validated_via_browser or validated_via_mcp else "manual_curation"
    enriched["exact_navigation_steps"] = exact_navigation_steps
    enriched["visible_ui_labels"] = visible_ui_labels
    enriched["recommended_filter_values_for_100k"] = recommended_filter_values_for_100k
    enriched["download_or_export_path"] = download_or_export_path
    enriched["available_formats"] = available_formats
    enriched["requires_auth"] = requires_auth
    enriched["blockers"] = blockers or []
    return enriched


def _build_hidroweb_guide(dataset: dict[str, Any]) -> dict[str, Any]:
    guide = _base_guide(
        guide_key="hidroweb",
        dataset=dataset,
        title="Hidroweb",
        category="dados_analiticos",
        entrypoint_url="https://www.snirh.gov.br/hidroweb",
        direct_access_url=dataset.get("canonical_url", "https://www.snirh.gov.br/hidroweb"),
        navigation_steps=[
            "Abrir o Hidroweb.",
            "Entrar em Series Historicas.",
            "Filtrar por estacao, rio, estado ou municipio.",
            "Executar a consulta e baixar os arquivos da estacao ou do lote selecionado.",
        ],
        portal_filters=[
            "Tipo Estacao.",
            "Codigo da Estacao.",
            "Nome Estacao.",
            "Bacia.",
            "SubBacia.",
            "Rio.",
            "Estado.",
            "Municipio.",
            "Operando.",
            "Responsavel (Sigla).",
            "Operadora (Sigla).",
        ],
        study_filters=_common_study_filters() + [
            "Para hidrologia do corredor, priorizar vazao, nivel e chuva.",
            "Para Jupia, incluir Castilho, Tiete, Parana e estacoes proximas ao reservatorio.",
        ],
        search_terms=["rio tiete", "reservatorio de jupia", "castilho", "tres lagoas", "vazao", "nivel", "chuva"],
        expected_outputs=["Series historicas por estacao.", "Metadados da estacao.", "Arquivos TXT, CSV e MDB."],
        official_reference_urls=["https://www.snirh.gov.br/hidroweb"],
        notes=[
            "A navegacao real confirmou o menu Series Historicas e os botoes de download por linha e por lote.",
            "A API aparece como fluxo separado em Solicite Acesso API e nao foi seguida nesta rodada.",
        ],
    )
    return _with_validation(
        guide,
        validated_via_browser=True,
        exact_navigation_steps=[
            "Abrir `https://www.snirh.gov.br/hidroweb`.",
            "Clicar em `Series Historicas`.",
            "Preencher `Estado`, `Municipio`, `Rio`, `Bacia` ou `Tipo Estacao`.",
            "Clicar em `Consultar`.",
            "No grid, usar `baixar txt`, `baixar csv` ou `baixar mdb` por estacao.",
            "Para lote, marcar estacoes, escolher `Texto (.txt)` ou `Excel (.csv)` e clicar em `Baixar Arquivo`.",
        ],
        visible_ui_labels=[
            "Series Historicas", "Tipo Estacao", "Bacia", "SubBacia", "Rio (Selecione Bacia)", "Estado",
            "Municipio", "Consultar", "baixar txt", "baixar csv", "baixar mdb",
            "Download para as estacoes selecionadas", "Texto (.txt)", "Excel (.csv)", "Baixar Arquivo",
            "Solicite Acesso API", "Acesso Restrito",
        ],
        recommended_filter_values_for_100k={
            "estado": ["Sao Paulo", "Mato Grosso do Sul"],
            "municipio": ["Castilho", "Tres Lagoas"],
            "rio": ["Rio Tiete", "Rio Parana"],
            "tipo_estacao": ["Fluviometrica", "Pluviometrica"],
            "variavel_operacional": ["Vazao", "Nivel", "Chuva"],
        },
        download_or_export_path={
            "summary": "O download publico aparece diretamente na grade de Series Historicas, por estacao ou em lote.",
            "steps": ["Abrir a consulta em `Series Historicas`.", "Filtrar o recorte desejado.", "Clicar em `Consultar`.", "Baixar por linha ou em lote no rodape do grid."],
            "observed_controls": ["baixar txt", "baixar csv", "baixar mdb", "Texto (.txt)", "Excel (.csv)", "Baixar Arquivo"],
            "observed_urls": ["https://www.snirh.gov.br/hidroweb", "https://www.snirh.gov.br/hidroweb/serieshistoricas"],
        },
        available_formats=["TXT", "CSV", "MDB"],
        requires_auth=False,
    )


def _build_mapbiomas_guide(dataset: dict[str, Any]) -> dict[str, Any]:
    guide = _base_guide(
        guide_key="mapbiomas",
        dataset=dataset,
        title="MapBiomas",
        category="dados_analiticos",
        entrypoint_url="https://plataforma.brasil.mapbiomas.org/",
        direct_access_url="https://plataforma.brasil.mapbiomas.org/",
        navigation_steps=["Abrir a plataforma.", "Selecionar tema, territorio e periodo.", "Entrar em Downloads.", "Baixar o GeoTIFF rapido por territorio ou gerar um mapa personalizado."],
        portal_filters=["Tema.", "Colecao.", "Territorio.", "Minha geometria.", "Ano."],
        study_filters=_common_study_filters() + [
            "Para o projeto 100K, priorizar uso e cobertura da terra, transicoes, agua e fogo.",
            "Para recorte fino, preferir geometria propria cobrindo Tiete e Jupia.",
        ],
        search_terms=["rio tiete", "uso da terra", "cobertura do solo", "transicoes", "fogo", "tres lagoas"],
        expected_outputs=["Mapas GeoTIFF.", "Estatisticas por territorio.", "Recorte personalizado por geometria."],
        official_reference_urls=["https://plataforma.brasil.mapbiomas.org/"],
        notes=[
            "A navegacao real confirmou o painel `Downloads` e o card `Gerar mapa personalizado (GeoTiff)`.",
            "A plataforma exibiu modais informativos antes de liberar o painel de download.",
        ],
    )
    return _with_validation(
        guide,
        validated_via_browser=True,
        exact_navigation_steps=[
            "Abrir `https://plataforma.brasil.mapbiomas.org/`.",
            "Fechar os modais informativos com `Continuar`.",
            "Clicar em `Downloads`.",
            "Escolher `Territorio` para o download rapido ou usar `Gerar mapa personalizado (GeoTiff)`.",
            "Acionar `Download (.TIFF)` quando o territorio estiver definido.",
        ],
        visible_ui_labels=["Temas", "Cobertura", "Transicoes", "Agua", "Fogo", "Downloads", "Pesquise um ou mais territorios", "Minha geometria", "Download de Mapas (GeoTiffs)", "Territorio", "Download (.TIFF)", "Gerar mapa personalizado (GeoTiff)"],
        recommended_filter_values_for_100k={
            "tema": ["Cobertura", "Transicoes", "Agua", "Fogo"],
            "territorio": ["Municipios do corredor Sao Paulo -> Tres Lagoas"],
            "geometria": ["Bacia/trecho cobrindo Rio Tiete e Reservatorio de Jupia"],
            "ano": ["2019", "2020", "2021", "2022", "2023", "2024"],
        },
        download_or_export_path={
            "summary": "O download publico fica no painel `Downloads`, com GeoTIFF rapido por territorio ou geracao personalizada.",
            "steps": ["Abrir a plataforma.", "Entrar em `Downloads`.", "Selecionar um `Territorio` ou optar por `Gerar mapa personalizado (GeoTiff)`.", "Clicar em `Download (.TIFF)`."],
            "observed_controls": ["Downloads", "Territorio", "Download (.TIFF)", "Gerar mapa personalizado (GeoTiff)"],
            "observed_urls": ["https://plataforma.brasil.mapbiomas.org/"],
        },
        available_formats=["GeoTIFF"],
        requires_auth=False,
    )


def _build_sidra_guide(dataset: dict[str, Any]) -> dict[str, Any]:
    guide = _base_guide(
        guide_key="sidra",
        dataset=dataset,
        title="SIDRA - IBGE",
        category="dados_analiticos",
        entrypoint_url="https://sidra.ibge.gov.br/",
        direct_access_url=dataset.get("canonical_url", "https://sidra.ibge.gov.br/"),
        navigation_steps=["Abrir o SIDRA.", "Entrar em Acervo.", "Filtrar pesquisa, assunto e tabela.", "Abrir a tabela, ajustar os editores e usar Download."],
        portal_filters=["Pesquisa.", "Assunto.", "Tabela de dados agregados.", "Variavel.", "Atividades economicas e familias.", "Ano.", "Unidade Territorial."],
        study_filters=_common_study_filters() + [
            "Priorizar recortes de meio ambiente, agua e indicadores territoriais.",
            "Cruzar o corredor via municipio, UF ou agregados nacionais quando a tabela nao descer ao nivel local.",
        ],
        search_terms=["contas economicas ambientais da agua", "meio ambiente", "indicadores de desenvolvimento sustentavel", "sao paulo", "tres lagoas"],
        expected_outputs=["Tabelas agregadas com URL persistida.", "Download tabular em formatos multiplos.", "Quadro salvo para reproducao da consulta."],
        official_reference_urls=["https://sidra.ibge.gov.br/", "https://sidra.ibge.gov.br/acervo", "https://sidra.ibge.gov.br/Tabela/9688"],
        notes=[
            "A navegacao real confirmou o fluxo `Acervo -> Assunto -> Tabela de dados agregados -> Tabela -> Download`.",
            "Na validacao real, a tabela 9688 exibiu apenas `Brasil` em Unidade Territorial no recorte testado.",
        ],
    )
    return _with_validation(
        guide,
        validated_via_browser=True,
        exact_navigation_steps=[
            "Abrir `https://sidra.ibge.gov.br/`.",
            "Clicar em `Acervo`.",
            "Selecionar a pesquisa `C4 - Contas Economicas Ambientais da Agua`.",
            "Selecionar o assunto `274 - Meio ambiente`.",
            "Abrir a tabela `9688` pelo icone de tabela.",
            "Ajustar os editores `Variavel`, `Atividades economicas e familias`, `Ano` e `Unidade Territorial`.",
            "Clicar em `Download` e escolher o formato.",
        ],
        visible_ui_labels=["Acervo", "Filtros ativos", "Pesquisa", "Assunto", "Tabela de dados agregados", "Contas Economicas Ambientais da Agua", "Variavel", "Atividades economicas e familias", "Ano", "Unidade Territorial", "Visualizar", "Download", "Salvar Quadro"],
        recommended_filter_values_for_100k={
            "pesquisa": ["C4 - Contas Economicas Ambientais da Agua", "IU - Indicadores de Desenvolvimento Sustentavel", "DU - uso da terra nos biomas brasileiros"],
            "assunto": ["274 - Meio ambiente"],
            "tabelas_uteis": ["9688", "9687", "9692", "9693"],
            "unidade_territorial": ["Brasil", "Sao Paulo", "Mato Grosso do Sul", "Municipios do corredor quando a tabela permitir"],
            "ano": ["2018", "2019", "2020"],
        },
        download_or_export_path={
            "summary": "O download publico aparece diretamente dentro da pagina da tabela selecionada.",
            "steps": ["Abrir a tabela desejada.", "Configurar os editores da tabela.", "Clicar em `Download`.", "Definir nome do arquivo e formato.", "Usar o link final de download gerado pela propria tabela."],
            "observed_controls": ["Download", "Nome do arquivo", "Formato", "XLSX", "ODS", "HTML", "CSV (BR)", "CSV (US)", "TSV (BR)", "TSV (US)"],
            "observed_urls": ["https://sidra.ibge.gov.br/acervo#/S/C4/A/274/T/Q", "https://sidra.ibge.gov.br/Tabela/9688"],
        },
        available_formats=["XLSX", "ODS", "HTML", "CSV (BR)", "CSV (US)", "TSV (BR)", "TSV (US)"],
        requires_auth=False,
    )


def _build_snis_guide(dataset: dict[str, Any]) -> dict[str, Any]:
    guide = _base_guide(
        guide_key="snis",
        dataset=dataset,
        title="SNIS",
        category="dados_analiticos",
        entrypoint_url="https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/snis",
        direct_access_url=dataset.get("canonical_url", "https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/snis"),
        navigation_steps=["Abrir a pagina principal do SNIS.", "Escolher entre Painel ou Serie Historica.", "Para consulta reproduzivel, entrar em Serie Historica > Municipios.", "Preencher filtros territoriais e de ano e seguir para o relatorio."],
        portal_filters=["Componente.", "Tipo Informacao.", "Ano de Referencia.", "Regiao.", "Estado.", "Municipios.", "Prestador de servico.", "Familia de informacoes e indicadores.", "Informacoes e Indicadores."],
        study_filters=_common_study_filters() + [
            "Priorizar Agua e Esgotos e, quando fizer sentido, Aguas Pluviais.",
            "Usar Castilho, Panorama, Tres Lagoas e outros municipios do eixo Tiete/Jupia como primeiro recorte.",
        ],
        search_terms=["agua e esgotos", "serie historica", "castilho", "panorama", "tres lagoas", "prestador"],
        expected_outputs=["Indicadores consolidados em painel.", "Series historicas por municipio ou prestador.", "Planilhas exportaveis e glossarios de apoio."],
        official_reference_urls=["https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/snis", "https://app4.cidades.gov.br/serieHistorica/", "https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/snis/painel/ab"],
        notes=[
            "A navegacao real confirmou a pagina principal, o `Painel` com Power BI e a tela de filtros da `Serie Historica`.",
            "O aplicativo da Serie Historica declara no proprio texto que permite exportacao para Excel e planilhas eletronicas.",
        ],
    )
    return _with_validation(
        guide,
        validated_via_browser=True,
        exact_navigation_steps=[
            "Abrir a pagina principal do SNIS.",
            "Entrar em `Serie Historica` pelo card `bt_serie_historica.png`.",
            "Na aplicacao `SNIS - Serie Historica`, abrir `Municipios`.",
            "Entrar em `Informacoes e indicadores municipais consolidados`.",
            "Preencher `Ano de Referencia`, `Estado` e `Municipios (*)` e clicar em `Continuar`.",
            "Se precisar de leitura agregada rapida, usar o `Painel` e filtrar o `Ano` no Power BI.",
        ],
        visible_ui_labels=["Painel", "Serie Historica", "Diagnosticos", "Abastecimento de Agua", "Esgotamento Sanitario", "Manejo dos Residuos Solidos Urbanos", "Drenagem e Manejo das Aguas Pluviais Urbanas", "Filtros", "Tipo Informacao", "Ano de Referencia", "Regiao", "Estado", "Municipios (*)", "Continuar", "Relatorio do Power BI", "Ano"],
        recommended_filter_values_for_100k={
            "componente": ["Agua e Esgotos", "Aguas Pluviais"],
            "estado": ["Sao Paulo", "Mato Grosso do Sul"],
            "municipios": ["Castilho/SP", "Panorama/SP", "Tres Lagoas/MS"],
            "ano": ["2022"],
            "familias": ["Operacionais - agua", "Operacionais - esgotos", "Qualidade", "Informacoes sobre PMSB"],
        },
        download_or_export_path={
            "summary": "O melhor caminho operacional e `Serie Historica`; a tela de filtros foi validada, mas o passo final da exportacao nao foi concluido na automacao desta rodada.",
            "steps": ["Abrir `Serie Historica`.", "Entrar em `Municipios`.", "Abrir `Informacoes e indicadores municipais consolidados`.", "Selecionar `Ano de Referencia`, `Estado` e `Municipios (*)`.", "Clicar em `Continuar` para gerar o relatorio e a exportacao."],
            "observed_controls": ["Filtros", "Tipo Informacao", "Ano de Referencia", "Estado", "Municipios (*)", "Continuar", "Relatorio do Power BI", "Ano"],
            "observed_urls": ["https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/snis", "https://app4.cidades.gov.br/serieHistorica/", "https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/snis/painel/ab"],
        },
        available_formats=["Excel (declarado pela aplicacao)", "Planilhas eletronicas (declarado pela aplicacao)"],
        requires_auth=False,
        blockers=[
            "Na automacao Playwright da Serie Historica, o app exibiu o alerta `E necessario selecionar ao menos um(a) Municipio.` mesmo com municipio marcado na interface.",
            "O caminho ate a tela final de exportacao ficou parcialmente validado, mas o clique final no relatorio nao foi concluido de ponta a ponta nesta rodada.",
        ],
    )


def _build_inpe_guide(dataset: dict[str, Any]) -> dict[str, Any]:
    guide = _base_guide(
        guide_key="inpe_queimadas",
        dataset=dataset,
        title="Programa Queimadas - INPE",
        category="dados_analiticos",
        entrypoint_url="https://terrabrasilis.dpi.inpe.br/queimadas/portal/",
        direct_access_url=dataset.get("canonical_url", "https://terrabrasilis.dpi.inpe.br/queimadas/portal/"),
        navigation_steps=["Abrir o portal do Programa Queimadas.", "Entrar em Download > Dados Abertos para acesso direto aos arquivos.", "Usar Estatisticas quando precisar de recorte por estado, regiao ou bioma.", "Baixar os arquivos do dataserver ou usar Geoservicos OGC."],
        portal_filters=["Estado.", "Regiao.", "Bioma.", "Periodicidade do arquivo.", "Tipo de dado."],
        study_filters=_common_study_filters() + [
            "Priorizar Sao Paulo e Mato Grosso do Sul.",
            "Cruzar foco de calor com recorte mensal, diario ou anual conforme a analise.",
        ],
        search_terms=["sao paulo", "mato grosso do sul", "focos ativos", "csv", "risco de fogo", "precipitacao"],
        expected_outputs=["Arquivos CSV e KML de focos.", "TIFF e Shapefile de area queimada.", "Arquivos diarios observados e previstos de risco de fogo e meteorologia.", "Servicos WMS/WFS."],
        official_reference_urls=["https://terrabrasilis.dpi.inpe.br/queimadas/portal/", "https://terrabrasilis.dpi.inpe.br/queimadas/portal/pages/secao_downloads/dados-abertos/#da-focos"],
        notes=[
            "A navegacao real confirmou a pagina `Dados Abertos` com links publicos diretos do dataserver do INPE.",
            "Para comparativos territoriais, o portal principal tambem exibe `Estatisticas: Estados, Regioes e Biomas`.",
        ],
    )
    return _with_validation(
        guide,
        validated_via_browser=True,
        exact_navigation_steps=[
            "Abrir `https://terrabrasilis.dpi.inpe.br/queimadas/portal/`.",
            "Entrar em `Download` > `Dados Abertos`.",
            "Na secao `Focos de Queimadas e Incendios`, escolher CSV (`10 min`, `Diarios`, `Mensais`, `Anuais`) ou KML.",
            "Na secao `Area Queimada`, escolher `Mensais` em `Tiff` ou `Shapefile`.",
            "Na secao `Risco de Fogo e Meteorologia`, escolher observado diario ou previsto para os proximos 3 dias.",
        ],
        visible_ui_labels=["Download", "Dados Abertos", "Focos de Queimadas e Incendios", "Arquivos CSV", "10 min", "Diarios", "Mensais", "Anuais", "Arquivos KML", "Area Queimada", "AQ 1km", "Tiff", "Shapefile", "Risco de Fogo e Meteorologia", "Risco de Fogo Observado", "Risco de Fogo Previsto", "Geoservicos OGC"],
        recommended_filter_values_for_100k={
            "estado": ["Sao Paulo", "Mato Grosso do Sul"],
            "regiao": ["Sudeste", "Centro-Oeste"],
            "bioma": ["Mata Atlantica", "Cerrado"],
            "periodicidade": ["Diario", "Mensal", "Anual"],
            "tipo_dado": ["Focos", "Area Queimada", "Risco de Fogo", "Precipitacao", "Temperatura", "Umidade relativa"],
        },
        download_or_export_path={
            "summary": "O portal expoe links publicos diretos para o dataserver do INPE por tipo de dado e periodicidade.",
            "steps": ["Abrir a pagina `Dados Abertos`.", "Escolher a secao do dado.", "Clicar no card de periodicidade ou formato desejado.", "Baixar diretamente do dataserver do INPE."],
            "observed_controls": ["10 min", "Diarios", "Mensais", "Anuais", "Focos diarios web", "Mensais Tiff", "Mensais Shapefile", "Risco de Fogo Observado", "Risco de Fogo Previsto"],
            "observed_urls": [
                "https://terrabrasilis.dpi.inpe.br/queimadas/portal/pages/secao_downloads/dados-abertos/#da-focos",
                "https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/diario/",
                "https://dataserver-coids.inpe.br/queimadas/queimadas/area_queimada/colecao2/tif/",
                "https://dataserver-coids.inpe.br/queimadas/queimadas/area_queimada/colecao2/shp/",
                "https://terrabrasilis.dpi.inpe.br/queimadas/geoserver/ows?SERVICE=WMS&VERSION=1.3.0&REQUEST=Getcapabilities",
            ],
        },
        available_formats=["CSV", "KML", "TIFF", "Shapefile", "WMS", "WFS"],
        requires_auth=False,
    )


def _build_scielo_guide(dataset: dict[str, Any]) -> dict[str, Any]:
    guide = _base_guide(
        guide_key="scielo",
        dataset=dataset,
        title="SciELO",
        category="literatura_documentacao",
        entrypoint_url="https://search.scielo.org/?lang=pt",
        direct_access_url=dataset.get("canonical_url", "https://www.scielo.br/"),
        navigation_steps=["Abrir a busca da SciELO.", "Executar a consulta por rio, reservatorio ou variavel.", "Usar filtros de colecao, periodico, idioma e ano.", "Abrir texto e PDF para rastrear fontes citadas."],
        portal_filters=["Colecoes.", "Periodico.", "Idioma.", "Ano.", "Area tematica.", "Tipo de literatura."],
        study_filters=_common_study_filters() + [
            "Priorizar ciencias ambientais, recursos hidricos, saneamento e geografia.",
            "Fechar por anos recentes para rastrear bases ainda ativas.",
        ],
        search_terms=["\"rio tiete\"", "\"reservatorio de jupia\"", "\"qualidade da agua\"", "sedimentos", "uso da terra", "saneamento"],
        expected_outputs=["Artigos e revisoes.", "PDFs e textos completos.", "Referencias de datasets e metodos."],
        official_reference_urls=["https://search.scielo.org/?lang=pt", "https://www.scielo.br/"],
        notes=[
            "SciELO segue sendo uma trilha de descoberta metodologica e bibliografica, nao um dataset operacional direto.",
            "Nesta rodada, a validacao real detectou bloqueio HTTP na busca publica automatizada.",
        ],
    )
    return _with_validation(
        guide,
        validated_via_browser=True,
        exact_navigation_steps=[
            "Abrir `https://search.scielo.org/?lang=pt`.",
            "A navegacao automatizada encontrou `403 Forbidden` antes de expor os filtros da busca.",
            "Usar `https://www.scielo.br/` manualmente se precisar continuar a pesquisa bibliografica fora da automacao.",
        ],
        visible_ui_labels=["403 Forbidden"],
        recommended_filter_values_for_100k={
            "consulta": ["\"rio tiete\"", "\"reservatorio de jupia\"", "\"qualidade da agua\""],
            "uso": ["Literatura", "Metodologia", "Referencias de datasets"],
        },
        download_or_export_path={
            "summary": "Nao houve caminho de download validado nesta rodada porque a busca automatizada retornou `403 Forbidden`.",
            "steps": ["Abrir a busca publica.", "Registrar o bloqueio HTTP.", "Tratar a fonte como apoio bibliografico, nao como fonte operacional nesta rodada."],
            "observed_controls": ["403 Forbidden"],
            "observed_urls": ["https://search.scielo.org/?lang=pt"],
        },
        available_formats=[],
        requires_auth=False,
        blockers=["A busca automatizada em `https://search.scielo.org/?lang=pt` retornou `403 Forbidden` no navegador real."],
    )


def _build_generic_guide(dataset: dict[str, Any]) -> dict[str, Any]:
    url = str(dataset.get("canonical_url", "") or dataset.get("source_url", ""))
    host = urlparse(url).netloc or "fonte"
    guide = _base_guide(
        guide_key=host.replace(".", "_"),
        dataset=dataset,
        title=str(dataset.get("title", "Fonte descoberta")),
        category="dados_analiticos" if dataset.get("source_class") == "analytical_data_source" else "literatura_documentacao",
        entrypoint_url=url,
        direct_access_url=url,
        navigation_steps=["Abrir o link canonico.", "Identificar menu de dados, downloads, pesquisa ou documentacao.", "Validar se o portal possui filtros territoriais, temporais ou tematicos antes de exportar."],
        portal_filters=["Territorio.", "Periodo.", "Tema ou modulo."],
        study_filters=_common_study_filters(),
        search_terms=list(dataset.get("variables_normalized", [])[:5]) or [str(dataset.get("title", ""))],
        expected_outputs=["Link de consulta principal.", "Indicacoes de filtro manual para reproduzir a busca."],
        official_reference_urls=[url] if url else [],
        notes=["Guia generico criado quando nao ha playbook especifico para a fonte."],
    )
    return _with_validation(
        guide,
        validated_via_browser=False,
        exact_navigation_steps=guide["navigation_steps"],
        visible_ui_labels=[],
        recommended_filter_values_for_100k={"territorio": ["Sao Paulo", "Mato Grosso do Sul", "Municipios do corredor"]},
        download_or_export_path={
            "summary": "Caminho generico; nao houve validacao em browser real para esta fonte.",
            "steps": guide["navigation_steps"],
            "observed_controls": [],
            "observed_urls": [url] if url else [],
        },
        available_formats=[],
        requires_auth=False,
        blockers=["Nao houve validacao em browser real para esta fonte nesta rodada."],
        validation_method="manual_curation",
    )
