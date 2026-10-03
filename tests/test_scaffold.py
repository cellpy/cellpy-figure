"""Scaffold checks: the public objects exist, and unfinished paths say so."""

import pytest

import cellpy_figure
from cellpy_figure import Encoding, Figure, Panel, Provenance, open_figure
from cellpy_figure.presets import get_preset


def test_version_is_set():
    assert cellpy_figure.__version__ == "0.1.0"


def test_figure_holds_a_panel():
    figure = Figure(
        data=[{"capacity": 1.0, "voltage": 3.5, "cycle": 1}],
        panels=[
            Panel(
                x=Encoding("capacity", label="Capacity", unit="mAh/g"),
                y=Encoding("voltage", label="Voltage", unit="V"),
                color=Encoding("cycle", type="nominal", legend_title="Cycle"),
            )
        ],
        title="Charge-Discharge Curves",
        provenance=Provenance("cellpy", "0.0.0", note="Plotted rows only."),
    )
    assert figure.panels[0].x.field == "capacity"
    assert figure.provenance.producer == "cellpy"


def test_write_and_open_are_not_implemented_yet():
    figure = Figure(data=[], panels=[])
    with pytest.raises(NotImplementedError, match="writing"):
        figure.write("out.cfz")
    with pytest.raises(NotImplementedError, match="reading"):
        open_figure("out.cfz")


def test_render_reaches_the_renderer():
    figure = Figure(data=[], panels=[])
    with pytest.raises(NotImplementedError, match="matplotlib"):
        figure.to_matplotlib()
    with pytest.raises(NotImplementedError, match="plotly"):
        figure.to_plotly()


def test_unknown_preset_names_the_known_ones():
    with pytest.raises(ValueError, match="acs-single"):
        get_preset("journal")
