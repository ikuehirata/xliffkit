"""Detect dialect from filename."""
from __future__ import annotations

from typing import Type

from .base import Dialect


def detect_dialect_from_filename(
        filename: str,
        roundtrip: bool = False) -> Dialect:
    """Detect dialect from filename.

    Return GenericXLIFF if no known dialect matches.
    """
    from .generic_xliff import GenericXLIFF
    from .mqxliff import MQXLIFF

    dialect_map: dict[str, Type[Dialect]] = {
        'mqxliff': MQXLIFF,
        'generic': GenericXLIFF,
    }

    lowered = filename.lower()
    for name, dialect_cls in dialect_map.items():
        if name in lowered:
            return dialect_cls(roundtrip=roundtrip)

    return GenericXLIFF(roundtrip=roundtrip)
