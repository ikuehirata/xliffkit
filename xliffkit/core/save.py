"""Save module"""
from __future__ import annotations

from pathlib import Path
from typing import Union

from .models import XliffDocument
from .serializer.mqxliff import serialize_mqxliff
from .serializer.plain import serialize

__all__ = ['save']


def save(doc: XliffDocument, out_path: Union[str, Path]) -> None:
    """Select the appropriate serializer based on the extension and doc.dialect, and write the file.

    The caller does not need to be aware of the serializer.
    """
    out_path = Path(out_path)
    suffix = out_path.suffix.lower()

    from ..dialects.mqxliff import MQXLIFF
    if suffix in {'.mqxliff'}:
        if not isinstance(doc.dialect, MQXLIFF):
            raise ValueError(
                f'Cannot write mqxliff from doc.dialect={doc.dialect!r}'
            )
        serialize_mqxliff(doc, out_path)
        return

    if suffix in {'.xliff', '.xlf'}:
        if doc.dialect is not None and doc.dialect is MQXLIFF:
            raise ValueError(
                f'Cannot write plain XLIFF from doc.dialect={doc.dialect!r}'
            )
        serialize(doc, out_path)
        return

    raise ValueError(f'Unsupported output format: {suffix}')
