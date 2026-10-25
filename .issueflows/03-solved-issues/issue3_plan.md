# Issue #3 plan: Draw one panel with Plotly

## Goal

`Figure.to_plotly` returns a `plotly.graph_objects.Figure` for one panel, using the same encodings and preset names as matplotlib. Facet rows stay refused.

## Constraints

- One panel only. A facet encoding or any other panel count raises `BundleError`.
- Nominal color is one series per category. The same category keeps one color across stroke values. Quantitative color stays sequential (`Viridis`) and a preset must not flip it.
- Stroke words stay the file's words (`solid`, `dashed`, `dotted`, `dashdot`). Plotly receives `solid`, `dash`, `dot`, `dashdot`.
- Size overrides are only `width_mm` and `height_mm`, and both must be positive. Pixels are `round(mm / 25.4 * 96)`.
- A missing Plotly install raises `ImportError` whose text names `pip install "cellpy-figure[plotly]"`. Drawing must not import matplotlib.
- Out of scope: matplotlib changes, facet rows, JSON Schema, PyPI, hover text, and modebar state.
- The worktree already contains this design, uncommitted. Accept confirms it.

### Prior art

- `cellpy_figure.mpl.render` — mirror. Same panel gate, column check, grouping, and preset size rules. Coexist: `plotly.py` keeps private copies and does not import `mpl`, so a Plotly figure does not load matplotlib.
- `cellpy_figure.presets.Preset.plotly_layout` — reuse. `notebook`, `acs-single`, and `nature-single` already carry font sizes 11, 8, and 7.
- `cellpy_figure.model.Figure.to_plotly` — already delegates to `plotly.render`.
- Toolbox: none. Graph: no `graphify-out/graph.json`.

## Approach

1. Import `plotly.graph_objects` inside the renderer. On `ImportError`, raise the extra message.
2. Resolve the preset, apply `width_mm` / `height_mm`, and refuse any other override.
3. Require exactly one panel and no facet. Require `x`, `y`, and any color or stroke column to exist.
4. Apply `preset.plotly_layout`, then set width, height, title, and axis titles (`label` or field, plus unit).
5. Nominal: one `Scatter` in `lines` mode per (color, stroke) group, in appearance order. Colors come from the layout colorway. Legend title is the color encoding's `legend_title`.
6. Quantitative: one `Scatter` in `lines+markers` mode per stroke group. Marker colorscale is `Viridis`, with one shared `cmin`/`cmax`. The colorbar is on the first trace only. A constant column gets `cmax = cmin + 1`.
7. An unknown stroke scale value or an unmapped dash name raises `BundleError`.

## Files to touch

- `src/cellpy_figure/plotly.py` — replace the import-check stub with `render` and the helpers above.
- `src/cellpy_figure/model.py` — document `to_plotly` overrides and the `BundleError` / `ValueError` cases.
- `src/cellpy_figure/presets.py` — docstring only: `plotly_layout` is applied by `to_plotly`.
- `tests/test_plotly.py` — new. Count traces and layout fields.
- `tests/test_scaffold.py` — drop the "not implemented" assertion.
- `README.md`, `PLAN.md` — status: both renderers draw one panel; facets, schema, and publishing do not.

## Test strategy

From the worktree, with extras installed:

```bash
uv sync --locked --all-extras --dev
uv run ruff check
uv run ruff format --check
MPLBACKEND=Agg uv run pytest
```

Cases: nominal color plus stroke (four traces, shared colors, `dashed` → `dash`); nominal color without stroke (two traces); quantitative color stays `Viridis` with shared limits for `notebook` and `acs-single`; `acs-single` size and font, plus a `width_mm` override; facet and extra panel refused; missing Plotly names the extra.

## Open questions

- None. Helper copies stay in `plotly.py` rather than a shared module, because this issue does not change matplotlib.
