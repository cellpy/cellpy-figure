# Issue #4 plan: Ship the figure JSON Schema in the wheel

## Goal

`figure-1.json` describes format version 1 and is loaded from the installed package. A wheel contains it at `cellpy_figure/schema/figure-1.json`. A `figure.json` written by `Figure.write` validates, and an unknown key fails.

## Constraints

- Hand-write the schema. Do not add a generator.
- The schema matches the keys `io.py` already accepts. `extensions` stays an open object. Every other object rejects unknown keys.
- Include `facet`. Issue #5 stores it, and this schema must accept that file.
- `open_figure` keeps its current checks. It does not validate with JSON Schema on every open, and `jsonschema` is a dev dependency, not a runtime one. PLAN.md already refuses a new runtime dependency for a check the reader performs.
- Out of scope: rendering, the publish workflow, and a second copy of the file under a top-level `schema/` directory.

### Prior art

- `cellpy_figure.io` key sets — mirror. Manifest keys are `format`, `format_version`, `created`. Figure keys are `title`, `panels`, `provenance`, `extensions`. Panel keys add `facet` to x, y, color, and stroke. Encoding keys are `field`, `label`, `unit`, `type`, `legend_title`, `scale`. Provenance keys are `producer`, `producer_version`, `note`, `source`.
- `tests/test_io.py` — reuse the write path. The schema test calls `Figure.write` and reads `figure.json` back out of the zip.
- `PLAN.md` "The sdist and the wheel" — the file lives at `src/cellpy_figure/schema/figure-1.json`, and a test asserts that path inside the wheel.
- Toolbox: none. Graph: no `graphify-out/graph.json`.

## Approach

1. Add Draft 2020-12 `src/cellpy_figure/schema/figure-1.json`. The root is the figure spec. `$defs.manifest` describes `manifest.json`.
2. Required figure fields are `panels` (at least one) and `provenance`. `title` is an optional string. `extensions` is an optional object that allows any keys. Panel `x` and `y` are required. Color `type` is `nominal` or `quantitative`. Scale values are strings. Provenance requires non-empty `producer` and `producer_version`. Manifest `format` is `cellpy-figure`, `format_version` is `1`, and `created` is a string.
3. `cellpy_figure.schema.load_schema()` reads that file with `importlib.resources`, so a non-checkout install does not need a `schema/` path in the repository.
4. Add `jsonschema` to the dev group with `uv add --dev`. Tests use `Draft202012Validator` on the loaded schema.
5. A wheel test runs `uv build --wheel` and asserts `cellpy_figure/schema/figure-1.json` is in the archive. If hatchling omits the file, add one `force-include` for that path.

## Files to touch

- `src/cellpy_figure/schema/figure-1.json` — the schema.
- `src/cellpy_figure/schema/__init__.py` — `load_schema`.
- `tests/test_schema.py` — round-trip validation, unknown key, manifest, and the wheel path.
- `pyproject.toml`, `uv.lock` — dev dependency `jsonschema`.
- `README.md`, `PLAN.md` — status: the schema ships in the wheel; publishing does not.

## Test strategy

From the worktree, with extras installed:

```bash
uv sync --locked --all-extras --dev
uv run ruff check
uv run ruff format --check
MPLBACKEND=Agg uv run pytest
```

Cases: `Figure.write` produces a `figure.json` that validates, including a facet encoding. Adding an unknown key fails and the error names that key. `manifest.json` validates against `$defs.manifest`. The built wheel contains `cellpy_figure/schema/figure-1.json`.

## Open questions

- None.
