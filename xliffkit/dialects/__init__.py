"""xliffkit.core.dialects

Subpackage that aggregates dialect (Dialect) definitions.
Re-exports main dialect classes here.
"""

from __future__ import annotations

from .base import Dialect
from .generic_xliff import GenericXLIFF
from .mqxliff import MQXLIFF

__all__ = ['Dialect', 'MQXLIFF', 'GenericXLIFF']
