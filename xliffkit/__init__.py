"""xliffkit

`xliffkit` is a small utility package for handling XLIFF / mqXLIFF.
At the top level, it mainly aggregates subpackages and provides overall package version information
and simple usage hints.

Usage example:

    from xliffkit import __version__
    from xliffkit import core, io

Note: Actual functionality is implemented in each subpackage,
the top level mainly exposes submodules and the version.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

# package submodules
from . import core, dialects, exceptions, io, normalize, segment, utils

# package version (できるだけ importlib.metadata から取得し、失敗時は '0.0.0')
try:
    __version__ = version('xliffkit')
except PackageNotFoundError:
    __version__ = '0.0.0'

__all__ = [
    '__version__',
    'core', 'dialects', 'io', 'normalize', 'segment', 'utils', 'exceptions',
]
