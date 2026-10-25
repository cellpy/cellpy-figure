# cellpy-figure

A figure file (`.cfz`) that holds the plotted table and the choices that drew
it, so a coauthor can redraw it with matplotlib or Plotly without installing
cellpy.

The design, the file format, and what cellpy and cellpy-simple-gui are
expected to do are in [PLAN.md](PLAN.md). Reading and writing a `.cfz` file
works. ``to_matplotlib`` and ``to_plotly`` draw one panel, or one facet
row. The format-version 1 JSON Schema ships in the package. Several panel
entries and publishing are not implemented yet.
