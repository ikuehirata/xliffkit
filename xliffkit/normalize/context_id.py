"""Module for Context ID normalization."""

import uuid

from ..core.models import XliffDocument


def normalize_context_ids(
    doc: XliffDocument,
) -> XliffDocument:
    """Normalization that renumbers TU.context_id across the entire `doc`.

    **Destructive operation**: the `context_id` of each TU instance in the
    given `doc` is rewritten in place.
    """
    new_tus = []
    for tu in doc.tus:
        tu.context_id = str(uuid.uuid4())
        new_tus.append(tu)

    return doc.with_tus(new_tus)
