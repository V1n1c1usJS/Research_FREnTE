"""CLI entrypoint for the multi-agent environmental discovery pipeline."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from src.pipelines.multi_agent_pipeline import MultiAgentPipeline
from src.pipelines.real_initialization_pipeline import RealInitializationPipeline
from src.schemas.settings import PipelineSettings
from src.utils.io import write_catalog_csv
from src.utils.logging import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="research-frente")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Executa pipeline em modo padrao")
    _add_common_run_args(run_parser)
    _add_llm_args(run_parser)

    dry_run_parser = subparsers.add_parser("dry-run", help="Executa pipeline em modo dry-run")
    _add_common_run_args(dry_run_parser)
    _add_llm_args(dry_run_parser)

    real_init_parser = subparsers.add_parser("real-init", help="Executa uma inicializacao real em larga escala")
    real_init_parser.add_argument("--limit-per-run", type=int, default=10, help="Limite por run individual")
    real_init_parser.add_argument("--web-timeout", type=float, default=5.0, help="Timeout do conector real em segundos")
    real_init_parser.add_argument("--max-queries", type=int, default=8, help="Quantidade maxima de queries seed")
    real_init_parser.add_argument("--query", action="append", dest="queries", help="Query seed adicional ou substituta")
    _add_llm_args(real_init_parser)

    export_parser = subparsers.add_parser("export", help="Exporta catalogo JSON para CSV")
    export_parser.add_argument("--catalog", required=True, help="Caminho para o catalog.json")
    export_parser.add_argument("--output", required=True, help="Caminho de saida CSV")

    return parser


def _add_common_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--query", default="impactos humanos no Rio Tiete", help="Tema de pesquisa")
    parser.add_argument("--limit", type=int, default=10, help="Limite de datasets")
    parser.add_argument(
        "--web-mode",
        choices=["mock", "real"],
        default="mock",
        help="Seleciona o conector de pesquisa web (dry-run sempre usa mock)",
    )
    parser.add_argument(
        "--web-timeout",
        type=float,
        default=8.0,
        help="Timeout em segundos para o conector real de pesquisa web",
    )


def _add_llm_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--llm-mode",
        choices=["off", "auto", "openai", "groq"],
        default=_env_value("RESEARCH_FRENTE_LLM_MODE", "auto"),
        help="Seleciona o uso de LLM. 'auto' usa OpenAI e depois Groq se houver chaves configuradas.",
    )
    parser.add_argument(
        "--llm-model",
        default=None,
        help="Modelo do provedor LLM. Se omitido, usa o default do modo escolhido.",
    )
    parser.add_argument(
        "--llm-timeout",
        type=float,
        default=_env_float("RESEARCH_FRENTE_LLM_TIMEOUT_SECONDS", 60.0),
        help="Timeout das chamadas ao provedor LLM em segundos.",
    )
    parser.add_argument(
        "--llm-temperature",
        type=float,
        default=_env_float("RESEARCH_FRENTE_LLM_TEMPERATURE", 0.2),
        help="Temperatura das chamadas ao LLM.",
    )
    parser.add_argument(
        "--llm-max-output-tokens",
        type=int,
        default=_env_int("RESEARCH_FRENTE_LLM_MAX_OUTPUT_TOKENS", 1800),
        help="Limite de tokens de saida para o LLM.",
    )
    parser.add_argument(
        "--llm-fail-on-error",
        action="store_true",
        default=_env_bool("RESEARCH_FRENTE_LLM_FAIL_ON_ERROR", False),
        help="Falha a execucao quando houver erro de LLM em vez de cair em fallback heuristico.",
    )


def run(argv: list[str] | None = None) -> int:
    configure_logging()
    _load_dotenv_if_available()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "export":
        return _run_export(catalog_path=Path(args.catalog), output_path=Path(args.output))
    if args.command == "real-init":
        return _run_real_init(args)

    dry_run = args.command == "dry-run"
    web_mode = "mock" if dry_run else args.web_mode

    settings = PipelineSettings(
        query=args.query,
        limit=args.limit,
        dry_run=dry_run,
        web_research_mode=web_mode,
        web_timeout_seconds=args.web_timeout,
        llm_mode=args.llm_mode,
        llm_model=_resolve_llm_model(args.llm_mode, args.llm_model),
        llm_timeout_seconds=args.llm_timeout,
        llm_temperature=args.llm_temperature,
        llm_max_output_tokens=args.llm_max_output_tokens,
        llm_fail_on_error=args.llm_fail_on_error,
    )
    result = MultiAgentPipeline(settings=settings).execute()

    print(f"Run ID: {result['run_id']}")
    print(f"Datasets: {result['dataset_count']}")
    print(f"Report: {result['report_path']}")
    print(f"Catalog: {result['catalog_path']}")
    return 0


def _run_real_init(args: argparse.Namespace) -> int:
    result = RealInitializationPipeline(
        limit_per_run=args.limit_per_run,
        web_timeout_seconds=args.web_timeout,
        max_queries=args.max_queries,
        queries=args.queries,
        llm_mode=args.llm_mode,
        llm_model=_resolve_llm_model(args.llm_mode, args.llm_model),
        llm_timeout_seconds=args.llm_timeout,
        llm_temperature=args.llm_temperature,
        llm_max_output_tokens=args.llm_max_output_tokens,
        llm_fail_on_error=args.llm_fail_on_error,
    ).execute()

    print(f"Bootstrap ID: {result['bootstrap_id']}")
    print(f"Runs: {result['run_count']}")
    print(f"Datasets: {result['dataset_count']}")
    print(f"Failed queries: {result['failed_query_count']}")
    print(f"Bootstrap: {result['bootstrap_path']}")
    print(f"Report: {result['report_path']}")
    print(f"CSV: {result['export_path']}")
    print(f"Manual guides JSON: {result['manual_guides_path']}")
    print(f"Manual guides Markdown: {result['manual_guides_report_path']}")
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


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover - depende do ambiente local
        return
    load_dotenv()


def _env_value(name: str, default: str) -> str:
    return os.getenv(name, default)


def _env_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_llm_model(llm_mode: str, requested_model: str | None) -> str:
    if requested_model:
        return requested_model

    configured_model = os.getenv("RESEARCH_FRENTE_LLM_MODEL")
    if configured_model:
        return configured_model

    if llm_mode == "groq":
        return os.getenv("RESEARCH_FRENTE_GROQ_TEST_MODEL", "groq/compound-mini")

    if llm_mode == "auto":
        if os.getenv("OPENAI_API_KEY"):
            return "gpt-4.1-nano"
        if os.getenv("GROQ_API_KEY"):
            return os.getenv("RESEARCH_FRENTE_GROQ_TEST_MODEL", "groq/compound-mini")

    return "gpt-4.1-nano"


if __name__ == "__main__":
    raise SystemExit(run())
