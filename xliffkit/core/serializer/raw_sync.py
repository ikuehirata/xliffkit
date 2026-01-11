"""Apply split results to raw mqxliff DOM (raw-preserving).

This module implements `sync_raw_with_tus(doc)` which rewrites the
`doc.raw_xml` <body> children to reflect `doc.tus` while preserving the
existing tree structure as much as possible (deepcopy of existing
trans-unit nodes, no recreation of file/header, preserve attributes).
"""
from __future__ import annotations

from copy import deepcopy
from typing import Optional

import lxml.etree as etree

from .. import serializer
from ..models import Segment, XliffDocument


def _find_by_localname(el: etree.Element, name: str) -> Optional[etree.Element]:
    for node in el.iter():
        if etree.QName(node).localname == name:
            return node
    return None


def _replace_inner_from_segment(container: etree.Element, segment: Segment) -> None:
    """Replace inner XML of `container` from a Segment-like object.

    Prefer `segment.raw_xml` when present; otherwise use serializer.plain
    to render a safe inner-XML fallback.
    """
    # Remove existing children without touching attributes
    for child in list(container):
        container.remove(child)

    # Get inner XML string from serializer
    inner = serializer.plain._render_segment(segment)
    if not inner:
        container.text = None
        return

    # Parse fragment by wrapping in a dummy root. If parsing fails,
    # set as text (last-resort).
    try:
        frag = etree.fromstring(f'<root>{inner}</root>')
        container.text = frag.text
        for child in frag:
            container.append(deepcopy(child))
    except Exception:
        container.text = inner


def sync_raw_with_tus(doc: XliffDocument) -> None:
    """Apply the split `doc.tus` into `doc.raw_xml` body in-place.

    This mutates `doc.raw_xml` (an lxml element) so that the <body>
    contains trans-unit elements corresponding to `doc.tus` in order.

    Parameters
    ----------
    doc : XliffDocument
        Document containing `tus` and `raw_xml` to modify.
    """
    assert doc.raw_xml is not None, 'doc.raw_xml is required for sync_raw_with_tus'

    root = doc.raw_xml

    body = _find_by_localname(root, 'body')
    if body is None:
        raise RuntimeError('No <body> element found in raw_xml')

    # Remove existing children but keep body element and attributes
    for child in list(body):
        body.remove(child)

    # Iterate tus in the desired order and append rebuilt trans-unit nodes
    for index, tu in enumerate(doc.tus, start=1):
        # tu.raw_xml should be an Element representing the original trans-unit
        if tu.raw_xml is None:
            raise AssertionError('Each TU must have raw_xml for sync_raw_with_tus')

        trans_el = deepcopy(tu.raw_xml)

        # Reassign id sequentially (1-based)
        trans_el.attrib['id'] = str(index)

        # Ensure context-group / x-mmq-context is set according to TU context id.
        # Prefer attributes on TU in this order: `context_id`, `parent_context_id`, `parent_id`.
        ctx_value = None
        for attr in ('context_id', 'parent_context_id', 'parent_id'):
            ctx_value = getattr(tu, attr, None)
            if ctx_value:
                break

        if ctx_value:
            # find existing context-group element if any
            cg = None
            for child in trans_el:
                if etree.QName(child).localname == 'context-group':
                    cg = child
                    break

            if cg is None:
                # create context-group with a single context child
                cg = etree.Element('context-group')
                ctx_el = etree.Element('context')
                ctx_el.attrib['context-type'] = 'x-mmq-context'
                ctx_el.text = str(ctx_value)
                cg.append(ctx_el)
                trans_el.append(cg)
            else:
                # find context with context-type='x-mmq-context'
                found = None
                for c in cg:
                    if etree.QName(c).localname == 'context' and \
                            c.get('context-type') == 'x-mmq-context':
                        found = c
                        break

                if found is not None:
                    found.text = str(ctx_value)
                else:
                    # append a new context element into existing group
                    ctx_el = etree.Element('context')
                    ctx_el.attrib['context-type'] = 'x-mmq-context'
                    ctx_el.text = str(ctx_value)
                    cg.append(ctx_el)

        # Source
        for child in trans_el:
            if etree.QName(child).localname == 'source':
                _replace_inner_from_segment(child, tu.source)
                break

        # Target
        if tu.target is not None:
            for child in trans_el:
                if etree.QName(child).localname == 'target':
                    _replace_inner_from_segment(child, tu.target)
                    break

        # # ウザいのでmq:minorversions は削除する
        # for mv in trans_el.xpath("./*[local-name()='minorversions']"):
        #     trans_el.remove(mv)

        body.append(trans_el)


__all__ = ['sync_raw_with_tus']
