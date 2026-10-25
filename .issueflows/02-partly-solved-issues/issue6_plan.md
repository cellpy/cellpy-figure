# Issue #6 plan: Publish 0.1.0 with trusted publishing

## Goal

Add a trusted-publishing workflow and the 0.1.0 release notes. `__version__` stays `0.1.0`. The PyPI upload happens after this pull request merges, from a GitHub Release, once a person has registered the pending publisher.

## Constraints

- No API token in the repo. Publish with OIDC.
- Trigger on `release: published`, plus `workflow_dispatch` with a `testpypi` / `pypi` choice. Do not publish on a bare tag push. cellpy-simple-gui publishes on tags; this repo does not copy that trigger.
- The workflow filename is `publish.yml`. The environments are `pypi` and `testpypi`. Renaming either later requires the same change on PyPI.
- Job names must not be `test (linux / uv)`. That name is the required CI check.
- The tag `v0.1.0` must equal `__version__` before a real upload. A mismatch fails the workflow. `workflow_dispatch` has no tag, so that check runs only for a published release.
- Do not bump the version. `0.1.0` is already in `src/cellpy_figure/__init__.py`, and PyPI will not reuse it.
- This pull request writes the `0.1.0` history section. Close must not append another changelog bullet.
- Out of scope: a container image, a conda-forge feedstock, the cellpy translator, and the GUI export.

### Prior art

- `cellpy-simple-gui/.github/workflows/publish.yml` — mirror the build, `twine check`, wheel-contents assertion, and the two publish jobs. Change the trigger to `release: published`. Assert `cellpy_figure/schema/figure-1.json` instead of the GUI's web assets.
- `cellpy-simple-gui/docs/releasing.md` — the pending-publisher steps. PyPI account **jepe**, GitHub owner `cellpy`, project `cellpy-figure`.
- `.github/workflows/ci.yml` — pin `actions/checkout@v6` and `astral-sh/setup-uv@v6`, matching this repo. Do not copy the GUI's older pins.
- `src/cellpy_figure/io.py` `README_TEXT` — the install line and the open-and-save script for `README.md`.
- Toolbox: none. Graph: no `graphify-out/graph.json`.

## Approach

1. Add `.github/workflows/publish.yml`.
   - `workflow_dispatch` input `target` defaults to `testpypi`.
   - A build job runs `uv build`, `twine check` via `uv run --no-project --with twine`, and asserts the schema path is in the wheel.
   - On `release: published`, compare `github.event.release.tag_name` without the leading `v` to `__version__`. Stop before upload if they differ.
   - `publish (TestPyPI)` runs only for a dispatch whose target is `testpypi`. `publish (PyPI)` runs for a published release, or a dispatch whose target is `pypi`.
   - Only the publish jobs set `permissions: id-token: write` and `environment:`.
2. Rewrite `HISTORY.md` into Keep a Changelog shape. Replace the scaffold bullet, which says rendering is not implemented. `## [0.1.0] - 2026-10-25` says a caller can read and write a `.cfz`, draw one panel or a facet row, and validate the spec with the schema in the wheel. Leave an empty `## [Unreleased]` above it.
3. `README.md` gains `pip install "cellpy-figure[mpl]"` and the open-and-save script. It still points at `PLAN.md`.
4. The pull request does not upload. After it merges, a person does the one-time setup and the release:
   - Pending publisher on PyPI and TestPyPI for owner `cellpy`, repository `cellpy-figure`, workflow `publish.yml`, environments `pypi` and `testpypi`.
   - Empty GitHub environments with those same names.
   - `workflow_dispatch` to TestPyPI. Install that wheel by its file URL, not by pointing uv at the TestPyPI index, and import it.
   - `gh release create v0.1.0` from `main`.
   - Confirm `https://pypi.org/project/cellpy-figure/` and that `uv add cellpy-figure` resolves `0.1.0`.

## Files to touch

- `.github/workflows/publish.yml` — trusted publishing.
- `HISTORY.md` — the `0.1.0` note.
- `README.md` — install line, script, and status.
- `PLAN.md` — status: the workflow is in the repo; the first upload waits on the pending publisher.
- `tests/test_publish_workflow.py` — the workflow text triggers on a published release and `workflow_dispatch`, and it does not list a tag push.

## Test strategy

From the worktree:

```bash
uv sync --locked --all-extras --dev
uv run ruff check
uv run ruff format --check
MPLBACKEND=Agg uv run pytest
```

The suite stays green. The new test only reads `publish.yml`. The TestPyPI rehearsal and the real upload are checked after merge, by the person who owns the PyPI account.

## Open questions

- None.
