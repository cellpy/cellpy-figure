# Issue #5: Facet a long summary table

Source: https://github.com/cellpy/cellpy-figure/issues/5

## Original issue text

A summary figure is one long table with a column that names the panel (one row per cell, cycle, and variable). Version 1 has to draw that as a facet row. The `facet` field exists on `Panel` and will be stored by #1, but neither renderer draws it.

Blocked by #2 and #3.

## Spec

- One panel with a facet encoding whose field is the variable column. Panels share x and differ in y.
- Both `to_matplotlib` and `to_plotly` draw one row of facets, using the same preset size.
- Several `panels` entries remain the path when panels do not share an x column. Do not force that shape into a facet.
- Synthetic long tables only. Do not import cellpy.

## Acceptance criteria

- A long table with three facet values produces three panels in matplotlib and three panels in Plotly.
- Each facet uses the y field for that value, and the shared x field.
- A missing facet column raises the same class of error as any other missing encoding column (named column and panel).

## Out of scope

- Density films, step bands, and Plotly chrome.
- A second panel-mapping for battery plot families. Those stay in cellpy.
- JSON Schema file and PyPI, except that the facet encoding must stay valid against the schema from #4.
