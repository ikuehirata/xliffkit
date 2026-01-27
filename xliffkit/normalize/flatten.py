"""flatten: a simple implementation that tokenizes inline tags in order.

Assumes the new InlineTag structure (tag, tag_id, xml, raw, id, position).
Each InlineTag is replaced in order with TOKEN_OPEN + id + TOKEN_CLOSE.
"""
from __future__ import annotations

import re

from ..core.models import InlineTag, Segment, XliffDocument

TOKEN_OPEN = '\uE000'
TOKEN_CLOSE = '\uE001'


def flatten_segment(
    seg: Segment, inline_tags: list[InlineTag] | None = None) -> str:
    """Tokenize inline tags in `source`/`target` and return an intermediate representation.

    Implementation notes:
    - Process tags in the order of `source/target.inline_tags` (or by
        `position`).
    - Replace each tag's XML with `token = TOKEN_OPEN + id + TOKEN_CLOSE`.

    Parameters
    ----------
    seg : Segment
            The segment to flatten.
    inline_tags : list[InlineTag] | None, optional
            Inline tags to use. If None, `seg.inline_tags` is used.

    Notes
    -----
    - Uses `InlineTag.tag_id`.
    - Does not attempt to extract fragments from the original text or
        re-parse XML; it relies on information provided by the parser.
    """
    if inline_tags is None:
        inline_tags = seg.inline_tags

    # ソート: tag_id を優先して安定化
    indexed: list[tuple[int | None, int, InlineTag]] = []
    for t in inline_tags:
        indexed.append((int(t.tag_id), t.position, t))
    indexed.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)

    flat_text = seg.text

    for _, _, tag in indexed:
        # determine token id: InlineTag.tag_id
        # 位置に挿入していく。flat_textにタグは含まれないため、置換はしない。
        token = f'{TOKEN_OPEN}{tag.tag_id}{TOKEN_CLOSE}'
        flat_text = flat_text[:tag.position] + token + flat_text[tag.position:]

    return flat_text


def flatten_all_segments(doc: XliffDocument) -> XliffDocument:
    """Destructive operation that flattens all source/target segments in the document.

    Parameters
    ----------
    doc : XliffDocument
        XLIFF document to flatten

    Returns
    -------
    XliffDocument
        Flattened XLIFF document
    """
    new_tus = []
    for tu in doc.tus:
        new_source = tu.source
        new_target = tu.target

        if tu.source is not None:
            flat_source_text = flatten_segment(tu.source)
            new_source = tu.source.with_flattened_text(flat_source_text)

        if tu.target is not None:
            flat_target_text = flatten_segment(tu.target)
            new_target = tu.target.with_flattened_text(flat_target_text)

        new_tu = tu.with_segments(source=new_source, target=new_target)
        new_tus.append(new_tu)

    return doc.with_tus(new_tus)


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in the given text.

    Parameters
    ----------
    text : str
        Text to normalize

    Returns
    -------
    str
        Normalized text
    """
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = text.replace('\u00a0', ' ')   # NBSP
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def normalize_whitespace_all_segments(doc: XliffDocument) -> XliffDocument:
    """Normalize whitespace in all segments of the document (destructive operation).

    Parameters
    ----------
    doc : XliffDocument
        Document to normalize

    Returns
    -------
    XliffDocument
        Normalized document
    """
    new_tus = []
    for tu in doc.tus:
        new_source = tu.source
        new_target = tu.target

        if tu.source is not None and tu.source.flattened_text is not None:
            norm_source_text = normalize_whitespace(tu.source.flattened_text)
            new_source = tu.source.with_flattened_text(norm_source_text)

        if tu.target is not None and tu.target.flattened_text is not None:
            norm_target_text = normalize_whitespace(tu.target.flattened_text)
            new_target = tu.target.with_flattened_text(norm_target_text)

        new_tu = tu.with_segments(source=new_source, target=new_target)
        new_tus.append(new_tu)

    return doc.with_tus(new_tus)


__all__ = [
    'flatten_segment',
    'TOKEN_OPEN', 'TOKEN_CLOSE',
    'normalize_whitespace', 'normalize_whitespace_all_segments']
