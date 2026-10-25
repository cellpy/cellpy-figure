"""The format-version 1 schema matches what Figure.write emits."""

import json
import subprocess
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from cellpy_figure import Encoding, Figure, Panel, Provenance
from cellpy_figure.schema import load_schema

ROOT = Path(__file__).resolve().parents[1]


def _figure() -> Figure:
    frame = pd.DataFrame(
        {
            "capacity": [1.0, 2.0],
            "voltage": [3.0, 4.0],
            "cycle": [1, 2],
            "direction": ["charge", "discharge"],
            "variable": ["capacity", "ce"],
        }
    )
    return Figure(
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
        provenance=Provenance("cellpy", "2.1.3", note="Plotted rows only."),
        extensions={"cellpy": {"family": "cycles"}},
    )


def _members(path: Path) -> tuple[dict, dict]:
    with ZipFile(path) as archive:
        figure = json.loads(archive.read("figure.json"))
        manifest = json.loads(archive.read("manifest.json"))
    return figure, manifest


def test_written_figure_and_manifest_validate(tmp_path):
    path = tmp_path / "figure.cfz"
    _figure().write(str(path))
    figure, manifest = _members(path)
    schema = load_schema()
    Draft202012Validator(schema).validate(figure)
    Draft202012Validator(schema["$defs"]["manifest"]).validate(manifest)
    assert "facet" in figure["panels"][0]


def test_unknown_key_names_the_key(tmp_path):
    path = tmp_path / "figure.cfz"
    _figure().write(str(path))
    figure, _manifest = _members(path)
    figure["nope"] = 1
    with pytest.raises(ValidationError, match="nope"):
        Draft202012Validator(load_schema()).validate(figure)


def test_schema_is_in_the_wheel(tmp_path):
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(tmp_path)],
        cwd=ROOT,
        check=True,
    )
    wheels = list(tmp_path.glob("*.whl"))
    assert len(wheels) == 1
    with ZipFile(wheels[0]) as archive:
        assert "cellpy_figure/schema/figure-1.json" in archive.namelist()
