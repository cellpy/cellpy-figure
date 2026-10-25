# Issue #5 plan: Facet a long summary table

## Goal

One panel with a facet encoding draws a single row of subplots in both matplotlib and Plotly. Three facet values produce three panels. A figure with no facet still draws one panel.

## Constraints

- Synthetic tables only. Do not import cellpy.
- The long table has one shared x column, one shared y column, and a facet column whose values name the panels. That matches cellpy's summary frame (`cycle_index`, `value`, `variable`). The facet value does not name a different y column.
- Several `panels` entries stay refused. They are the shape for panels that do not share x, and this issue does not draw that shape.
- The whole figure uses the preset size. Facets do not each get a full preset canvas.
- Color and stroke rules stay as they are: nominal color is one series per category, quantitative color stays Viridis, and stroke words stay the file's words.
- No new JSON keys. The writer already stores `facet`. Schema file and PyPI stay out.
- Out of scope: density films, step bands, Plotly chrome, and a battery-specific panel mapping.

### Prior art

- `cellpy_figure.mpl.render` and `cellpy_figure.plotly.render` — extend. Both refuse `panel.facet` today. One-panel tests must keep passing.
- `cellpy_figure.io._check_columns` — mirror. A missing facet column uses the same `panel N facet names column ...` error.
- cellpy `generate_summary_frame_for_plotting` — convention only. Columns are `cycle_index`, `variable`, `value`, `cell`. This package does not call it.
- Toolbox: none. Graph: no `graphify-out/graph.json`.
- Draw helpers stay copied in each renderer. The row split is data-only, so it lives in one shared function both renderers call. Neither renderer imports the other.

## Approach

1. Split the frame on the facet column in first-seen order. Drop null facet values. Each slice keeps the panel's x and y columns.
2. No facet: keep the current single axes or single set of traces.
3. With a facet: one row. Matplotlib uses `subplots(1, n)` inside the preset `rc_context`. Plotly uses `plotly.subplots.make_subplots` with the preset width and height. Import Plotly inside the renderer.
4. Each subplot title is the facet value. Axis titles stay the x and y encodings. The figure title stays the figure title.
5. Nominal colors are assigned once on the full table, so a category keeps its color across facets. The legend is drawn once. Quantitative color uses one shared `Viridis` range and one colorbar.
6. A missing facet column raises `BundleError` and names the column and the panel. Extra `panels` entries still raise `BundleError`.

## Files to touch

- `src/cellpy_figure/mpl.py` — draw the facet row; require the facet column.
- `src/cellpy_figure/plotly.py` — the same row, with Plotly subplots.
- `src/cellpy_figure/facets.py` — shared split of the table by facet value.
- `src/cellpy_figure/model.py` — docstrings: a facet row is drawn; extra panels are not.
- `tests/test_facet.py` — three facet values, shared x and per-value y, missing column.
- `README.md`, `PLAN.md` — status: one facet row is drawn; several panel entries, the schema, and publishing are not.

## Test strategy

From the worktree, with extras installed:

```bash
uv sync --locked --all-extras --dev
uv run ruff check
uv run ruff format --check
MPLBACKEND=Agg uv run pytest
```

New case: a long table with facet values `capacity`, `efficiency`, and `ir` produces three matplotlib axes and three Plotly subplots. Each panel's x data is the shared x column for that value, and its y data is the y column for that value. A missing facet column names the column. Existing one-panel tests stay as they are.

## Open questions

- None.
