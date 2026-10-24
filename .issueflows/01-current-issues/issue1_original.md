# Issue #1: Write and read a .cfz bundle

Source: https://github.com/cellpy/cellpy-figure/issues/1

## Original issue text

Figure.write and open_figure still raise NotImplementedError, so neither cellpy nor the GUI can hand a coauthor a file. PLAN.md is the contract. This is step 1 of the suggested order (steps 2–6 are separate issues).

## Spec

- Implement `Figure.write` and `open_figure` for format_version 1.
- A `.cfz` is a zip with exactly `manifest.json`, `figure.json`, `data.parquet`, and `README.txt`.
- `manifest.json` carries `format` (`cellpy-figure`), `format_version` (1), and `created` (UTC timestamp).
- `figure.json` carries `title`, `panels`, `provenance`, and `extensions`. Each panel has `x` and `y`, plus optional `color`, `stroke`, and `facet`. Encodings use the fields already on `Encoding`.
- `data.parquet` is one table for the whole figure. Accept a pandas frame, or a polars frame converted on the way in. Polars is not a dependency. `open_figure` returns pandas.
- Provenance (`producer`, `producer_version`) is required to write. Optional `note` and `source` round-trip.
- Every encoding `field` must name a column. A missing column is an error that names the column and the panel.
- Unknown keys anywhere except inside `extensions` are an error that names the key. `extensions` round-trips and is not interpreted.
- A `format_version` this package does not implement raises, and the message includes the file's version and the version this package reads. The writer emits only version 1.
- `README.txt` starts with `pip install "cellpy-figure[mpl]"` and a short open-and-save script.
- Opening a bundle does not import matplotlib or Plotly.

## Acceptance criteria

- A round-trip test writes a zip, opens it, and matches the table and the spec (columns, labels, units, color type, stroke scale, facet, provenance, title).
- A missing column, an unknown key, and a newer `format_version` each raise an error that names the problem.
- `extensions` content survives a round-trip.
- The scaffold test no longer expects `NotImplementedError` from write/open. Renderers still do.

## Out of scope

- `to_matplotlib`, `to_plotly`, and journal preset style mappings.
- `schema/figure-1.json` and the wheel assertion.
- PyPI publishing.
- Any cellpy or GUI change.
