"""Matplotlib renderer. Drawing is not implemented yet."""

from __future__ import annotations

from typing import Any

from cellpy_figure.presets import get_preset

_EXTRA = 'matplotlib is required for to_matplotlib(); pip install "cellpy-figure[mpl]"'


def render(figure: Any, *, preset: str = "notebook", **_overrides: Any) -> Any:
    """Draw ``figure`` with matplotlib.

    Args:
        figure: A ``cellpy_figure.Figure``.
        preset: Preset name.
        overrides: Reserved for size overrides.

    Returns:
        A ``matplotlib.figure.Figure``.

    Raises:
        ImportError: The ``mpl`` extra is not installed.
        NotImplementedError: Rendering is not implemented yet.
    """
    try:
        import matplotlib  # noqa: F401
    except ImportError as exc:
        raise ImportError(_EXTRA) from exc
    get_preset(preset)
    raise NotImplementedError("matplotlib rendering is not implemented yet")
