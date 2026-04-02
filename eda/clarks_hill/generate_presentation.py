"""
Prepare the report-context handoff for the Clarks Hill HTML layer.

This scaffold intentionally stops before rendering HTML. The final HTML should be
assembled by the dedicated report agent once figures and narrative context are ready.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


EDA_DIR = Path(__file__).resolve().parent
CONTEXT_TEMPLATE = EDA_DIR / "report_context.template.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the report-context payload before HTML rendering."
    )
    parser.add_argument(
        "--context",
        type=Path,
        default=CONTEXT_TEMPLATE,
        help="Path to the report context JSON template or final payload.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.context.exists():
        raise SystemExit(f"Context file not found: {args.context}")

    payload = json.loads(args.context.read_text(encoding="utf-8"))

    print(f"Context file: {args.context}")
    print("Top-level keys:")
    for key in sorted(payload.keys()):
        print(f"- {key}")

    print("HTML rendering is intentionally deferred to the report agent.")


if __name__ == "__main__":
    main()
