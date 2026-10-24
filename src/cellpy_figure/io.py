"""Read and write a ``.cfz`` bundle.

A bundle is a zip with ``manifest.json``, ``figure.json``, ``data.parquet``,
and ``README.txt``. The schema is format version 1, as specified in
``PLAN.md``. Rendering is not part of this module.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile, is_zipfile

import pandas as pd

from cellpy_figure.model import Encoding, Figure, Panel, Provenance

log = logging.getLogger("cellpy_figure")

FORMAT_NAME = "cellpy-figure"
FORMAT_VERSION = 1
SUPPORTED_FORMAT_VERSIONS = frozenset({FORMAT_VERSION})

_MEMBERS = ("manifest.json", "figure.json", "data.parquet", "README.txt")
_MANIFEST_KEYS = frozenset({"format", "format_version", "created"})
_FIGURE_KEYS = frozenset({"title", "panels", "provenance", "extensions"})
_PANEL_KEYS = frozenset({"x", "y", "color", "stroke", "facet"})
_ENCODING_KEYS = frozenset({"field", "label", "unit", "type", "legend_title", "scale"})
_PROVENANCE_KEYS = frozenset({"producer", "producer_version", "note", "source"})
_COLOR_TYPES = frozenset({"nominal", "quantitative"})
_OPTIONAL_CHANNELS = ("color", "stroke", "facet")

README_TEXT = """\
pip install "cellpy-figure[mpl]"

This file is a cellpy-figure bundle. It holds the plotted table and the
encodings that drew it, not a frozen image.

import cellpy_figure

figure = cellpy_figure.open_figure("figure.cfz")
drawn = figure.to_matplotlib(preset="notebook")
drawn.savefig("figure.pdf")
"""


class BundleError(ValueError):
    """A ``.cfz`` bundle cannot be written or read."""


def write_figure(figure: Figure, path: str) -> None:
    """Write ``figure`` to a ``.cfz`` bundle at ``path``.

    Args:
        figure: Figure to store. ``data`` is a pandas or polars frame.
            ``provenance`` is required.
        path: Destination path. An existing file is replaced.

    Raises:
        BundleError: The figure is not a valid format-version-1 bundle, or
            the path cannot be written.
    """
    if FORMAT_VERSION not in SUPPORTED_FORMAT_VERSIONS:
        supported = ", ".join(str(v) for v in sorted(SUPPORTED_FORMAT_VERSIONS))
        raise BundleError(
            f"refusing to write format_version {FORMAT_VERSION}; "
            f"this package writes format_version {supported}."
        )
    frame = _as_pandas(figure.data)
    if not figure.panels:
        raise BundleError("a figure needs at least one panel.")
    _check_columns(frame, figure.panels)
    spec = _figure_to_json(figure)
    manifest = {
        "format": FORMAT_NAME,
        "format_version": FORMAT_VERSION,
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    table = BytesIO()
    try:
        frame.to_parquet(table, index=False, engine="pyarrow")
    except Exception as exc:
        raise BundleError(f"could not write data.parquet ({exc}).") from exc
    try:
        with ZipFile(Path(path), "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", _dumps(manifest))
            archive.writestr("figure.json", _dumps(spec))
            archive.writestr("data.parquet", table.getvalue())
            archive.writestr("README.txt", README_TEXT)
    except OSError as exc:
        raise BundleError(f"could not write {path} ({exc}).") from exc


def open_figure(path: str) -> Figure:
    """Open a ``.cfz`` bundle.

    Args:
        path: Path to the bundle.

    Returns:
        The figure, with ``data`` as a ``pandas.DataFrame``. The table index
        is not stored.

    Raises:
        BundleError: The file is missing, not a format-version-1 bundle, or
            disagrees with its table.
    """
    location = Path(path)
    if not location.is_file():
        raise BundleError(f"no such bundle: {path}")
    if not is_zipfile(location):
        raise BundleError(f"not a .cfz bundle (not a zip): {path}")
    with ZipFile(location) as archive:
        names = archive.namelist()
        _check_members(names)
        manifest = _load_json(archive, "manifest.json")
        _check_manifest(manifest)
        spec = _load_json(archive, "figure.json")
        figure = _figure_from_json(spec)
        try:
            figure.data = pd.read_parquet(
                BytesIO(archive.read("data.parquet")), engine="pyarrow"
            )
        except Exception as exc:
            raise BundleError(f"data.parquet could not be read ({exc}).") from exc
    _check_columns(figure.data, figure.panels)
    if figure.extensions:
        log.debug("opened a bundle with extensions; contents are not interpreted")
    return figure


def _dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def _check_members(names: list[str]) -> None:
    if len(names) != len(set(names)):
        raise BundleError("bundle contains duplicate members.")
    missing = [name for name in _MEMBERS if name not in names]
    extra = [name for name in names if name not in _MEMBERS]
    if missing:
        raise BundleError(f"bundle is missing {', '.join(missing)}.")
    if extra:
        unexpected = ", ".join(repr(name) for name in extra)
        expected = ", ".join(_MEMBERS)
        raise BundleError(
            f"bundle contains unexpected member {unexpected}. Expected {expected}."
        )


def _load_json(archive: ZipFile, name: str) -> dict[str, Any]:
    try:
        text = archive.read(name).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BundleError(f"{name} is not UTF-8.") from exc
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise BundleError(f"{name} is not valid JSON ({exc}).") from exc
    if not isinstance(payload, dict):
        raise BundleError(f"{name} must be a JSON object.")
    return payload


def _check_manifest(manifest: dict[str, Any]) -> None:
    _reject_unknown(manifest, _MANIFEST_KEYS, "manifest.json")
    if manifest.get("format") != FORMAT_NAME:
        raise BundleError(
            f"manifest format is {manifest.get('format')!r}; expected {FORMAT_NAME!r}."
        )
    if "format_version" not in manifest:
        raise BundleError(
            "manifest.json is missing format_version; "
            f"cellpy-figure reads format_version {FORMAT_VERSION}."
        )
    found = manifest["format_version"]
    if isinstance(found, bool) or not isinstance(found, int):
        raise BundleError(
            f"this file uses format_version {found!r}; "
            f"cellpy-figure reads format_version {FORMAT_VERSION}."
        )
    if found not in SUPPORTED_FORMAT_VERSIONS:
        raise BundleError(
            f"this file uses format_version {found}; "
            f"cellpy-figure reads format_version {FORMAT_VERSION}."
        )
    created = manifest.get("created")
    if not isinstance(created, str) or not created:
        raise BundleError("manifest.json created must be a UTC timestamp string.")


def _as_pandas(data: Any) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        frame = data
    else:
        module = type(data).__module__.split(".", 1)[0]
        to_pandas = getattr(data, "to_pandas", None)
        if module == "polars" and callable(to_pandas):
            frame = to_pandas()
            if not isinstance(frame, pd.DataFrame):
                raise BundleError(
                    "polars to_pandas() did not return a pandas.DataFrame."
                )
        else:
            raise BundleError(
                "figure data must be a pandas.DataFrame or a polars.DataFrame; "
                f"got {type(data).__module__}.{type(data).__name__}."
            )
    if not all(isinstance(column, str) for column in frame.columns):
        raise BundleError("column names must be strings.")
    return frame


def _check_columns(frame: pd.DataFrame, panels: list[Panel]) -> None:
    columns = set(frame.columns)
    listed = ", ".join(frame.columns) or "none"
    for index, panel in enumerate(panels, start=1):
        channels: list[tuple[str, Encoding | None]] = [
            ("x", panel.x),
            ("y", panel.y),
            ("color", panel.color),
            ("stroke", panel.stroke),
            ("facet", panel.facet),
        ]
        for name, encoding in channels:
            if encoding is None:
                continue
            if encoding.field not in columns:
                raise BundleError(
                    f"panel {index} {name} names column {encoding.field!r}, "
                    f"which is not in the table (columns: {listed})."
                )


def _figure_to_json(figure: Figure) -> dict[str, Any]:
    if figure.provenance is None:
        raise BundleError(
            "provenance is required to write a bundle; set producer and producer_version."
        )
    if not isinstance(figure.extensions, dict):
        raise BundleError("extensions must be a JSON object.")
    try:
        json.dumps(figure.extensions)
    except TypeError as exc:
        raise BundleError(f"extensions must be JSON-serializable ({exc}).") from exc
    spec: dict[str, Any] = {}
    if figure.title is not None:
        if not isinstance(figure.title, str):
            raise BundleError("title must be a string.")
        spec["title"] = figure.title
    spec["panels"] = [
        _panel_to_json(panel, index)
        for index, panel in enumerate(figure.panels, start=1)
    ]
    spec["provenance"] = _provenance_to_json(figure.provenance)
    spec["extensions"] = figure.extensions
    return spec


def _panel_to_json(panel: Panel, index: int) -> dict[str, Any]:
    raw: dict[str, Any] = {
        "x": _encoding_to_json(panel.x, index, "x"),
        "y": _encoding_to_json(panel.y, index, "y"),
    }
    for name in _OPTIONAL_CHANNELS:
        encoding = getattr(panel, name)
        if encoding is not None:
            raw[name] = _encoding_to_json(encoding, index, name)
    return raw


def _encoding_to_json(encoding: Encoding, index: int, channel: str) -> dict[str, Any]:
    where = f"panel {index} {channel}"
    if not isinstance(encoding, Encoding):
        raise BundleError(f"{where} must be an Encoding.")
    if not isinstance(encoding.field, str) or not encoding.field:
        raise BundleError(f"{where} field must be a column name.")
    raw: dict[str, Any] = {"field": encoding.field}
    for attr in ("label", "unit", "legend_title"):
        value = getattr(encoding, attr)
        if value is None:
            continue
        if not isinstance(value, str):
            raise BundleError(f"{where} {attr} must be a string.")
        raw[attr] = value
    if encoding.type is not None:
        if encoding.type not in _COLOR_TYPES:
            raise BundleError(
                f"{where} type is {encoding.type!r}; expected nominal or quantitative."
            )
        raw["type"] = encoding.type
    if encoding.scale is not None:
        raw["scale"] = _scale_to_json(encoding.scale, where)
    return raw


def _scale_to_json(scale: dict[str, str], where: str) -> dict[str, str]:
    if not isinstance(scale, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in scale.items()
    ):
        raise BundleError(f"{where} scale must map strings to strings.")
    return dict(scale)


def _provenance_to_json(provenance: Provenance) -> dict[str, Any]:
    raw: dict[str, Any] = {
        "producer": _required_string(provenance.producer, "provenance.producer"),
        "producer_version": _required_string(
            provenance.producer_version, "provenance.producer_version"
        ),
    }
    for attr in ("note", "source"):
        value = _optional_string(getattr(provenance, attr), f"provenance.{attr}")
        if value is not None:
            raw[attr] = value
    return raw


def _required_string(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise BundleError(f"{where} must be a non-empty string.")
    return value


def _optional_string(value: Any, where: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise BundleError(f"{where} must be a string.")
    return value


def _figure_from_json(spec: dict[str, Any]) -> Figure:
    _reject_unknown(spec, _FIGURE_KEYS, "figure.json")
    if "panels" not in spec:
        raise BundleError("figure.json is missing panels.")
    if not isinstance(spec["panels"], list) or not spec["panels"]:
        raise BundleError("a figure needs at least one panel.")
    if "provenance" not in spec:
        raise BundleError("figure.json is missing provenance.")
    title = spec.get("title")
    if title is not None and not isinstance(title, str):
        raise BundleError("title must be a string.")
    if "extensions" in spec and not isinstance(spec["extensions"], dict):
        raise BundleError("extensions must be a JSON object.")
    return Figure(
        data=None,
        panels=[
            _panel_from_json(panel, index)
            for index, panel in enumerate(spec["panels"], start=1)
        ],
        title=title,
        provenance=_provenance_from_json(spec["provenance"]),
        extensions=spec.get("extensions", {}),
    )


def _panel_from_json(raw: Any, index: int) -> Panel:
    where = f"panel {index}"
    if not isinstance(raw, dict):
        raise BundleError(f"{where} must be a JSON object.")
    _reject_unknown(raw, _PANEL_KEYS, where)
    for channel in ("x", "y"):
        if channel not in raw:
            raise BundleError(f"{where} is missing {channel}.")
    return Panel(
        x=_encoding_from_json(raw["x"], index, "x"),
        y=_encoding_from_json(raw["y"], index, "y"),
        color=_optional_encoding(raw, index, "color"),
        stroke=_optional_encoding(raw, index, "stroke"),
        facet=_optional_encoding(raw, index, "facet"),
    )


def _optional_encoding(
    raw: dict[str, Any], index: int, channel: str
) -> Encoding | None:
    if channel not in raw:
        return None
    return _encoding_from_json(raw[channel], index, channel)


def _encoding_from_json(raw: Any, index: int, channel: str) -> Encoding:
    where = f"panel {index} {channel}"
    if not isinstance(raw, dict):
        raise BundleError(f"{where} must be a JSON object.")
    _reject_unknown(raw, _ENCODING_KEYS, where)
    if "field" not in raw:
        raise BundleError(f"{where} is missing field.")
    field = raw["field"]
    if not isinstance(field, str) or not field:
        raise BundleError(f"{where} field must be a column name.")
    encoding_type = raw.get("type")
    if encoding_type is not None and encoding_type not in _COLOR_TYPES:
        raise BundleError(
            f"{where} type is {encoding_type!r}; expected nominal or quantitative."
        )
    scale = raw.get("scale")
    if scale is not None:
        scale = _scale_to_json(scale, where)
    for attr in ("label", "unit", "legend_title"):
        if attr in raw and not isinstance(raw[attr], str):
            raise BundleError(f"{where} {attr} must be a string.")
    return Encoding(
        field=field,
        label=raw.get("label"),
        unit=raw.get("unit"),
        type=encoding_type,
        legend_title=raw.get("legend_title"),
        scale=scale,
    )


def _provenance_from_json(raw: Any) -> Provenance:
    if not isinstance(raw, dict):
        raise BundleError("provenance must be a JSON object.")
    _reject_unknown(raw, _PROVENANCE_KEYS, "provenance")
    for key in ("producer", "producer_version"):
        if key not in raw:
            raise BundleError(f"provenance is missing {key}.")
    return Provenance(
        producer=_required_string(raw["producer"], "provenance.producer"),
        producer_version=_required_string(
            raw["producer_version"], "provenance.producer_version"
        ),
        note=_optional_string(raw.get("note"), "provenance.note"),
        source=_optional_string(raw.get("source"), "provenance.source"),
    )


def _reject_unknown(
    payload: dict[str, Any], allowed: frozenset[str], where: str
) -> None:
    extra = sorted(set(payload) - allowed)
    if not extra:
        return
    found = ", ".join(repr(key) for key in extra)
    known = ", ".join(sorted(allowed))
    label = "key" if len(extra) == 1 else "keys"
    raise BundleError(
        f"{where} has unknown {label} {found}. Known keys: {known}. "
        "Other producer data belongs in extensions."
    )
