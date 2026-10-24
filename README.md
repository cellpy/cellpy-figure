# cellpy-figure

A figure file (`.cfz`) that holds the plotted table and the choices that drew
it, so a coauthor can redraw it with matplotlib or Plotly without installing
cellpy.

The design, the file format, and what cellpy and cellpy-simple-gui are
expected to do are in [PLAN.md](PLAN.md). Reading and writing a `.cfz` file
works. ``to_matplotlib`` draws one panel. Plotly rendering and facet rows
are not implemented yet.
