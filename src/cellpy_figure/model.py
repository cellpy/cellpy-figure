"""Figure model: a tidy table plus the encodings that draw it.

The on-disk schema is not implemented yet. These types are the in-memory
shape ``PLAN.md`` describes, so callers can build a figure before write
and render exist.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ColorType = Literal["nominal", "quantitative"]


@dataclass
class Encoding:
    """One visual channel, bound to a column of the plotted table.

    Args:
        field: Column name in the figure table.
        label: Axis title. Used for x and y. Ignored by color and stroke
            when ``legend_title`` is set.
        unit: Unit string appended to an axis label, such as ``mAh/g``.
        type: ``nominal`` (one colour per category) or ``quantitative``
            (a sequential scale). Meaningful for color.
        legend_title: Title drawn above the legend for this channel.
        scale: Explicit map from category to a renderer value, such as
            ``{"charge": "solid", "discharge": "dashed"}``.
    """

    field: str
    label: str | None = None
    unit: str | None = None
    type: ColorType | None = None
    legend_title: str | None = None
    scale: dict[str, str] | None = None


@dataclass
class Panel:
    """One panel: x and y, plus optional color, stroke, and facet encodings."""

    x: Encoding
    y: Encoding
    color: Encoding | None = None
    stroke: Encoding | None = None
    facet: Encoding | None = None


@dataclass
class Provenance:
    """Who wrote the bundle, and whether the table is a filtered sample.

    Args:
        producer: Short name of the writer, such as ``cellpy``.
        producer_version: Version of that writer.
        note: Free text. Use it to say the table is plotted rows only.
        source: Path or hash of the file the writer read, when known.
    """

    producer: str
    producer_version: str
    note: str | None = None
    source: str | None = None


@dataclass
class Figure:
    """A plotted table and the panels that describe how to draw it.

    Args:
        data: The plotted rows. A ``pandas.DataFrame`` or a
            ``polars.DataFrame``. Stored as given until write exists.
        panels: One or more panels sharing ``data``.
        title: Figure title.
        provenance: Writer identity. Required once the bundle is written.
        extensions: Producer-specific payload. Readers ignore it.
    """

    data: Any
    panels: list[Panel]
    title: str | None = None
    provenance: Provenance | None = None
    extensions: dict[str, Any] = field(default_factory=dict)

    def write(self, path: str) -> None:
        """Write this figure to a ``.cfz`` bundle.

        Raises:
            NotImplementedError: Bundle writing is not implemented yet.
        """
        raise NotImplementedError("writing a .cfz bundle is not implemented yet")

    def to_matplotlib(self, preset: str = "notebook", **overrides: Any) -> Any:
        """Draw this figure with matplotlib.

        Args:
            preset: Name of a preset in ``cellpy_figure.presets``.
            overrides: Reserved for size overrides. Unused until rendering exists.

        Returns:
            A ``matplotlib.figure.Figure``.

        Raises:
            ImportError: Matplotlib is not installed.
            NotImplementedError: Rendering is not implemented yet.
        """
        from cellpy_figure.mpl import render

        return render(self, preset=preset, **overrides)

    def to_plotly(self, preset: str = "notebook", **overrides: Any) -> Any:
        """Draw this figure with Plotly.

        Args:
            preset: Name of a preset in ``cellpy_figure.presets``.
            overrides: Reserved for size overrides. Unused until rendering exists.

        Returns:
            A ``plotly.graph_objects.Figure``.

        Raises:
            ImportError: Plotly is not installed.
            NotImplementedError: Rendering is not implemented yet.
        """
        from cellpy_figure.plotly import render

        return render(self, preset=preset, **overrides)
