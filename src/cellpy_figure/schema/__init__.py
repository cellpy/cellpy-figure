"""JSON Schema for format version 1, loaded from this package."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any


def load_schema() -> dict[str, Any]:
    """Return the format-version 1 schema shipped with this package.

    Returns:
        The parsed ``figure-1.json`` document. Callers validate with it.
        ``open_figure`` does not.
    """
    text = (
        files("cellpy_figure.schema")
        .joinpath("figure-1.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(text)
