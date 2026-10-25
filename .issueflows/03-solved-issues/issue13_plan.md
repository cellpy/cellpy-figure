# Issue 13 plan — publishing skills

## Goal

Make `/iflow-close` and the version-bump skill follow this repository’s real release path: edit `__version__`, then publish to GitHub and PyPI from `main`. Do not cut a new release in this issue.

## Constraints

- The generated skills under `.cursor/skills/iflow-*` are replaced by `issue-flow update`. Project procedure belongs in `.issueflows/04-designs-and-guides/this-project.md`, which those skills already read first and which update does not overwrite.
- `issue-flow agent version-plan` currently returns `strategy: unknown` (`dynamic [project] version with an unrecognized backend`) and `brief_release_section: todo`. Hatch’s `[tool.hatch.version] path` is not a static `uv version` field and not a git-tag backend.
- `__version__` is already `0.1.0` and that version is on PyPI. This issue does not bump it, tag it, or upload it again.
- Production publish is a published GitHub Release. A bare tag push does not publish. The workflow environment is `pypi`. Do not dispatch the TestPyPI target.
- Do not run `issue-flow update` here. That refreshes every skill and is separate from recording this release path.

### Prior art

- `iflow-version-bump` — follows the “Release & version bump” section of `this-project.md` verbatim; otherwise it cannot plan a bump for this backend.
- `iflow-close` — after a `publish` label, creates `gh release create "v<version>"` only once the version is on the default branch. It does not name this repo’s PyPI environment.
- [publish.yml](.github/workflows/publish.yml) — `release: published`, environment `pypi`, tag must equal `__version__`, then `uv build` and trusted publishing. A `workflow_dispatch` choice still lists `testpypi`; this issue does not remove that job.
- [PLAN.md](PLAN.md) — version is single-sourced from `src/cellpy_figure/__init__.py`. The status line and the TestPyPI rehearsal paragraph are stale after the 0.1.0 upload.
- Toolbox: none. No knowledge graph in this repo.

## Approach

Fill **Release & version bump** in [this-project.md](.issueflows/04-designs-and-guides/this-project.md). Leave the other TODO sections alone. The section will say:

1. Change only `__version__` in `src/cellpy_figure/__init__.py`. Do not run `uv version` and do not write a version into `pyproject.toml`.
2. In that same pull request, promote `HISTORY.md` from `## [Unreleased]` to the new version. Do not tag or create the GitHub Release on the issue branch.
3. After the pull request is on `main`, create the release from `main` with `gh release create vX.Y.Z --repo cellpy/cellpy-figure --target main`. The tag, without the leading `v`, must equal `__version__`.
4. [publish.yml](.github/workflows/publish.yml) then uploads to PyPI with trusted publishing. The GitHub environment name is `pypi`. The pending publisher is already registered for owner `cellpy`, repository `cellpy-figure`, workflow `publish.yml`, environment `pypi`.
5. Do not use the TestPyPI dispatch, and do not publish a version PyPI already has.

Correct the two stale status sentences (README and PLAN) and PLAN’s TestPyPI rehearsal paragraph so they match that path: 0.1.0 is published; the next release follows the brief; TestPyPI is not part of it.

## Files to touch

- `.issueflows/04-designs-and-guides/this-project.md` — replace the TODO release section with the procedure above.
- `README.md` — status sentence: 0.1.0 is on PyPI; the next release follows the brief.
- `PLAN.md` — same status correction, and drop the instruction to rehearse the first upload on TestPyPI.

## Test strategy

No product tests. After the edit, `issue-flow agent version-plan --json` must report `brief_release_section` as filled. Do not bump `__version__`.

## Open questions

- None. The generated skill files stay as they are; the brief is the hook they already honor.
