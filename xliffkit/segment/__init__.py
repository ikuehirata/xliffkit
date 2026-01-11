"""xliffkit.segment

Segment editing utilities (flatten / split / merge).

Mainly exposes operational functions like `flatten.flatten_tu`.
"""

from __future__ import annotations

from . import merge, split

__all__ = ['merge', 'split']
