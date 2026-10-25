# Issue #3: Draw one panel with Plotly

Source: https://github.com/cellpy/cellpy-figure/issues/3

## Original issue text

The same bundle should also open as a Plotly figure. `to_plotly` still raises NotImplementedError after the import check.

Blocked by #1. Independent of the matplotlib issue; both can land in either order.

## Spec

- Draw the same encodings as matplotlib: one panel, x and y, optional nominal or quantitative color, optional stroke scale.
- Use the same preset names. A preset carries a Plotly layout mapping plus the size in millimetres.
- Return a `plotly.graph_objects.Figure`.
- A missing Plotly install raises an error that names `pip install "cellpy-figure[plotly]"`. Tests simulate the absence by monkeypatching the import.
- No pixel snapshots. Count traces, not pixels.

## Acceptance criteria

- One panel with a color encoding and a stroke scale produces the expected number of traces.
- Nominal and quantitative color follow the file, not the preset.
- The stroke scale in the file is applied.
- Without Plotly, the error names the `plotly` extra.

## Out of scope

- Matplotlib.
- Facet rows (separate issue).
- JSON Schema and PyPI.
- Plotly hover text, modebar state, and other renderer chrome.
