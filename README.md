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
row. The format-version 1 JSON Schema ships in the package. The publish
workflow is in the repository. The first upload waits on the pending
publisher. Several panel entries are not implemented yet.
