"""CLI entrypoint para o fluxo principal de pesquisa via Perplexity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from src.pipelines.perplexity_intelligence_pipeline import PerplexityIntelligencePipeline
from src.utils.io import write_catalog_csv
from src.utils.logging import configure_logging

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTEXT_FILE = REPO_ROOT / "config" / "context_100k.yaml"
DEFAULT_TRACKS_FILE = REPO_ROOT / "config" / "tracks_100k.yaml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="research-frente")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="Executa o fluxo principal: contexto mestre + chats tematicos no Perplexity",
    )
    _add_perplexity_args(run_parser)

    perplexity_parser = subparsers.add_parser(
        "perplexity-intel",
        help="Alias explicito para o fluxo principal via Perplexity",
    )
    _add_perplexity_args(perplexity_parser)

    export_parser = subparsers.add_parser("export", help="Exporta catalogo JSON para CSV")
    export_parser.add_argument("--catalog", required=True, help="Caminho para o catalog.json")
    export_parser.add_argument("--output", required=True, help="Caminho de saida CSV")

    return parser


def _add_perplexity_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--query", required=True, help="Tema base da pesquisa")
    parser.add_argument("--limit", type=int, default=20, help="Limite de datasets/fontes normalizadas")
    parser.add_argument("--max-searches", type=int, default=5, help="Quantidade maxima de chats tematicos")
    parser.add_argument(
        "--perplexity-max-results",
        type=int,
        default=20,
        help="Numero maximo de resultados por busca na Search API (1-20).",
    )
    parser.add_argument(
        "--perplexity-timeout",
        type=float,
        default=60.0,
        help="Timeout em segundos das chamadas a API do Perplexity.",
    )
    parser.add_argument(
        "--context-file",
        help="Arquivo JSON ou YAML com o contexto mestre da pesquisa.",
    )
    parser.add_argument(
        "--tracks-file",
        help="Arquivo JSON ou YAML com as trilhas/chats tematicos.",
    )
    parser.add_argument(
        "--track-limit",
        type=int,
        help="Limita quantas trilhas do arquivo de tracks serao executadas nesta rodada.",
    )
    parser.add_argument(
        "--llm-mode",
        choices=["auto", "off", "openai"],
        default="auto",
        help="Modo de inferencia para classificar fontes. 'auto' usa OpenAI se houver chave configurada.",
    )
    parser.add_argument(
        "--llm-model",
        default="gpt-4.1-nano",
        help="Modelo OpenAI usado na inferencia estrutural das fontes.",
    )
    parser.add_argument(
        "--llm-timeout",
        type=float,
        default=60.0,
        help="Timeout das chamadas de inferencia por LLM.",
    )
    parser.add_argument(
        "--llm-fail-on-error",
        action="store_true",
        help="Interrompe a execucao se a inferencia por LLM falhar.",
    )


def run(argv: list[str] | None = None) -> int:
    configure_logging()
    _load_dotenv_if_available()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "export":
        return _run_export(catalog_path=Path(args.catalog), output_path=Path(args.output))
    return _run_perplexity_intel(args)


def _run_perplexity_intel(args: argparse.Namespace) -> int:
    import os

    perplexity_api_key = os.getenv("PERPLEXITY_API_KEY", "").strip()
    if not perplexity_api_key:
        print("Erro: PERPLEXITY_API_KEY nao configurada no ambiente.")
        return 1

    master_context_payload = _resolve_structured_payload(args.context_file, DEFAULT_CONTEXT_FILE)
    research_tracks_payload = _resolve_structured_payload(args.tracks_file, DEFAULT_TRACKS_FILE)
    if isinstance(research_tracks_payload, list) and args.track_limit:
        research_tracks_payload = research_tracks_payload[: max(args.track_limit, 0)]

    result = PerplexityIntelligencePipeline(
        base_query=args.query,
        limit=args.limit,
        max_searches=args.max_searches,
        perplexity_api_key=perplexity_api_key,
        perplexity_max_results=args.perplexity_max_results,
        perplexity_timeout_seconds=args.perplexity_timeout,
        master_context_payload=master_context_payload,
        research_tracks_payload=research_tracks_payload,
        llm_mode=args.llm_mode,
        llm_model=args.llm_model,
        llm_timeout_seconds=args.llm_timeout,
        llm_fail_on_error=args.llm_fail_on_error,
    ).execute()

    print(f"Research ID: {result['research_id']}")
    print(f"Master context: {result['master_context_path']}")
    print(f"Categorized sources: {result['categorized_source_count']}")
    print(f"Dataset candidates: {result['dataset_candidate_count']}")
    print(f"Datasets: {result['dataset_count']}")
    print(f"Intelligence JSON: {result['intelligence_path']}")
    print(f"Report: {result['report_path']}")
    print(f"Sources CSV: {result['sources_csv_path']}")
    print(f"Datasets CSV: {result['datasets_csv_path']}")
    return 0


def _run_export(catalog_path: Path, output_path: Path) -> int:
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    rows = [
        {
            "dataset_id": item["dataset_id"],
            "title": item["title"],
            "source_name": item["source_name"],
            "source_url": item["source_url"],
            "relevance_score": item["relevance_score"],
            "access_level": item["access_level"],
            "priority": item.get("priority", "unknown"),
            "dataset_kind": item.get("dataset_kind", "unknown"),
            "methodological_note": " | ".join(item.get("methodological_notes", [])[:1]),
        }
        for item in payload.get("datasets", [])
    ]
    write_catalog_csv(output_path, rows)
    print(f"Exportado CSV em: {output_path}")
    return 0


def _load_structured_file(path_str: str) -> Any:
    path = Path(path_str)
    raw = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".json":
        return json.loads(raw)
    return yaml.safe_load(raw)


def _resolve_structured_payload(explicit_path: str | None, default_path: Path) -> Any:
    if explicit_path:
        return _load_structured_file(explicit_path)
    if default_path.exists():
        return _load_structured_file(str(default_path))
    return None


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover - depende do ambiente local
        return
    load_dotenv()


if __name__ == "__main__":
    raise SystemExit(run())
