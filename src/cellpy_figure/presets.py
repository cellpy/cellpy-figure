"""Journal and notebook presets.

A preset is a size plus a matplotlib ``rcParams`` mapping and a Plotly
layout mapping. Widths below are the usual single-column measures.
The sequential color scale for a quantitative encoding is not a preset:
the file chooses nominal or quantitative, and the renderer keeps that choice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _rcparams(*, font: float, line: float, spine: float) -> dict[str, Any]:
    return {
        "font.size": font,
        "axes.labelsize": font,
        "axes.titlesize": font + 1,
        "legend.fontsize": max(font - 1, 6),
        "xtick.labelsize": max(font - 1, 6),
        "ytick.labelsize": max(font - 1, 6),
        "lines.linewidth": line,
        "axes.linewidth": spine,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }


def _plotly_layout(*, font: float) -> dict[str, Any]:
    return {
        "font": {"size": font},
        "margin": {"l": 48, "r": 16, "t": 40, "b": 40},
    }


@dataclass(frozen=True)
class Preset:
    """Named figure size and style.

    Args:
        name: Preset name passed to ``to_matplotlib`` and ``to_plotly``.
        width_mm: Figure width in millimetres.
        height_mm: Figure height in millimetres.
        rcparams: Matplotlib ``rcParams`` applied while drawing.
        plotly_layout: Plotly layout mapping. Drawing it is a later step.
    """

    name: str
    width_mm: float
    height_mm: float
    rcparams: dict[str, Any] = field(default_factory=dict)
    plotly_layout: dict[str, Any] = field(default_factory=dict)


PRESETS: dict[str, Preset] = {
    "notebook": Preset(
        "notebook",
        160,
        100,
        _rcparams(font=11, line=1.6, spine=0.8),
        _plotly_layout(font=11),
    ),
    "acs-single": Preset(
        "acs-single",
        82.5,
        60,
        _rcparams(font=8, line=1.0, spine=0.6),
        _plotly_layout(font=8),
    ),
    "nature-single": Preset(
        "nature-single",
        89,
        60,
        _rcparams(font=7, line=0.9, spine=0.5),
        _plotly_layout(font=7),
    ),
}


def get_preset(name: str) -> Preset:
    """Return a preset by name.

    Args:
        name: One of ``notebook``, ``acs-single``, ``nature-single``.

    Returns:
        The preset.

    Raises:
        ValueError: ``name`` is not a known preset. The message lists them.
    """
    try:
        return PRESETS[name]
    except KeyError:
        known = ", ".join(sorted(PRESETS))
        raise ValueError(f"unknown preset {name!r}; expected one of: {known}") from None
