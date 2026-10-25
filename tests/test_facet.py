"""One facet row over a long summary table."""

import os

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from cellpy_figure import BundleError, Encoding, Figure, Panel, Provenance
from cellpy_figure.plotly import _px

_MM = 25.4


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "cycle": [1, 2, 1, 2, 1, 2, 3],
            "value": [10.0, 11.0, 90.0, 91.0, 0.1, 0.2, 0.0],
            "variable": [
                "capacity",
                "capacity",
                "efficiency",
                "efficiency",
                "ir",
                "ir",
                None,
            ],
        }
    )


def _figure() -> Figure:
    return Figure(
        data=_frame(),
        panels=[
            Panel(
                x=Encoding("cycle", label="Cycle"),
                y=Encoding("value", label="Value"),
                facet=Encoding("variable"),
            )
        ],
        title="Summary",
        provenance=Provenance("cellpy", "0.1.0"),
    )


def test_three_facet_values_draw_three_panels():
    fig = _figure().to_matplotlib()
    try:
        assert [ax.get_title() for ax in fig.axes] == ["capacity", "efficiency", "ir"]
        assert list(fig.axes[0].lines[0].get_xdata()) == [1.0, 2.0]
        assert list(fig.axes[0].lines[0].get_ydata()) == [10.0, 11.0]
        assert list(fig.axes[1].lines[0].get_ydata()) == [90.0, 91.0]
        assert list(fig.axes[2].lines[0].get_ydata()) == pytest.approx([0.1, 0.2])
        width, height = fig.get_size_inches()
        assert width == pytest.approx(160 / _MM)
        assert height == pytest.approx(100 / _MM)
    finally:
        plt.close(fig)

    plotted = _figure().to_plotly()
    titles = [annotation.text for annotation in plotted.layout.annotations]
    assert titles == ["capacity", "efficiency", "ir"]
    by_axis = {trace.xaxis: list(trace.y) for trace in plotted.data}
    assert by_axis["x"] == [10.0, 11.0]
    assert by_axis["x2"] == [90.0, 91.0]
    assert by_axis["x3"] == pytest.approx([0.1, 0.2])
    assert list(plotted.data[0].x) == [1, 2]
    assert plotted.layout.xaxis.title.text == "Cycle"
    assert plotted.layout.yaxis2.title.text == "Value"
    assert plotted.layout.width == _px(160)
    assert plotted.layout.height == _px(100)


def test_missing_facet_column_names_the_column():
    figure = _figure()
    figure.panels[0].facet = Encoding("absent")
    message = r"panel 1 facet names column 'absent'"
    with pytest.raises(BundleError, match=message):
        figure.to_matplotlib()
    with pytest.raises(BundleError, match=message):
        figure.to_plotly()
