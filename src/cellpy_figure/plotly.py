"""Draw one panel with Plotly.

Facet rows and extra panels are refused. Matplotlib lives in ``mpl.py``.
The stroke scale uses the same words as matplotlib (``solid``, ``dashed``,
``dotted``, ``dashdot``). This module translates them into Plotly dashes.
"""

from __future__ import annotations

from typing import Any

from cellpy_figure.io import BundleError, _as_pandas
from cellpy_figure.model import Encoding, Figure, Panel
from cellpy_figure.presets import get_preset

_EXTRA = 'plotly is required for to_plotly(); pip install "cellpy-figure[plotly]"'
_SEQUENTIAL_COLORSCALE = "Viridis"
_MM_PER_INCH = 25.4
_PX_PER_INCH = 96
_DASH = {
    "solid": "solid",
    "dashed": "dash",
    "dotted": "dot",
    "dashdot": "dashdot",
    "dash": "dash",
    "dot": "dot",
    "longdash": "longdash",
    "longdashdot": "longdashdot",
}


def render(figure: Figure, *, preset: str = "notebook", **overrides: Any) -> Any:
    """Draw ``figure`` with Plotly.

    Args:
        figure: A ``cellpy_figure.Figure`` with one panel and no facet.
        preset: Preset name. Supplies the layout mapping and the default size.
            It does not change a quantitative color encoding into a nominal one.
        overrides: ``width_mm`` and ``height_mm`` replace the preset size.

    Returns:
        A ``plotly.graph_objects.Figure``. Further edits belong to the caller.

    Raises:
        ImportError: The ``plotly`` extra is not installed.
        BundleError: The figure is not one drawable panel, or an encoding
            does not match the table.
        ValueError: ``preset`` is unknown, or an override is not a size.
    """
    go = _graph_objects()
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

    fig = go.Figure()
    fig.update_layout(**chosen.plotly_layout)
    if panel.color is not None and panel.color.type == "quantitative":
        _draw_quantitative(fig, go, frame, panel)
    else:
        _draw_nominal(fig, go, frame, panel)
    fig.update_layout(
        width=_px(width),
        height=_px(height),
        title=figure.title,
        xaxis_title=_axis_label(panel.x),
        yaxis_title=_axis_label(panel.y),
    )
    return fig


def _graph_objects():
    try:
        import plotly.graph_objects as go
    except ImportError as exc:
        raise ImportError(_EXTRA) from exc
    return go


def _px(mm: float) -> int:
    return round(mm / _MM_PER_INCH * _PX_PER_INCH)


def _one_panel(figure: Figure) -> Panel:
    count = len(figure.panels)
    if count != 1:
        raise BundleError(
            f"to_plotly draws one panel; this figure has {count}. "
            "Facet rows are not drawn yet."
        )
    panel = figure.panels[0]
    if panel.facet is not None:
        raise BundleError(
            "facet encodings are not drawn yet. to_plotly draws one panel."
        )
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


def _draw_nominal(fig, go, frame, panel: Panel) -> None:
    color = panel.color
    stroke = panel.stroke
    fields = [enc.field for enc in (color, stroke) if enc is not None]
    palette = _colorway(fig)
    color_of: dict[Any, str] = {}
    if color is not None:
        categories = list(dict.fromkeys(frame[color.field].tolist()))
        color_of = {
            category: palette[i % len(palette)] for i, category in enumerate(categories)
        }
    for key, group in _groups(frame, fields):
        color_value = key[0] if color is not None else None
        stroke_value = key[-1] if stroke is not None else None
        dash = "solid"
        if stroke is not None:
            dash = _dash(stroke_value, stroke.scale)
        name = _series_label(
            color_value, stroke_value, color is not None, stroke is not None
        )
        line: dict[str, Any] = {"dash": dash}
        if color is not None:
            line["color"] = color_of[color_value]
        fig.add_trace(
            go.Scatter(
                x=group[panel.x.field],
                y=group[panel.y.field],
                mode="lines",
                name=name or "",
                line=line,
                showlegend=name is not None,
            )
        )
    if color is not None and color.legend_title and fig.data:
        fig.update_layout(legend_title_text=color.legend_title)


def _draw_quantitative(fig, go, frame, panel: Panel) -> None:
    color = panel.color
    assert color is not None
    values = _numeric_color(frame, color.field)
    vmin = float(values.min())
    vmax = float(values.max())
    if vmin == vmax:
        vmax = vmin + 1.0
    stroke = panel.stroke
    fields = [stroke.field] if stroke is not None else []
    label = color.legend_title or _axis_label(color)
    first = True
    for key, group in _groups(frame, fields):
        dash = "solid"
        name = label
        if stroke is not None:
            dash = _dash(key[0], stroke.scale)
            name = str(key[0])
        colors = values.loc[group.index].tolist()
        marker: dict[str, Any] = {
            "color": colors,
            "colorscale": _SEQUENTIAL_COLORSCALE,
            "cmin": vmin,
            "cmax": vmax,
            "showscale": first,
            "size": 6,
        }
        if first:
            marker["colorbar"] = {"title": {"text": label}}
        fig.add_trace(
            go.Scatter(
                x=group[panel.x.field],
                y=group[panel.y.field],
                mode="lines+markers",
                name=name,
                marker=marker,
                line={"dash": dash},
            )
        )
        first = False


def _colorway(fig) -> list[str]:
    colors = list(fig.layout.colorway or [])
    if colors:
        return [str(color) for color in colors]
    template = fig.layout.template
    if template is not None and template.layout and template.layout.colorway:
        return [str(color) for color in template.layout.colorway]
    return ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"]


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
    for position in range(len(frame)):
        key = tuple(column[position] for column in columns)
        buckets.setdefault(key, []).append(position)
    for key, indexes in buckets.items():
        yield key, frame.iloc[indexes]


def _scale_value(value: Any, scale: dict[str, str] | None) -> str:
    if scale is None:
        return "solid"
    if value in scale:
        return scale[value]
    text = str(value)
    if text in scale:
        return scale[text]
    known = ", ".join(repr(key) for key in scale)
    raise BundleError(f"stroke value {value!r} is not in the scale (keys: {known}).")


def _dash(value: Any, scale: dict[str, str] | None) -> str:
    name = _scale_value(value, scale)
    dash = _DASH.get(name)
    if dash is None:
        known = ", ".join(sorted(set(_DASH)))
        raise BundleError(
            f"stroke style {name!r} is not a dash Plotly can draw (expected one of: {known})."
        )
    return dash


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
