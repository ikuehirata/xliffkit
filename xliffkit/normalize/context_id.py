"""Module for Context ID normalization."""

import uuid

from ..core.models import XliffDocument


def normalize_context_ids(
    doc: XliffDocument,
) -> XliffDocument:
    """Normalize by reassigning TU.context_id across the entire doc."""
    new_tus = []
    for tu in doc.tus:
        tu.context_id = str(uuid.uuid4())
        new_tus.append(tu)

    return doc.with_tus(new_tus)
