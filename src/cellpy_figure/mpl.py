"""Draw one panel with matplotlib.

A facet encoding draws that panel as one row. Extra panel entries are
refused. Plotly lives in ``plotly.py``.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from cellpy_figure.facets import facet_slices
from cellpy_figure.io import BundleError, _as_pandas
from cellpy_figure.model import Encoding, Figure, Panel
from cellpy_figure.presets import get_preset

_EXTRA = 'matplotlib is required for to_matplotlib(); pip install "cellpy-figure[mpl]"'
_SEQUENTIAL_CMAP = "viridis"
_MM_PER_INCH = 25.4


def render(figure: Figure, *, preset: str = "notebook", **overrides: Any) -> Any:
    """Draw ``figure`` with matplotlib.

    Args:
        figure: A ``cellpy_figure.Figure`` with one panel. A facet encoding
            draws that panel as one row of subplots.
        preset: Preset name. Supplies ``rcParams`` and the default size.
            It does not change a quantitative color encoding into a nominal one.
        overrides: ``width_mm`` and ``height_mm`` replace the preset size.

    Returns:
        A ``matplotlib.figure.Figure``. Further edits belong to the caller.

    Raises:
        ImportError: The ``mpl`` extra is not installed.
        BundleError: The figure has several panels, or an encoding does not
            match the table.
        ValueError: ``preset`` is unknown, or an override is not a size.
    """
    plt = _pyplot()
    unknown = sorted(set(overrides) - {"width_mm", "height_mm"})
    if unknown:
        names = ", ".join(unknown)
        raise ValueError(f"unknown override {names}; expected width_mm and height_mm.")
    chosen = get_preset(preset)
    width = float(overrides.get("width_mm", chosen.width_mm))
    height = float(overrides.get("height_mm", chosen.height_mm))
    if width <= 0 or height <= 0:
        raise ValueError("width_mm and height_mm must be positive.")
    panel = _one_panel(figure)
    frame = _as_pandas(figure.data)
    _require_columns(frame, panel)

    size = (width / _MM_PER_INCH, height / _MM_PER_INCH)
    with plt.rc_context(dict(chosen.rcparams)):
        if panel.facet is None:
            fig, ax = plt.subplots(figsize=size)
            _draw_panel(ax, fig, frame, panel)
            ax.set_xlabel(_axis_label(panel.x))
            ax.set_ylabel(_axis_label(panel.y))
            if figure.title:
                ax.set_title(figure.title)
            fig.tight_layout()
            return fig
        slices = facet_slices(frame, panel.facet.field)
        fig, axes = plt.subplots(1, len(slices), figsize=size, squeeze=False)
        color_of = _nominal_colors(frame, panel)
        values = _quantitative_values(frame, panel)
        for index, (title, part) in enumerate(slices):
            ax = axes[0, index]
            _draw_panel(
                ax,
                fig,
                part,
                panel,
                color_of=color_of,
                values=values,
                legend=index == 0,
                colorbar=index == 0,
            )
            ax.set_xlabel(_axis_label(panel.x))
            ax.set_ylabel(_axis_label(panel.y))
            ax.set_title(str(title))
        if figure.title:
            fig.suptitle(figure.title)
        fig.tight_layout()
    return fig


def _pyplot():
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(_EXTRA) from exc
    return plt


def _one_panel(figure: Figure) -> Panel:
    count = len(figure.panels)
    if count != 1:
        raise BundleError(
            f"to_matplotlib draws one panel; this figure has {count}. "
            "Several panel entries are not a facet row."
        )
    panel = figure.panels[0]
    if panel.color is not None and panel.color.type not in ("nominal", "quantitative"):
        raise BundleError(
            "panel 1 color.type must be nominal or quantitative; "
            f"got {panel.color.type!r}."
        )
    return panel


def _require_columns(frame, panel: Panel) -> None:
    listed = ", ".join(frame.columns) or "none"
    channels: list[tuple[str, Encoding | None]] = [
        ("x", panel.x),
        ("y", panel.y),
        ("color", panel.color),
        ("stroke", panel.stroke),
        ("facet", panel.facet),
    ]
    for name, encoding in channels:
        if encoding is None:
            continue
        if encoding.field not in frame.columns:
            raise BundleError(
                f"panel 1 {name} names column {encoding.field!r}, "
                f"which is not in the table (columns: {listed})."
            )


def _axis_label(encoding: Encoding) -> str:
    text = encoding.label or encoding.field
    if encoding.unit:
        return f"{text} ({encoding.unit})"
    return text


def _draw_panel(
    ax,
    fig,
    frame,
    panel: Panel,
    *,
    color_of: dict[Any, str] | None = None,
    values=None,
    legend: bool = True,
    colorbar: bool = True,
) -> None:
    if panel.color is not None and panel.color.type == "quantitative":
        _draw_quantitative(ax, fig, frame, panel, values=values, colorbar=colorbar)
    else:
        _draw_nominal(ax, frame, panel, color_of=color_of, legend=legend)


def _nominal_colors(frame, panel: Panel) -> dict[Any, str] | None:
    color = panel.color
    if color is None or color.type == "quantitative":
        return None
    import matplotlib.pyplot as plt

    palette = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    categories = list(dict.fromkeys(frame[color.field].tolist()))
    return {
        category: palette[i % len(palette)] for i, category in enumerate(categories)
    }


def _quantitative_values(frame, panel: Panel):
    color = panel.color
    if color is None or color.type != "quantitative":
        return None
    return _numeric_color(frame, color.field)


def _draw_nominal(
    ax,
    frame,
    panel: Panel,
    *,
    color_of: dict[Any, str] | None = None,
    legend: bool = True,
) -> None:
    color = panel.color
    stroke = panel.stroke
    fields = [enc.field for enc in (color, stroke) if enc is not None]
    if color is not None and color_of is None:
        import matplotlib.pyplot as plt

        palette = plt.rcParams["axes.prop_cycle"].by_key()["color"]
        categories = list(dict.fromkeys(frame[color.field].tolist()))
        color_of = {
            category: palette[i % len(palette)] for i, category in enumerate(categories)
        }
    for key, group in _groups(frame, fields):
        color_value = key[0] if color is not None else None
        stroke_value = key[-1] if stroke is not None else None
        linestyle = "solid"
        if stroke is not None:
            linestyle = _linestyle(stroke_value, stroke.scale)
        label = _series_label(
            color_value, stroke_value, color is not None, stroke is not None
        )
        kwargs: dict[str, Any] = {"linestyle": linestyle}
        if color is not None and color_of is not None:
            kwargs["color"] = color_of[color_value]
        if label is not None and legend:
            kwargs["label"] = label
        ax.plot(group[panel.x.field], group[panel.y.field], **kwargs)
    if legend:
        _legend(ax, color)


def _draw_quantitative(
    ax, fig, frame, panel: Panel, *, values=None, colorbar: bool = True
) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection

    color = panel.color
    assert color is not None
    if values is None:
        values = _numeric_color(frame, color.field)
    vmin = float(values.min())
    vmax = float(values.max())
    if vmin == vmax:
        vmax = vmin + 1.0
    norm = plt.Normalize(vmin, vmax)
    cmap = plt.get_cmap(_SEQUENTIAL_CMAP)
    stroke = panel.stroke
    fields = [stroke.field] if stroke is not None else []
    mappable = None
    for key, group in _groups(frame, fields):
        linestyle = "solid"
        if stroke is not None:
            linestyle = _linestyle(key[0], stroke.scale)
        indexes = group.index
        xs = group[panel.x.field].to_numpy(dtype=float)
        ys = group[panel.y.field].to_numpy(dtype=float)
        colors = values.loc[indexes].to_numpy(dtype=float)
        if len(xs) < 2:
            mappable = ax.scatter(xs, ys, c=colors, cmap=cmap, norm=norm)
            continue
        points = np.column_stack([xs, ys]).reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        collection = LineCollection(
            segments, cmap=cmap, norm=norm, linestyles=linestyle
        )
        collection.set_array(colors[:-1])
        ax.add_collection(collection)
        mappable = collection
    ax.autoscale_view()
    if colorbar and mappable is not None:
        label = color.legend_title or _axis_label(color)
        fig.colorbar(mappable, ax=ax, label=label)


def _numeric_color(frame, field: str):
    values = frame[field]
    numeric = values if values.dtype.kind in "iuf" else values.map(_as_float)
    numeric = numeric.astype(float)
    if numeric.notna().sum() == 0:
        raise BundleError(
            f"panel 1 color column {field!r} has no numeric values "
            "for a quantitative scale."
        )
    return numeric


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _groups(frame, fields: list[str]):
    if not fields:
        yield (), frame
        return
    columns = [frame[field].tolist() for field in fields]
    buckets: dict[tuple[Any, ...], list[int]] = {}
    positions = list(range(len(frame)))
    for position in positions:
        key = tuple(column[position] for column in columns)
        buckets.setdefault(key, []).append(position)
    for key, indexes in buckets.items():
        yield key, frame.iloc[indexes]


def _linestyle(value: Any, scale: dict[str, str] | None) -> str:
    if scale is None:
        return "solid"
    if value in scale:
        return scale[value]
    text = str(value)
    if text in scale:
        return scale[text]
    known = ", ".join(repr(key) for key in scale)
    raise BundleError(f"stroke value {value!r} is not in the scale (keys: {known}).")


def _series_label(
    color_value, stroke_value, has_color: bool, has_stroke: bool
) -> str | None:
    parts = []
    if has_color:
        parts.append(str(color_value))
    if has_stroke:
        parts.append(str(stroke_value))
    if not parts:
        return None
    return ", ".join(parts)


def _legend(ax, color: Encoding | None) -> None:
    _handles, labels = ax.get_legend_handles_labels()
    if not labels:
        return
    title = color.legend_title if color is not None else None
    ax.legend(title=title)
