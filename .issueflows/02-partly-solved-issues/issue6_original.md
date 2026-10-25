# Issue #6: Publish 0.1.0 with trusted publishing

Source: https://github.com/cellpy/cellpy-figure/issues/6

## Original issue text

`cellpy-figure` 0.1.0 is not on PyPI. cellpy `save_bundle` (jepegit/cellpy#1132) and the GUI `.cfz` export (cellpy/cellpy-simple-gui#196) both wait on that release, and both forbid a git pin. `__version__` is already `0.1.0`. PyPI will not reuse that number, so this issue publishes only after the library issues have landed.

Blocked by #1, #2, #3, #4, and #5.

## Spec

- Add `.github/workflows/publish.yml` using trusted publishing (OIDC). No API token in the repo.
- Trigger on `release: published`, plus `workflow_dispatch` with a `testpypi` / `pypi` choice. Do not publish on a bare tag push.
- The publish job sets `permissions: id-token: write` and `environment: pypi` (rehearsal: `testpypi`).
- Before upload: the release tag `vX.Y.Z` must equal `__version__` in `src/cellpy_figure/__init__.py`. Then `uv build`, `twine check`, and an assertion that `cellpy_figure/schema/figure-1.json` is in the wheel.
- `HISTORY.md` is part of the release pull request: a short note of what a caller can do in 0.1.0.
- `README.md` gets the install line `pip install "cellpy-figure[mpl]"` and the six-line open-and-save script.

One-time setup, done by a person logged into PyPI (same pattern as cellpy-simple-gui `docs/releasing.md`):

- Pending publisher on PyPI for project `cellpy-figure`, owner `cellpy`, repository `cellpy-figure`, workflow `publish.yml`, environment `pypi`.
- The same on TestPyPI with environment `testpypi`.
- GitHub environments `pypi` and `testpypi` on this repository.

Rehearse with workflow_dispatch to TestPyPI. Install the wheel by its URL, not by pointing uv at the TestPyPI index. Then `gh release create v0.1.0` from `main`.

## Acceptance criteria

- TestPyPI rehearsal succeeds and the downloaded wheel imports.
- The GitHub Release `v0.1.0` publishes to `https://pypi.org/project/cellpy-figure/`.
- `uv add cellpy-figure` resolves that release.
- The tag and `__version__` match. A mismatch fails the workflow before upload.

## Out of scope

- A container image and a conda-forge feedstock.
- The cellpy translator and the GUI export. Those are separate repositories and start after this release is on PyPI.
