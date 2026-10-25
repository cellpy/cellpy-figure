# Issue 6 status

The publish workflow, the 0.1.0 history note, and the README install script are ready to merge. A pending publisher for `cellpy-figure` has been registered. The GitHub environments `pypi` and `testpypi` are not on the repository yet, and nothing has been uploaded. 32 tests passed, and ruff is clean.

- [ ] Done

## What's done

- `.github/workflows/publish.yml` publishes on a published GitHub Release or a manual dispatch. A bare tag push does not publish.
- A published release must match `__version__`. The wheel check looks for `cellpy_figure/schema/figure-1.json`.
- `HISTORY.md` has the `0.1.0` note. `README.md` has the install line and the open-and-save script.
- The pending publisher was registered by the project owner.

## Remaining work

- Create the empty GitHub environments `pypi` and `testpypi`.
- After this pull request merges, rehearse with a manual dispatch to TestPyPI and install that wheel by its file URL.
- Publish the GitHub Release `v0.1.0` from `main`, then confirm the PyPI project.
