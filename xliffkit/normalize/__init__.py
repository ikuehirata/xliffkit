"""xliffkit.normalize

Module providing normalization functions for XLIFF documents.

Each module provides an independent set of normalization functions,
and here they are exposed at the module level.
"""

from __future__ import annotations

from . import flatten, tags, text

__all__ = ['tags', 'text', 'flatten']
