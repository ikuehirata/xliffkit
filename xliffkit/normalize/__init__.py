"""xliffkit.normalize

Module providing normalization functions for XLIFF documents.

Each module provides an independent set of normalization functions,
and here they are exposed at the module level.
"""

from __future__ import annotations

from . import context_id, flatten, tags, text

__all__ = ['context_id', 'tags', 'text', 'flatten']
