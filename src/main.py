"""Ponto de entrada CLI do pipeline multiagente."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.pipelines.multi_agent_pipeline import MultiAgentPipeline
from src.schemas.settings import PipelineSettings
from src.utils.io import write_catalog_csv
from src.utils.logging import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="research-frente")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Executa pipeline em modo padrão (mock)")
    _add_common_run_args(run_parser)

    dry_run_parser = subparsers.add_parser("dry-run", help="Executa pipeline em modo dry-run")
    _add_common_run_args(dry_run_parser)

    export_parser = subparsers.add_parser("export", help="Exporta catálogo JSON para CSV")
    export_parser.add_argument("--catalog", required=True, help="Caminho para o catalog.json")
    export_parser.add_argument("--output", required=True, help="Caminho de saída CSV")

    return parser


def _add_common_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--query", default="impactos humanos no Rio Tietê", help="Tema de pesquisa")
    parser.add_argument("--limit", type=int, default=10, help="Limite de datasets simulados")
    parser.add_argument(
        "--web-mode",
        choices=["mock", "real"],
        default="mock",
        help="Seleciona conector de pesquisa web (run permite real; dry-run força mock)",
    )
    parser.add_argument(
        "--web-timeout",
        type=float,
        default=8.0,
        help="Timeout em segundos para o conector real de pesquisa web",
    )


def run(argv: list[str] | None = None) -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "export":
        return _run_export(catalog_path=Path(args.catalog), output_path=Path(args.output))

    dry_run = args.command == "dry-run"
    web_mode = "mock" if dry_run else args.web_mode

    settings = PipelineSettings(
        query=args.query,
        limit=args.limit,
        dry_run=dry_run,
        web_research_mode=web_mode,
        web_timeout_seconds=args.web_timeout,
    )
    pipeline = MultiAgentPipeline(settings=settings)
    result = pipeline.execute()

    print(f"Run ID: {result['run_id']}")
    print(f"Datasets: {result['dataset_count']}")
    print(f"Report: {result['report_path']}")
    print(f"Catalog: {result['catalog_path']}")
    return 0


def _run_export(catalog_path: Path, output_path: Path) -> int:
    import json

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


if __name__ == "__main__":
    raise SystemExit(run())
