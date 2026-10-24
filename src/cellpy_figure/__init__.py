"""A figure bundle a coauthor can redraw without installing cellpy."""

__version__ = "0.1.0"

from cellpy_figure.io import BundleError, open_figure
from cellpy_figure.model import Encoding, Figure, Panel, Provenance

__all__ = [
    "BundleError",
    "Encoding",
    "Figure",
    "Panel",
    "Provenance",
    "open_figure",
    "__version__",
]
