"""Split a figure table into one row of facet panels.

Renderers share this split so matplotlib and Plotly keep the same panel
order. Drawing stays in each renderer.
"""

from __future__ import annotations

import pandas as pd

from cellpy_figure.io import BundleError


def facet_slices(
    frame: pd.DataFrame, field: str | None
) -> list[tuple[object, pd.DataFrame]]:
    """Return ``(title, rows)`` pairs in first-seen order.

    Args:
        frame: The figure table.
        field: Facet column. ``None`` means the whole table is one panel.

    Returns:
        One pair when there is no facet. Otherwise one pair per non-null
        facet value, in the order those values first appear.

    Raises:
        BundleError: The facet column has no values to draw.
    """
    if field is None:
        return [(None, frame)]
    column = frame[field]
    order: list[object] = []
    seen: set[object] = set()
    for value in column.tolist():
        if _missing(value) or value in seen:
            continue
        seen.add(value)
        order.append(value)
    if not order:
        raise BundleError(f"panel 1 facet column {field!r} has no values to draw.")
    return [(value, frame.loc[column == value]) for value in order]


def _missing(value: object) -> bool:
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False
