# cellpy-figure — guiding plan

Status: **design, not implemented.** This file is the contract for the first
version. Change it when a decision changes; do not let the code drift ahead of
it.

The package on PyPI will be `cellpy-figure`. The import name will be
`cellpy_figure`. The on-disk figure is a zip with the extension `.cfz`.

## The problem

A person builds a figure they are happy with in cellpy or in
[cellpy-simple-gui](https://github.com/cellpy/cellpy-simple-gui): the right
cells, cycles, capacity basis, and charge/discharge layout. They then want to
change it for a publication — fonts, column width, line width, axis limits,
which cycles survive, categorical colours versus a sequential colormap — and
hand the result to a coauthor.

Today that handoff does not exist.

- PNG, SVG, and PDF from the GUI are a frozen Plotly render. A vector file can
  be nudged in a drawing program. Dropping a cycle or changing the typeface
  means drawing the figure again.
- CSV, Excel, Parquet, and JSON from the GUI are the tidy numbers, without the
  choices that turned those numbers into a figure.
- Plotly's own JSON contains both, and it does not open as a matplotlib
  figure. Translating Plotly traces into matplotlib artists is lossy, and it
  is not a path we will build.
- cellpy already splits drawing into `prepare` → `(tidy frame, FigureSpec)` →
  a backend. That pair lives only in memory. `FigureSpec` is panels, axis
  labels, and a title. It is a cellpy object, not a file a coauthor can open.

## Who this is for

The reader of a `.cfz` file is a coauthor who will never install cellpy. They
have Python, and they want either a matplotlib `Figure` or a Plotly `Figure`,
plus the table that was plotted, so they can still call `set_xlim` or drop a
row and redraw.

The writers are cellpy and cellpy-simple-gui. Both already know how to build
the tidy frame. This package does not load raw tester files, does not know
what a cycle is, and does not depend on either project.

## What this library is

Three responsibilities:

1. The schema of a figure file.
2. Reading and writing that file.
3. Rendering it with matplotlib and with Plotly.

Battery words — cycle, gravimetric, forth-and-forth, plot family — stay in
the column names, axis labels, units, and explicit scales that the writer
put in the file. The library sees fields, encodings, and scales.

```text
coauthor notebook
    └── cellpy-figure          read, render

cellpy
    └── cellpy-figure          write (via a translator that lives in cellpy)

cellpy-simple-gui
    └── cellpy                 the common path
    └── cellpy-figure          only when the GUI has a view cellpy cannot
                               express yet (see below)
```

Dependencies point one way. `cellpy_figure` imports neither `cellpy` nor
`cellpy_simple_gui`.

## What this library is not

- A third plotting library. Matplotlib and Plotly draw. This package maps a
  small grammar onto them.
- A grammar of graphics. Vega-Lite and Altair already are that, and they do
  not hand back a matplotlib `Figure` with journal `rcParams`. That is the
  tweak this format exists to allow.
- A place for cellpy's prepare pipeline, unit registry, or plot-family
  registry. Those stay in cellpy. This package receives an already tidy table.
- A round-trip of a Plotly figure. The source of truth is the table plus the
  spec, not the traces a particular renderer emitted.
- A data archive. The table is the rows that were plotted (after cycle
  filters and point thinning), not the tester file and not the full
  `.cellpy` file. Provenance says so.

## Three artefacts, and which one this is

| Artefact | Contains | Lives where |
|---|---|---|
| Recipe | GUI or library choices, no rows | cellpy / the GUI, if they want "draw this again" from the original files |
| Figure bundle (`.cfz`) | Plotted rows, spec, provenance | **this package** |
| Frozen render | SVG, PDF, PNG, or Plotly JSON | cellpy's existing image export; unchanged |

A recipe is useful while the `.cellpy` files are still at hand. It is not a
substitute for the bundle: the coauthor does not have those files, and should
not need them.

## File format

A `.cfz` file is a zip:

```text
manifest.json     format version, created time
figure.json       spec, no rows
data.parquet      one long table for the whole figure
README.txt        how to open the file, including the pip install line
```

One table, not one file per panel. A summary figure with several panels is a
long table with a column that names the panel (cellpy's collected frames
already look like this: one row per cell, cycle, and variable). The spec
points at that column.

`README.txt` is inside the zip on purpose. The file will arrive as an email
attachment. The first thing in it is:

```text
pip install "cellpy-figure[mpl]"
```

and a six-line script that opens the bundle and saves a PDF.

### `manifest.json`

```json
{
  "format": "cellpy-figure",
  "format_version": 1,
  "created": "2026-10-03T18:00:00Z"
}
```

`format_version` is the schema, not the package version. A reader that does
not know the number raises, and the message includes both versions. A writer
refuses to emit a version newer than it implements.

### `figure.json`

A panel list plus provenance. Illustrative, not the final field-by-field
schema (that lands in `schema/figure-1.json` when the models do):

```json
{
  "title": "Charge-Discharge Curves",
  "panels": [
    {
      "x": {"field": "capacity", "label": "Capacity", "unit": "mAh/g"},
      "y": {"field": "voltage", "label": "Voltage", "unit": "V"},
      "color": {
        "field": "cycle",
        "type": "nominal",
        "legend_title": "Cycle"
      },
      "stroke": {
        "field": "direction",
        "scale": {"charge": "solid", "discharge": "dashed"}
      }
    }
  ],
  "provenance": {
    "producer": "cellpy",
    "producer_version": "2.1.3",
    "note": "Plotted rows only, after cycle filter and interpolation."
  },
  "extensions": {}
}
```

Rules:

- Every encoding names a column in `data.parquet`. A missing column is an
  error that names the column and the panel.
- Scales are explicit. "Charge is a solid line" is in the file, so the reader
  does not contain a battery convention.
- `color.type` is `nominal` or `quantitative`. Nominal is the categorical
  legend (one colour per cycle number, as in a typical GUI export).
  Quantitative is a sequential colormap, which is what a fade figure usually
  wants. That choice is scientific, so it is stored. The preset does not
  override it.
- Font, figure width in millimetres, spine style, and grid are presets. They
  are not stored. The file may carry an optional size hint
  (`width_mm`, `height_mm`); a named preset replaces it when the caller asks
  for that preset.
- `extensions` is producer-specific and the reader ignores its contents.
  cellpy may stash the original family name or the GUI spec here so a later
  cellpy can round-trip. Unknown keys anywhere else, including inside a
  panel, are an error.
- Units are strings for axis labels (`mAh/g`, `V`). This package does not
  convert them.

A multi-panel summary uses either several entries in `panels` that share the
table, or one panel with a facet encoding whose field is the variable column.
Prefer the facet encoding when the panels share x and differ only in y: that
matches the long collected frame cellpy already builds. Use several panel
entries when the panels do not share an x column (rare in v1).

### Provenance

Required: `producer` (a short name: `cellpy`, `cellpy-simple-gui`) and
`producer_version`. Optional: `note`, `source` (path or hash of the file the
writer read). The note must say when the table is a thinned or filtered
sample. The bundle does not pretend to be the tester file.

## Public API

```python
from cellpy_figure import Figure, Panel, open_figure

figure = Figure(
    data=df,  # pandas.DataFrame or polars.DataFrame; stored as parquet
    panels=[Panel(...)],
    title="Charge-Discharge Curves",
    provenance=...,
)
figure.write("six031_07.cfz")

figure = open_figure("six031_07.cfz")
figure.data  # pandas.DataFrame
mpl = figure.to_matplotlib(preset="acs-single")
mpl.savefig("fig2.pdf")
figure.to_plotly(preset="acs-single")
```

`to_matplotlib` returns a real `matplotlib.figure.Figure`. Further edits
(`set_xlim`, a panel letter, `savefig`) are the caller's, in matplotlib, not
new methods on `Figure`.

`to_plotly` returns a `plotly.graph_objects.Figure`.

Both accept `preset=` and a small set of overrides (`width_mm`, `height_mm`).
They do not accept a free-form matplotlib `rcParams` dict or a Plotly layout
dict as the way to style a figure. Those belong in `presets.py`, so a journal
style has one name and both renderers honour it as far as each renderer can.

### Presets

Ship a few, as data in `presets.py`, not as classes:

| Name | Intent |
|---|---|
| `notebook` | Default. Readable on screen. |
| `acs-single` | Single ACS column. |
| `nature-single` | Single Nature column. |

A preset is a matplotlib `rcParams` mapping plus a Plotly layout mapping plus
a size in millimetres. Adding a journal is a dictionary, not a renderer
change.

### Dependencies

Runtime, always installed:

- `pandas` — `Figure.data` is a pandas frame, because that is what a coauthor
  already knows how to filter.
- `pyarrow` — read and write the parquet member.

Writers may pass a polars frame; the package converts it on the way into the
zip. Polars is not a dependency.

Optional extras:

| Extra | Installs | Provides |
|---|---|---|
| `mpl` | matplotlib | `to_matplotlib` |
| `plotly` | plotly | `to_plotly` |

Calling a renderer without its extra raises an error that names the extra
(`pip install "cellpy-figure[mpl]"`). Opening a bundle and inspecting
`.data` never imports matplotlib or Plotly.

Python floor: **3.13**, matching cellpy, cellpy-core, and cellpy-simple-gui.
Lowering it is a deliberate change to this plan, made only if a real coauthor
is stuck on an older interpreter. Do not add a version matrix "just in case."

## What version 1 draws

Figures that can be stated as: one long table, one or more panels, x and y
fields, optional color, optional stroke with an explicit scale, optional row
or column facet.

That covers the charge–discharge overlay (capacity vs voltage, color by
cycle, stroke by direction), a summary life plot (cycle index vs a variable,
facet by variable, color by cell), and ICA / DVA curves (the same shape as
charge–discharge, different column names).

## What version 1 refuses

These stay GUI-only or cellpy-only until the spec grows an encoding that can
state them. Do not smuggle them in through `extensions` and a private
renderer branch.

- Density films (`histogram2d`).
- Step-number and step-type bands from `cycle_info_plot`.
- Plotly hover text, modebar state, and any other renderer chrome.
- Storing rewritten traces. Compare-overlay in the GUI is "one pair of axes,
  color by cell or by cycle" in the spec. The bundle stores the filtered
  rows, not the post-processed traces.

## Package layout

```text
cellpy-figure/
  PLAN.md                  this file
  README.md                short user page; points here and at the API
  HISTORY.md               user-facing changelog, updated in the release PR
  pyproject.toml
  uv.lock
  schema/
    figure-1.json          JSON Schema for the spec, for non-Python readers
  src/cellpy_figure/
    __init__.py            open_figure, Figure, Panel, __version__
    model.py               Figure, Panel, Encoding, Provenance
    io.py                  zip read/write
    presets.py
    mpl.py
    plotly.py
  tests/                   synthetic frames only; never import cellpy
  docs/                    added when the API is real enough to document
```

Two render modules, not a backend class hierarchy. A third renderer later is
another module plus an extra. No `kinds/` package and no plugin registry
until a figure truly cannot be stated as panels and encodings.

`schema/figure-1.json` is generated from the same models the reader uses, or
hand-written and checked against them in a test. It is the artefact a
non-Python tool can validate. The Python models remain the implementation.

## What cellpy is expected to do

cellpy owns the translation from its own objects into this schema. That
translator does not live in this repository.

Place it beside the existing prepare path:

```text
src/cellpy/plotting/bundle.py
```

It accepts the same `(frame, FigureSpec)` pair the backends already render,
fills labels and units from cellpy's unit helpers, and calls
`Figure.write`. Public wrappers stay thin: one function that takes a kind
(`cycles`, `summary`, `ica`, `dva`) plus the arguments the matching
`*_plot` function already takes, and a path.

```python
from cellpy.plotting.bundle import save_bundle

save_bundle(
    cell,
    kind="cycles",
    path="six031_07.cfz",
    cycles=[1, 2, 4, 5, 6, 7, 9, 10],
    mode="gravimetric",
)
```

Conventions the translator is responsible for, because they are battery
knowledge:

- Axis labels and unit strings (`Capacity` / `mAh/g`, `Voltage` / `V`).
- Mapping direction to a stroke scale: charge solid, discharge dashed, when
  both half-cycles are on one panel.
- Choosing `nominal` versus `quantitative` color. Default for a
  charge–discharge overlay: `quantitative` on the cycle column when the
  caller asked for a colormap, `nominal` when they asked for a legend of
  discrete cycles. Record the choice in the file.
- Writing `provenance.producer = "cellpy"` and the installed cellpy version.
- Writing a `note` when the frame was interpolated or thinned.
- Putting the plot-family name, when there is one, under `extensions.cellpy`.

cellpy gains `cellpy-figure` as a dependency of the extras that already mean
"I am plotting":

- `batch` (Plotly is already there)
- `plotting-mpl`

Do not add it to cellpy's required dependencies. A cellpy install that never
draws must not pull this package.

Pin an exact `cellpy-figure==X.Y.Z` before a cellpy release, the same way
cellpy pins `cellpycore`. Do not commit a `[tool.uv.sources]` path override
for local dual-repo work. That override breaks Dependabot lock updates. Local
development is `uv sync` and then an editable install of the sibling
checkout, and the lock is regenerated with `UV_NO_SOURCES=1`.

Tests in cellpy, one round-trip per kind that v1 claims (cycles, summary,
ICA): write a bundle to a temp directory, open it with `cellpy_figure`, and
assert column names, axis labels, and the stroke scale. Do not assert
pixels.

The GUI must be able to call this translator. If the only way to produce a
bundle is a private helper, the two writers will drift.

## What cellpy-simple-gui is expected to do

The export menu gains `cfz` next to png, svg, and pdf, on every figure that
v1 can express: cycle summary, voltage curves, dQ/dV, and dV/dQ.

The common path calls cellpy's `save_bundle` (or the collection it already
built, passed into the translator). The GUI does not grow a second mapping
from plot type to panels.

The exception is a view cellpy cannot express yet. Compare-overlay, which the
GUI builds by restyling facets after cellpy returns them, is the known case.
For that view the GUI constructs a `cellpy_figure.Figure` itself from the
tidy rows and writes the same schema. `provenance.producer` is
`cellpy-simple-gui`. A coauthor cannot tell the writers apart except by that
field, and should not need to.

Availability follows the same rule as the other figure formats: if the
`cellpy-figure` import fails, the `cfz` entry is absent or disabled with a
reason, and png/svg/pdf keep working.

A GUI test asserts that the export bytes are a zip containing `manifest.json`,
`figure.json`, and `data.parquet`, and that `format_version` is 1. It does
not render the bundle (that is this package's test).

## Tests in this repository

Synthetic tables only. Importing cellpy here would invert the dependency
arrow the moment someone "just uses a real cell in the test."

Minimum set for v1:

- Write a zip, open it, and compare the table and the spec.
- A missing column, an unknown key, and a newer `format_version` each raise
  an error that names the problem.
- `extensions` content survives a round-trip and is not interpreted.
- `to_matplotlib` and `to_plotly` on one panel with a color encoding and a
  stroke scale produce the expected number of series. Run matplotlib with
  `MPLBACKEND=Agg`.
- A call to `to_matplotlib` without matplotlib installed raises the
  extra-named error. Same for Plotly. (Install the extra in the positive
  tests; simulate the absence by monkeypatching the import, so CI does not
  need two environments.)

No pixel snapshots in v1. They fail across matplotlib versions and do not
catch a wrong column.

## Python library practice

These are the rules for this repository, taken from how cellpy, cellpy-core,
and cellpy-simple-gui are actually built, narrowed to a small library.

### Layout and tooling

- **src layout.** Installable code in `src/cellpy_figure/`. Tests in
  `tests/`. Hatch:

  ```toml
  [tool.hatch.build.targets.wheel]
  packages = ["src/cellpy_figure"]
  ```

  Editable `uv sync` puts the package on the path. Tests must not insert the
  repository root onto `sys.path`.

- **uv is the toolchain.** `uv sync`, then `uv run pytest`. Commit `uv.lock`.
  CI uses `uv sync --locked`. Do not call a bare `python` in docs or
  workflows.

- **Build backend is hatchling.** Same as the other three repositories. No
  setuptools configuration, no `setup.py`.

- **Version is single-sourced** from `src/cellpy_figure/__init__.py`
  (`__version__`), read by hatch via `[tool.hatch.version] path = ...`. This
  is the cellpy-simple-gui pattern, chosen over cellpy's
  `uv-dynamic-versioning`. Dynamic versioning from git tags reports `0.0.0`
  on a shallow checkout and has already forced cellpy to tolerate several
  historical tag spellings. A new package has no history to tolerate. The
  release workflow compares the tag to `__version__` and stops on a mismatch.

- **Python `>=3.13`.** One classifier, one CI job. cellpy-core's matrix of a
  single version is the model; do not copy a multi-version matrix until
  someone needs it.

- **Ruff, not black plus flake8.** cellpy-core's setup: line length 88,
  `select = ["E", "F", "W", "I"]`. cellpy's black length of 120 and its
  pre-existing flake8 debt are not a pattern to copy. Format is part of CI
  (`ruff check`, `ruff format --check`).

- **Google-style docstrings**, as in cellpy-core. Sections are `Args:`,
  `Returns:`, `Raises:`. They describe behaviour. mkdocstrings can render
  them later without a docstring migration.

- **Logging.** Use the stdlib logger named `cellpy_figure`. Log a warning
  when a file is opened with an ignored `extensions` payload only at debug.
  A schema violation raises. Do not print.

- **Errors name the fix.** Unknown format version, missing column, missing
  extra: the message says what was found and what to do (`pip install
  "cellpy-figure[mpl]"`). No bare `except`.

- **No new dependency for a stdlib job.** Zip handling is `zipfile`. JSON is
  `json`. Parquet is the one job that needs pyarrow.

### The sdist and the wheel

Follow cellpy-core: the sdist excludes `.github/`, `docs/`, `tests/`. The
wheel contains `cellpy_figure` and the JSON Schema if tests or the reader
load it from the package; otherwise the schema stays in `schema/` and is
only in the repository. Prefer loading the schema from the package so a
non-checkout install can validate. If it ships in the wheel, put it next to
the modules (`src/cellpy_figure/schema/figure-1.json`) and test that the
wheel contains it. cellpy-simple-gui lost this class of bug once (web assets
missing from the wheel); the publish workflow there runs `twine check` and
an explicit "is this path inside the wheel" assertion. Copy both.

## Continuous integration

One workflow, one required check name. cellpy-simple-gui's lesson: two
workflows that share a check name (a real one gated on `paths`, a mock gated
on `paths-ignore`) both fire on a pull request that touches code and docs,
and `gh pr checks` reports whichever it sees. Always run the real check.
This repository is small enough that docs-only pulls can run the suite too.
Skip the "detect docs-only and skip" logic until the suite is slow.

Shape, modelled on cellpy-core's `simpletest.yml` and cellpy's uv setup:

```text
on: pull_request, push to main, workflow_dispatch
runs-on: ubuntu-latest
steps:
  checkout
  astral-sh/setup-uv, Python 3.13
  uv sync --locked --all-extras --dev
  uv run ruff check
  uv run ruff format --check
  MPLBACKEND=Agg uv run pytest
```

`--all-extras` so the matplotlib and Plotly tests actually render. A test
that skips in CI because the extra was not installed is not a test; that
bit cellpy (plotting paths never ran until `batch` was synced) and the GUI
(MCP tests skipped until the extra was synced).

Headless matplotlib needs `MPLBACKEND=Agg` in the job even though the tests
should set it too. cellpy hid real plotting breakage for a while by
excluding those tests as "needs a display."

Pin the checkout action and setup-uv to a major version, as the other repos
do. Do not pin `uv` itself to an old patch unless a bug forces it;
cellpy-core pinned `0.8.13` for a reason that does not apply here. Use the
current setup-uv default.

Branch protection: the pytest job's name is the required check. Do not add a
second workflow that reports the same name.

Concurrency: cancel superseded runs on the same ref, as cellpy's CI workflow
does.

## Publishing

Trusted publishing (OIDC), as cellpy, cellpy-core, and cellpy-simple-gui
already do. GitHub proves the workflow's identity to PyPI. There is no API
token in the repository.

One-time setup, copied from cellpy-simple-gui's `docs/releasing.md`. It
cannot be automated; it needs a logged-in PyPI account:

1. PyPI → Account → Publishing → add a pending publisher (the project name
   is unclaimed until the first upload):
   - PyPI project: `cellpy-figure`
   - Owner: `cellpy` (the GitHub org, not the PyPI username)
   - Repository: `cellpy-figure`
   - Workflow: the filename, e.g. `publish.yml`
   - Environment: `pypi`
2. Repeat on TestPyPI with environment `testpypi` before the first real
   upload.
3. GitHub → Settings → Environments → create `pypi` and `testpypi`. Empty is
   fine. A required reviewer can be added later so a release waits for a
   person.

PyPI checks the environment name. If the workflow's `environment:` and the
pending publisher disagree, the upload is rejected. Renaming the workflow
file has the same effect: update the trusted publisher in the same change.

The workflow:

- Triggers on a published GitHub Release, or on a `v*` tag. Pick one and
  stick to it. cellpy and cellpy-core publish on `release: published`.
  cellpy-simple-gui publishes on a `v*` tag. For this package, **publish on
  `release: published`**, and make the release from a `vX.Y.Z` tag that
  matches `__version__`. The tag-match check from cellpy-simple-gui still
  runs: PyPI will never let that version number be reused, including after
  a deleted file.
- `permissions: id-token: write` on the publish job only.
- `uv build`, then `twine check`, then an assertion that
  `cellpy_figure/schema/figure-1.json` is in the wheel if we ship it there,
  then `pypa/gh-action-pypi-publish`.
- Checkout with `fetch-depth: 0` only if something reads git history. A
  static `__version__` does not need it. cellpy needs it because the version
  comes from tags.

Rehearse the first upload on TestPyPI via `workflow_dispatch`. cellpy-simple-gui
does this and it is the cheap way to discover a wrong environment name.

There is no container image and no conda-forge feedstock in v1. cellpy-simple-gui's
GHCR lesson (new org packages are private until an owner allows public
packages) does not apply until a container exists. A feedstock is reasonable
later, once PyPI has a release and cellpy pins it; it is not part of the
first milestone. Do not block the library on conda.

`HISTORY.md` is updated in the pull request that bumps the version, not after
the release. Keep entries short: what a coauthor or a cellpy caller can do
that they could not do before.

## Documentation

Do not stand up a doc site before the API in this file exists. The first
documentation is:

- `README.md`: what a `.cfz` is, the install line with the `mpl` extra, and
  the six-line open-and-save script. Point at this plan for contributors.
- Docstrings on `Figure`, `open_figure`, `to_matplotlib`, and `to_plotly`.
- `README.txt` inside every bundle.

When the API has settled, copy the cellpy / cellpy-core doc stack rather than
inventing one:

- [Zensical](https://zensical.org) (the successor to Material for MkDocs) plus
  `mkdocstrings-python`.
- A `docs` dependency group, not the default install.
- Read the Docs via `.readthedocs.yaml`: Ubuntu, Python 3.13, `pip install
  zensical mkdocstrings-python`, `zensical build --clean`, copy `site/` to
  the RTD output. cellpy-core's `.readthedocs.yaml` is the template.
- A docs workflow that builds the site **without installing the package**.
  mkdocstrings reads the source with Griffe. cellpy's docs workflow is
  deliberately separate from the test workflow so a docs failure is not
  confused with the required test check, and so the docs job's dependencies
  stay the doc tools only. Copy that split.
- Griffe's search path is `src`, as in cellpy's `zensical.toml` after the src
  layout move.
- Host stable from the latest release tag and latest from `main`, the same
  way cellpy does. There is no separate docs branch.

User docs describe the file and the two renderers. They do not explain
cellpy's plot families; that stays on cellpy's site, with a link to "export a
`.cfz`".

## Suggested order of work

1. Models, zip read/write, schema version check, round-trip tests. No
   renderer yet. A coauthor can already open `.data`.
2. `to_matplotlib` for one panel, nominal and quantitative color, stroke
   scale. Preset `notebook` and one journal preset.
3. `to_plotly` for the same encodings.
4. Facet row for a long summary table.
5. JSON Schema file and the wheel assertion.
6. PyPI trusted-publisher setup, TestPyPI rehearsal, `0.1.0`.
7. cellpy's `bundle.py` translator and one round-trip test per kind.
8. GUI export entry calling that translator.

Steps 1–6 are this repository. Steps 7 and 8 are pull requests in the other
two, and they wait until `0.1.0` is on PyPI so those projects can pin a
release rather than a git URL. cellpy-simple-gui already carries a temporary
git pin for another package and treats it as temporary; do not add another.

## Decisions recorded here

| Topic | Decision |
|---|---|
| Reader audience | Coauthor, no cellpy install |
| Writers | cellpy (translator) and, for views cellpy cannot express, the GUI |
| On-disk form | Zip, `.cfz`, one parquet table, spec in JSON |
| Schema escape hatch | `extensions`, ignored by the reader; any other unknown key errors |
| Style | Presets in this package; encodings and scales in the file |
| Renderers | matplotlib and Plotly, both optional extras |
| Version source | `__version__` in `__init__.py`, tag must match |
| Publish | Trusted publishing, on GitHub Release, environment `pypi` |
| Python | 3.13+ |
| First release blocker | Steps 1–6 above. cellpy and the GUI follow the release. |
