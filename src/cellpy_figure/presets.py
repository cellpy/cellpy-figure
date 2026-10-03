"""Journal and notebook presets.

A preset is a size plus, later, a matplotlib ``rcParams`` mapping and a
Plotly layout mapping. Widths below are the usual single-column measures.
Heights are placeholders until rendering uses them.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Preset:
    """Named figure size.

    Args:
        name: Preset name passed to ``to_matplotlib`` and ``to_plotly``.
        width_mm: Figure width in millimetres.
        height_mm: Figure height in millimetres.
    """

    name: str
    width_mm: float
    height_mm: float


PRESETS: dict[str, Preset] = {
    "notebook": Preset("notebook", 160, 100),
    "acs-single": Preset("acs-single", 82.5, 60),
    "nature-single": Preset("nature-single", 89, 60),
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
