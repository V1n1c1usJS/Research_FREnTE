from __future__ import annotations

import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

THEMES = [
    "hidrologia",
    "qualidade da água",
    "uso da terra",
    "desmatamento",
    "queimadas",
    "saneamento e esgoto",
    "resíduos e lixo",
    "relevo",
    "reservatórios",
    "limites hidrográficos",
    "sedimentos",
    "material orgânico",
    "meteorologia",
    "ocupação urbana",
]

BASE_QUERY = "São Paulo Três Lagoas Rio Tietê Reservatório de Jupiá dataset base de dados"


def run_batch(theme: str, limit: int = 30) -> dict[str, object]:
    query = f"{BASE_QUERY} {theme}"
    cmd = [
        "python",
        "-m",
        "src.main",
        "run",
        "--query",
        query,
        "--limit",
        str(limit),
        "--web-mode",
        "real",
        "--web-timeout",
        "12",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    run_id_match = re.search(r"Run ID: (run-[a-f0-9]+)", out)
    run_id = run_id_match.group(1) if run_id_match else None
    return {
        "theme": theme,
        "query": query,
        "returncode": proc.returncode,
        "run_id": run_id,
        "stdout_stderr": out,
    }


def host(url: str) -> str:
    cleaned = re.sub(r"^https?://", "", url).split("/")[0].lower()
    return re.sub(r"^www\.", "", cleaned)


def main() -> int:
    results = [run_batch(theme) for theme in THEMES]

    timestamp = datetime.now(timezone.utc).isoformat()
    run_stats: list[dict[str, object]] = []
    retrieval_counter = Counter()
    class_counter = Counter()
    domain_counter = Counter()

    by_url: dict[str, dict[str, object]] = {}
    evidence_by_url: Counter[str] = Counter()
    theme_coverage: defaultdict[str, int] = defaultdict(int)
    failed_quality_gates: list[str] = []

    for item in results:
        run_id = item["run_id"]
        if not run_id:
            run_stats.append({
                "theme": item["theme"],
                "query": item["query"],
                "run_id": None,
                "status": "run_error_no_id",
                "returncode": item["returncode"],
            })
            continue

        scout_path = Path("data") / "runs" / str(run_id) / "01_research-scout.json"
        scout = json.loads(scout_path.read_text(encoding="utf-8"))
        meta = scout.get("web_research_meta", {})
        kept = scout.get("web_research_results", [])
        raw = scout.get("web_research_results_raw", [])
        discarded = scout.get("web_research_results_discarded", [])

        retrieval_counter[meta.get("retrieval_status", "unknown")] += 1
        if meta.get("quality_gate_status") == "failed_quality_gate":
            failed_quality_gates.append(str(run_id))

        kept_classes = Counter(k.get("source_class", "unknown") for k in kept)
        class_counter.update(kept_classes)

        for k in kept:
            url = k.get("source_url", "")
            domain_counter[host(url)] += 1
            evidence_by_url[url] += 1
            theme_coverage[str(item["theme"])] += 1
            if url not in by_url:
                by_url[url] = {
                    "source_title": k.get("source_title"),
                    "source_url": url,
                    "source_type": k.get("source_type"),
                    "source_class": k.get("source_class"),
                    "publisher_or_org": k.get("publisher_or_org"),
                    "confidence": k.get("confidence"),
                    "relevance_hint": k.get("relevance_hint"),
                    "dataset_names_mentioned": k.get("dataset_names_mentioned", []),
                    "variables_mentioned": k.get("variables_mentioned", []),
                }

        run_stats.append(
            {
                "theme": item["theme"],
                "query": item["query"],
                "run_id": run_id,
                "returncode": item["returncode"],
                "connector_mode_used": meta.get("connector_mode_used"),
                "retrieval_status": meta.get("retrieval_status"),
                "quality_gate_status": meta.get("quality_gate_status"),
                "raw_result_count": len(raw),
                "discarded_result_count": len(discarded),
                "kept_result_count": len(kept),
                "kept_by_source_class": dict(kept_classes),
            }
        )

    consolidated = {
        "generated_at": timestamp,
        "batch_name": "scale_web_scan_real_mode_v2_quality_hardened",
        "total_batches": len(THEMES),
        "retrieval_status_counts": dict(retrieval_counter),
        "totals": {
            "total_raw": sum(int(r.get("raw_result_count", 0)) for r in run_stats),
            "total_discarded": sum(int(r.get("discarded_result_count", 0)) for r in run_stats),
            "total_kept": sum(int(r.get("kept_result_count", 0)) for r in run_stats),
            "unique_sources_after_dedup": len(by_url),
        },
        "source_class_totals": dict(class_counter),
        "top_domains": domain_counter.most_common(20),
        "top_sources_by_evidence": [
            {
                **by_url[url],
                "evidence_count": cnt,
            }
            for url, cnt in evidence_by_url.most_common(30)
        ],
        "coverage_by_theme": dict(theme_coverage),
        "failed_quality_gate_runs": failed_quality_gates,
        "run_stats": run_stats,
        "consolidated_catalog": [
            {
                **payload,
                "evidence_count": evidence_by_url[url],
            }
            for url, payload in sorted(by_url.items(), key=lambda x: evidence_by_url[x[0]], reverse=True)
        ],
    }

    out_json = Path("data") / "runs" / "scale_web_scan_real_mode_v2_quality_hardened.json"
    out_json.write_text(json.dumps(consolidated, ensure_ascii=False, indent=2), encoding="utf-8")

    report_lines = [
        "# Varredura web em escala (modo real) - Qualidade endurecida",
        "",
        f"- Arquivo consolidado JSON: `{out_json}`",
        f"- Total de lotes: `{consolidated['total_batches']}`",
        f"- Status de recuperação: `{consolidated['retrieval_status_counts']}`",
        f"- Totais (raw/descartados/mantidos): `{consolidated['totals']['total_raw']}` / `{consolidated['totals']['total_discarded']}` / `{consolidated['totals']['total_kept']}`",
        f"- Fontes únicas após deduplicação: `{consolidated['totals']['unique_sources_after_dedup']}`",
        f"- Failed quality gate runs: `{len(failed_quality_gates)}`",
        "",
        "## Before vs After",
        "- Before: `reports/scale_web_scan_real_mode.md` mostrou domínio de resultados irrelevantes e `analytical_data_source=0`.",
        "- After: esta execução aplica hardening de consulta, tiers de domínio, filtro negativo forte e quality gates por lote.",
        "",
        "## Analytical vs Scientific",
        f"- source_class_totals: `{consolidated['source_class_totals']}`",
        "",
        "## Top domínios",
    ]
    report_lines.extend([f"- {d}: {c}" for d, c in consolidated["top_domains"][:15]])
    report_lines.extend(["", "## Estatísticas por lote"])
    report_lines.extend(
        [
            (
                f"- {r['theme']} | run={r['run_id']} | mode={r.get('connector_mode_used')} "
                f"| status={r.get('retrieval_status')} | quality_gate={r.get('quality_gate_status')} "
                f"| raw={r.get('raw_result_count')} | discarded={r.get('discarded_result_count')} | kept={r.get('kept_result_count')}"
            )
            for r in run_stats
        ]
    )
    report_lines.extend(
        [
            "",
            "## JSON outputs gerados",
            f"- `{out_json}`",
            "- `data/runs/<run_id>/01_research-scout.json` (raw/discarded/kept + quality gate por lote)",
            "- `data/runs/<run_id>/02_query-expansion.json`",
            "- `data/runs/<run_id>/03_dataset-discovery.json`",
            "- `data/runs/<run_id>/04_normalization.json`",
            "- `data/runs/<run_id>/05_relevance.json`",
            "- `data/runs/<run_id>/06_access.json`",
            "- `data/runs/<run_id>/07_extraction-plan.json`",
            "- `data/runs/<run_id>/08_report.json`",
            "- `data/runs/<run_id>/catalog.json`",
        ]
    )

    md_path = Path("reports") / "scale_web_scan_real_mode_v2_quality_hardened.md"
    md_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(out_json)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
