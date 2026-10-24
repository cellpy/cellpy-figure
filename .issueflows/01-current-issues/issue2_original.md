# Issue #2: Draw one panel with matplotlib

Source: https://github.com/cellpy/cellpy-figure/issues/2

## Original issue text

A coauthor should get a real matplotlib Figure from a bundle and then call `set_xlim` or `savefig` themselves. `to_matplotlib` still raises NotImplementedError after the import check.

Blocked by #1.

## Spec

- Draw one panel: x and y fields, optional nominal or quantitative color, optional stroke with an explicit scale.
- Honour presets `notebook` and one journal preset (`acs-single` or `nature-single`): a matplotlib `rcParams` mapping plus a size in millimetres. Adding a journal stays a dictionary in `presets.py`.
- Return a `matplotlib.figure.Figure`. Do not add style methods on `cellpy_figure.Figure`.
- A missing matplotlib install raises an error that names `pip install "cellpy-figure[mpl]"`. Tests simulate the absence by monkeypatching the import.
- Run matplotlib with `MPLBACKEND=Agg`. No pixel snapshots.

## Acceptance criteria

- One panel with a color encoding and a stroke scale produces the expected number of series.
- Nominal color yields one series per category. Quantitative color is a sequential scale, and the preset does not override that choice.
- The stroke scale in the file (for example charge solid, discharge dashed) is what matplotlib draws.
- Without matplotlib, the error names the `mpl` extra.

## Out of scope

- Plotly.
- Facet rows (separate issue).
- JSON Schema and PyPI.
- Pixel comparison.
