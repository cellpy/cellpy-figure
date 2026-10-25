# cellpy-figure

## What this project is

TODO: Summarize the project in one short paragraph. Mention what it does, who it is for, and the main outcome it produces.

## Stack / runtime

- TODO: Primary language(s), runtime versions, package manager(s), and major frameworks.
- TODO: External services, CLIs, or local tools that agents should know about.

## How to run / test

```bash
TODO: command to install or sync dependencies
TODO: command to run the main test suite
TODO: command to run lint/format checks
```

## Conventions

- TODO: Branch, commit, formatting, typing, testing, or review conventions that are specific to this project.
- TODO: Any project-specific workflow details that are easy for agents to miss.
- **Multi-root workspaces:** put this repo's Python/toolchain commands here (conda vs uv, test invocations, etc.) so they do not collide with sibling repos in a shared editor workspace.

## Release & version bump

Version `0.1.0` is already on PyPI. PyPI will not accept that number again.

The version string lives only in `src/cellpy_figure/__init__.py` as
`__version__`. Hatch reads it through `[tool.hatch.version] path`.
`pyproject.toml` keeps `dynamic = ["version"]`. Do not run `uv version`, and
do not write a version into `pyproject.toml`. This is not a git-tag version:
there is no setuptools-scm, hatch-vcs, or versioningit backend.

To release a new version:

1. On the issue branch, set `__version__` to the next number. On a stable
   release the default step is `patch`. In that same pull request, promote
   `HISTORY.md`: move `## [Unreleased]` to `## [<version>] - <YYYY-MM-DD>`
   and leave a fresh empty `## [Unreleased]` above it.
2. Merge that pull request. Do not tag it, and do not create the GitHub
   Release from the issue branch.
3. From `main`, after that version commit is on the default branch:

```bash
gh release create vX.Y.Z --repo cellpy/cellpy-figure --target main --title "vX.Y.Z"
```

The tag without the leading `v` must equal `__version__`. Take the release
notes from the version section in `HISTORY.md`.

`.github/workflows/publish.yml` runs when that release is published. A bare
tag push does not publish. The publish job uses GitHub environment `pypi`
and trusted publishing (OIDC). There is no API token. The pending publisher
is already registered: PyPI project `cellpy-figure`, owner `cellpy`,
repository `cellpy-figure`, workflow `publish.yml`, environment `pypi`. The
workflow builds the sdist and wheel, checks them, asserts
`cellpy_figure/schema/figure-1.json` is in the wheel, and uploads to PyPI.

Do not dispatch the workflow's TestPyPI target, and do not create a
`testpypi` environment. The `workflow_dispatch` choice that lists `testpypi`
is unused.

## Entry points

- TODO: Main application/package/module entry point.
- TODO: Important directories or files to read first.

## Non-goals / known limitations

- TODO: Scope boundaries, known caveats, or things this project intentionally does not do.
