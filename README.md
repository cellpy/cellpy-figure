# cellpy-figure

A figure file (`.cfz`) that holds the plotted table and the choices that drew
it, so a coauthor can redraw it with matplotlib or Plotly without installing
cellpy.

```bash
pip install "cellpy-figure[mpl]"
```

```python
import cellpy_figure

figure = cellpy_figure.open_figure("figure.cfz")
drawn = figure.to_matplotlib(preset="notebook")
drawn.savefig("figure.pdf")
```

The design, the file format, and what cellpy and cellpy-simple-gui are
expected to do are in [PLAN.md](PLAN.md). Reading and writing a `.cfz` file
works. ``to_matplotlib`` and ``to_plotly`` draw one panel, or one facet
row. The format-version 1 JSON Schema ships in the package. Version 0.1.0
is on PyPI. The next release follows the Release & version bump section of
`.issueflows/04-designs-and-guides/this-project.md`. Several panel entries
are not implemented yet.
