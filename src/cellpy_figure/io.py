"""Read and write a ``.cfz`` bundle.

The zip layout (``manifest.json``, ``figure.json``, ``data.parquet``,
``README.txt``) is specified in ``PLAN.md`` and is not implemented yet.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cellpy_figure.model import Figure


def open_figure(path: str) -> Figure:
    """Open a ``.cfz`` bundle.

    Args:
        path: Path to the bundle.

    Returns:
        The figure, with ``data`` as a ``pandas.DataFrame``.

    Raises:
        NotImplementedError: Bundle reading is not implemented yet.
    """
    raise NotImplementedError("reading a .cfz bundle is not implemented yet")
