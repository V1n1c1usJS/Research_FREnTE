"""Utilitários transversais do projeto."""

from src.utils.io import ensure_dir, write_bytes, write_catalog_csv, write_json, write_markdown
from src.utils.logging import configure_logging

try:
    from src.utils.prompts import load_prompt
except ImportError:  # pragma: no cover - depende do ambiente local
    def load_prompt(*args, **kwargs):  # type: ignore[no-redef]
        raise RuntimeError("Dependencias para carregar prompts nao estao disponiveis no ambiente atual.")

__all__ = [
    "configure_logging",
    "ensure_dir",
    "load_prompt",
    "write_bytes",
    "write_catalog_csv",
    "write_json",
    "write_markdown",
]
