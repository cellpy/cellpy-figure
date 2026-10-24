"""One-panel matplotlib drawing. No pixel snapshots."""

import builtins
import os
import sys

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from cellpy_figure import BundleError, Encoding, Figure, Panel, Provenance

_MM = 25.4


def _close(fig):
    plt.close(fig)


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


def _drawn_linestyle(name: str) -> str:
    from matplotlib.lines import Line2D

    return Line2D([0], [0], linestyle=name).get_linestyle()


def test_nominal_color_and_stroke_scale():
    fig = _figure().to_matplotlib()
    try:
        ax = fig.axes[0]
        assert len(ax.lines) == 4
        by_label = {line.get_label(): line for line in ax.lines}
        assert set(by_label) == {
            "1, charge",
            "1, discharge",
            "2, charge",
            "2, discharge",
        }
        assert by_label["1, charge"].get_linestyle() == _drawn_linestyle("solid")
        assert by_label["1, discharge"].get_linestyle() == _drawn_linestyle("dashed")
        assert by_label["2, charge"].get_linestyle() == _drawn_linestyle("solid")
        assert by_label["1, charge"].get_color() == by_label["1, discharge"].get_color()
        assert by_label["1, charge"].get_color() != by_label["2, charge"].get_color()
        assert ax.get_xlabel() == "Capacity (mAh/g)"
        assert ax.get_ylabel() == "Voltage (V)"
    finally:
        _close(fig)


def test_nominal_color_is_one_series_per_category():
    fig = _figure(with_stroke=False).to_matplotlib()
    try:
        assert len(fig.axes[0].lines) == 2
        assert {line.get_label() for line in fig.axes[0].lines} == {"1", "2"}
    finally:
        _close(fig)


def test_quantitative_color_stays_sequential_across_presets():
    cycles = [1, 1, 2, 2, 3, 3, 4, 4]
    for preset in ("notebook", "acs-single"):
        fig = _figure(color_type="quantitative", cycles=cycles).to_matplotlib(
            preset=preset
        )
        try:
            ax = fig.axes[0]
            assert len(ax.lines) == 0
            assert len(ax.collections) == 2
            assert {col.get_cmap().name for col in ax.collections} == {"viridis"}
        finally:
            _close(fig)


def test_journal_preset_sets_size_and_font():
    fig = _figure(with_stroke=False).to_matplotlib(preset="acs-single")
    try:
        width, height = fig.get_size_inches()
        assert width == pytest.approx(82.5 / _MM)
        assert height == pytest.approx(60 / _MM)
        assert fig.axes[0].xaxis.label.get_fontsize() == 8
    finally:
        _close(fig)
    fig = _figure(with_stroke=False).to_matplotlib(preset="acs-single", width_mm=120)
    try:
        assert fig.get_size_inches()[0] == pytest.approx(120 / _MM)
    finally:
        _close(fig)


def test_facet_and_extra_panels_are_refused():
    figure = _figure()
    figure.panels[0].facet = Encoding("cycle")
    with pytest.raises(BundleError, match="facet"):
        figure.to_matplotlib()
    figure = _figure()
    figure.panels.append(Panel(x=Encoding("capacity"), y=Encoding("voltage")))
    with pytest.raises(BundleError, match="one panel"):
        figure.to_matplotlib()


def test_missing_matplotlib_names_the_extra(monkeypatch):
    real_import = builtins.__import__

    def guarded(name, globals=None, locals=None, fromlist=(), level=0):
        if name.split(".", 1)[0] == "matplotlib":
            raise ModuleNotFoundError("simulated absence")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded)
    for key in list(sys.modules):
        if key == "matplotlib" or key.startswith("matplotlib."):
            monkeypatch.delitem(sys.modules, key)

    with pytest.raises(ImportError, match=r"cellpy-figure\[mpl\]"):
        _figure().to_matplotlib()
