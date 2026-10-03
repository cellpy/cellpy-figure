"""Plotly renderer. Drawing is not implemented yet."""

from __future__ import annotations

from typing import Any

from cellpy_figure.presets import get_preset

_EXTRA = 'plotly is required for to_plotly(); pip install "cellpy-figure[plotly]"'


def render(figure: Any, *, preset: str = "notebook", **_overrides: Any) -> Any:
    """Draw ``figure`` with Plotly.

    Args:
        figure: A ``cellpy_figure.Figure``.
        preset: Preset name.
        overrides: Reserved for size overrides.

    Returns:
        A ``plotly.graph_objects.Figure``.

    Raises:
        ImportError: The ``plotly`` extra is not installed.
        NotImplementedError: Rendering is not implemented yet.
    """
    try:
        import plotly  # noqa: F401
    except ImportError as exc:
        raise ImportError(_EXTRA) from exc
    get_preset(preset)
    raise NotImplementedError("plotly rendering is not implemented yet")
