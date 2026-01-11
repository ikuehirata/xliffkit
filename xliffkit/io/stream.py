"""Load XLIFF and output <trans-unit> as a generic dict stream."""
from typing import Any, Dict, Iterator

from ..core.models import XliffDocument
from ..dialects.base import Dialect


def iter_tus(doc: XliffDocument, dialect: Dialect) -> Iterator[dict[str, Any]]:
    """Stream TUs from an XliffDocument as dicts one by one.

    Minimal, usage-agnostic representation.
    """
    for tu in doc.tus:
        d: Dict[str, Any] = {
            'id': tu.tu_id,
            'state': tu.state,
            'source': tu.source.text if tu.source else '',
            'target': tu.target.text if tu.target is not None else '',
        }
        if tu.comment is not None:
            d['comment'] = tu.comment

        # dialect に拡張を委ねる
        extra = dialect.extend_stream_dict(tu)

        if extra:
            d.update(extra)

        yield d
