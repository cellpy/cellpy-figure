# Issue #4: Ship the figure JSON Schema in the wheel

Source: https://github.com/cellpy/cellpy-figure/issues/4

## Original issue text

Non-Python tools need a schema for the spec, and a wheel install must be able to validate without a git checkout. `schema/figure-1.json` does not exist yet.

Blocked by #1, because the schema has to describe the JSON that `Figure.write` actually emits.

## Spec

- Add `src/cellpy_figure/schema/figure-1.json` for format_version 1, covering manifest and figure spec fields from PLAN.md (including `extensions` as an open object, and rejecting unknown keys elsewhere).
- The reader loads that schema from the installed package, not from a `schema/` path that only exists in the repository.
- A test builds the wheel (`uv build`) and asserts `cellpy_figure/schema/figure-1.json` is inside it.
- Keep the schema and the Python models in agreement: a fixture written by `Figure.write` validates, and a document with an unknown key does not.

## Acceptance criteria

- The schema file is in the wheel at `cellpy_figure/schema/figure-1.json`.
- A round-tripped `figure.json` validates against it.
- An unknown key fails validation and names the key.

## Out of scope

- Rendering.
- Publishing to PyPI (the publish workflow will repeat the wheel assertion).
- A generated-schema toolchain, unless hand-writing the file proves brittle. PLAN.md allows either hand-written or generated.
