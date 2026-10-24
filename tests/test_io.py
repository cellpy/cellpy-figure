"""Round-trip and rejection tests for .cfz bundles."""

import json
import logging
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
import pandas.testing as pdt
import pytest

from cellpy_figure import BundleError, Encoding, Figure, Panel, Provenance, open_figure
from cellpy_figure.io import README_TEXT

ROOT = Path(__file__).resolve().parents[1]


def _figure(**overrides) -> Figure:
    frame = pd.DataFrame(
        {
            "capacity": [1.0, 2.0, 1.5],
            "voltage": [3.0, 4.0, 3.5],
            "cycle": [1, 1, 2],
            "direction": ["charge", "discharge", "charge"],
            "variable": ["capacity", "capacity", "ce"],
        }
    )
    figure = Figure(
        data=frame,
        panels=[
            Panel(
                x=Encoding("capacity", label="Capacity", unit="mAh/g"),
                y=Encoding("voltage", label="Voltage", unit="V"),
                color=Encoding("cycle", type="nominal", legend_title="Cycle"),
                stroke=Encoding(
                    "direction",
                    scale={"charge": "solid", "discharge": "dashed"},
                ),
                facet=Encoding("variable", label="Variable"),
            )
        ],
        title="Charge-Discharge Curves",
        provenance=Provenance(
            "cellpy",
            "2.1.3",
            note="Plotted rows only.",
            source="synthetic",
        ),
        extensions={"cellpy": {"family": "cycles", "keep": True}},
    )
    for key, value in overrides.items():
        setattr(figure, key, value)
    return figure


def _rewrite(path: Path, name: str, mutate) -> None:
    with ZipFile(path) as archive:
        items = {item: archive.read(item) for item in archive.namelist()}
    items[name] = mutate(items[name])
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        for item, payload in items.items():
            archive.writestr(item, payload)


def _assert_same_figure(found: Figure, expected: Figure) -> None:
    pdt.assert_frame_equal(found.data, expected.data)
    assert found.panels == expected.panels
    assert found.title == expected.title
    assert found.provenance == expected.provenance
    assert found.extensions == expected.extensions


def test_round_trip_matches_table_and_spec(tmp_path):
    original = _figure()
    path = tmp_path / "figure.cfz"
    original.write(str(path))

    with ZipFile(path) as archive:
        assert archive.namelist() == [
            "manifest.json",
            "figure.json",
            "data.parquet",
            "README.txt",
        ]
        manifest = json.loads(archive.read("manifest.json"))
        readme = archive.read("README.txt").decode()

    assert manifest["format"] == "cellpy-figure"
    assert manifest["format_version"] == 1
    assert manifest["created"].endswith("Z")
    assert readme == README_TEXT
    assert readme.startswith('pip install "cellpy-figure[mpl]"')

    opened = open_figure(str(path))
    _assert_same_figure(opened, original)


def test_extensions_round_trip_and_are_not_interpreted(tmp_path, caplog):
    caplog.set_level(logging.DEBUG, logger="cellpy_figure")
    path = tmp_path / "figure.cfz"
    _figure().write(str(path))
    opened = open_figure(str(path))
    assert opened.extensions == {"cellpy": {"family": "cycles", "keep": True}}
    assert "not interpreted" in caplog.text


def test_polars_frame_is_converted(tmp_path):
    frame = _figure().data

    class DataFrame:
        def to_pandas(self):
            return frame

    DataFrame.__module__ = "polars"
    figure = _figure(data=DataFrame())
    path = tmp_path / "figure.cfz"
    figure.write(str(path))
    opened = open_figure(str(path))
    pdt.assert_frame_equal(opened.data, frame)


def test_missing_column_names_the_panel(tmp_path):
    figure = _figure()
    figure.panels[0].color = Encoding("missing", type="nominal")
    path = tmp_path / "figure.cfz"
    with pytest.raises(BundleError, match="panel 1 color.*'missing'"):
        figure.write(str(path))


def test_second_panel_is_numbered():
    figure = _figure()
    figure.panels.append(
        Panel(
            x=Encoding("capacity"),
            y=Encoding("not_a_column"),
        )
    )
    with pytest.raises(BundleError, match="panel 2 y"):
        figure.write("unused.cfz")


def test_unknown_key_names_the_key(tmp_path):
    path = tmp_path / "figure.cfz"
    _figure().write(str(path))

    def add_panel_key(raw: bytes) -> bytes:
        spec = json.loads(raw)
        spec["panels"][0]["kind"] = "cycles"
        return json.dumps(spec).encode()

    _rewrite(path, "figure.json", add_panel_key)
    with pytest.raises(BundleError, match="unknown key 'kind'"):
        open_figure(str(path))


def test_unknown_key_inside_extensions_is_kept(tmp_path):
    path = tmp_path / "figure.cfz"
    figure = _figure()
    figure.extensions = {"cellpy": {"not_a_spec_key": 1}}
    figure.write(str(path))
    assert open_figure(str(path)).extensions == {"cellpy": {"not_a_spec_key": 1}}


def test_newer_format_version_names_both_versions(tmp_path):
    path = tmp_path / "figure.cfz"
    _figure().write(str(path))

    def bump(raw: bytes) -> bytes:
        manifest = json.loads(raw)
        manifest["format_version"] = 2
        return json.dumps(manifest).encode()

    _rewrite(path, "manifest.json", bump)
    with pytest.raises(BundleError, match=r"format_version 2.*format_version 1"):
        open_figure(str(path))


def test_non_frame_is_rejected():
    figure = _figure(data=[{"capacity": 1.0}])
    with pytest.raises(BundleError, match="pandas.DataFrame or a polars.DataFrame"):
        figure.write("unused.cfz")


def test_provenance_is_required():
    figure = _figure(provenance=None)
    with pytest.raises(BundleError, match="provenance is required"):
        figure.write("unused.cfz")


def test_open_does_not_import_renderers(tmp_path):
    path = tmp_path / "figure.cfz"
    _figure().write(str(path))
    code = """
import sys
import cellpy_figure
cellpy_figure.open_figure(sys.argv[1])
banned = [name for name in ("matplotlib", "plotly") if name in sys.modules]
if banned:
    raise SystemExit("imported " + ", ".join(banned))
"""
    completed = subprocess.run(
        ["uv", "run", "python", "-c", code, str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
