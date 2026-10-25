# Issue 4 status

`figure-1.json` describes format version 1 and loads from the installed package. A written figure and its manifest validate. An unknown key fails and names the key. The wheel contains `cellpy_figure/schema/figure-1.json`. 31 tests passed, and ruff is clean.

- [x] Done

## What's done

- Hand-written Draft 2020-12 schema, including `facet` and an open `extensions` object.
- `cellpy_figure.schema.load_schema()` reads the packaged file. `open_figure` does not validate with it.
- `jsonschema` is a dev dependency. The wheel test passed without a hatch `force-include`.

## Remaining work

- None.
