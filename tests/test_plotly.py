"""One-panel Plotly drawing. Count traces, not pixels."""

import builtins
import sys

import pandas as pd
import pytest

from cellpy_figure import BundleError, Encoding, Figure, Panel, Provenance
from cellpy_figure.plotly import _px


def _frame():
    return pd.DataFrame(
        {
            "capacity": [0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0],
            "voltage": [3.0, 4.0, 4.0, 3.0, 3.1, 4.1, 4.1, 3.1],
            "cycle": [1, 1, 1, 1, 2, 2, 2, 2],
            "direction": [
                "charge",
                "charge",
                "discharge",
                "discharge",
                "charge",
                "charge",
                "discharge",
                "discharge",
            ],
        }
    )


def _figure(*, color_type="nominal", with_stroke=True, cycles=None) -> Figure:
    frame = _frame()
    if cycles is not None:
        frame = frame.copy()
        frame["cycle"] = cycles
    color = Encoding("cycle", type=color_type, legend_title="Cycle")
    stroke = None
    if with_stroke:
        stroke = Encoding(
            "direction",
            scale={"charge": "solid", "discharge": "dashed"},
        )
    return Figure(
        data=frame,
        panels=[
            Panel(
                x=Encoding("capacity", label="Capacity", unit="mAh/g"),
                y=Encoding("voltage", label="Voltage", unit="V"),
                color=color,
                stroke=stroke,
            )
        ],
        title="Charge-Discharge Curves",
        provenance=Provenance("cellpy", "0.1.0"),
    )


def _by_name(fig):
    return {trace.name: trace for trace in fig.data}


def test_nominal_color_and_stroke_scale():
    fig = _figure().to_plotly()
    assert len(fig.data) == 4
    by_name = _by_name(fig)
    assert set(by_name) == {"1, charge", "1, discharge", "2, charge", "2, discharge"}
    assert by_name["1, charge"].line.dash == "solid"
    assert by_name["1, discharge"].line.dash == "dash"
    assert by_name["2, charge"].line.dash == "solid"
    assert by_name["1, charge"].line.color == by_name["1, discharge"].line.color
    assert by_name["1, charge"].line.color != by_name["2, charge"].line.color
    assert fig.layout.xaxis.title.text == "Capacity (mAh/g)"
    assert fig.layout.yaxis.title.text == "Voltage (V)"
    assert fig.layout.legend.title.text == "Cycle"


def test_nominal_color_is_one_trace_per_category():
    fig = _figure(with_stroke=False).to_plotly()
    assert len(fig.data) == 2
    assert {trace.name for trace in fig.data} == {"1", "2"}


def test_quantitative_color_stays_sequential_across_presets():
    cycles = [1, 1, 2, 2, 3, 3, 4, 4]
    scales = []
    for preset in ("notebook", "acs-single"):
        fig = _figure(color_type="quantitative", cycles=cycles).to_plotly(preset=preset)
        assert len(fig.data) == 2
        by_name = _by_name(fig)
        assert by_name["charge"].line.dash == "solid"
        assert by_name["discharge"].line.dash == "dash"
        for trace in fig.data:
            assert trace.marker.colorscale is not None
            assert trace.marker.cmin == 1
            assert trace.marker.cmax == 4
        scales.append(tuple(fig.data[0].marker.colorscale))
    assert scales[0] == scales[1]


def test_journal_preset_sets_size_and_font():
    fig = _figure(with_stroke=False).to_plotly(preset="acs-single")
    assert fig.layout.width == _px(82.5)
    assert fig.layout.height == _px(60)
    assert fig.layout.font.size == 8
    wider = _figure(with_stroke=False).to_plotly(preset="acs-single", width_mm=120)
    assert wider.layout.width == _px(120)


def test_facet_and_extra_panels_are_refused():
    figure = _figure()
    figure.panels[0].facet = Encoding("cycle")
    with pytest.raises(BundleError, match="facet"):
        figure.to_plotly()
    figure = _figure()
    figure.panels.append(Panel(x=Encoding("capacity"), y=Encoding("voltage")))
    with pytest.raises(BundleError, match="one panel"):
        figure.to_plotly()


def test_missing_plotly_names_the_extra(monkeypatch):
    real_import = builtins.__import__

    def guarded(name, globals=None, locals=None, fromlist=(), level=0):
        if name.split(".", 1)[0] == "plotly":
            raise ModuleNotFoundError("simulated absence")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded)
    for key in list(sys.modules):
        if key == "plotly" or key.startswith("plotly."):
            monkeypatch.delitem(sys.modules, key)

    with pytest.raises(ImportError, match=r"cellpy-figure\[plotly\]"):
        _figure().to_plotly()
