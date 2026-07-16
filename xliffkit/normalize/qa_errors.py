"""Module for removing memoQ QA error elements."""

from __future__ import annotations

import lxml.etree as etree

from ..core.models import XliffDocument


def remove_qa_errors(doc: XliffDocument) -> XliffDocument:
    """Remove mq:warnings40 elements from each trans-unit.

    Removes the QA error information (<mq:warnings40>) that memoQ attaches,
    from all trans-units.

    Parameters
    ----------
    doc : XliffDocument
        The document to process.

    Returns
    -------
    XliffDocument
        The document with mq:warnings40 removed.
    """
    for tu in doc.tus:
        if tu.raw_xml is None:
            continue
        for child in list(tu.raw_xml):
            if etree.QName(child).localname == 'warnings40':
                tu.raw_xml.remove(child)
    return doc
