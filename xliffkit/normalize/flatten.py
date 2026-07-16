"""flatten: a simple implementation that tokenizes inline tags in order.

Assumes the new InlineTag structure (tag, tag_id, xml, raw, id, position).
Each InlineTag is replaced in order with TOKEN_OPEN + id + TOKEN_CLOSE.
"""
from __future__ import annotations

import re

from ..core.models import InlineTag, Segment, XliffDocument

TOKEN_OPEN = '\uE000'
TOKEN_CLOSE = '\uE001'


def _build_pair_position_map(
    tags: list[InlineTag],
) -> dict[str | None, tuple[int, int]]:
    """Build a tag_id -> (bpt_position, ept_position) map for bpt-ept pairs.

    Only pairs with tag_rid set are included. Used for sorting same-position
    tags into correct nesting order.
    """
    rid_to_bpt: dict[str, InlineTag] = {}
    pair_map: dict[str | None, tuple[int, int]] = {}

    for tag in tags:
        if tag.tag == 'bpt' and tag.tag_rid is not None:
            rid_to_bpt[tag.tag_rid] = tag

    for tag in tags:
        if tag.tag == 'ept' and tag.tag_rid is not None:
            bpt = rid_to_bpt.get(tag.tag_rid)
            if bpt is not None:
                pair_map[bpt.tag_id] = (bpt.position, tag.position)
                pair_map[tag.tag_id] = (bpt.position, tag.position)

    return pair_map


def flatten_segment(
    seg: Segment, inline_tags: list[InlineTag] | None = None) -> str:
    """Tokenize inline tags in `source`/`target` and return an intermediate representation.

    Implementation approach:
    - Process tags in the order of `source/target.inline_tags` (i.e. by position).
    - Replace each tag's xml with `token = TOKEN_OPEN + id + TOKEN_CLOSE`.
    - Insert tags in descending order of position (right to left).
    - When multiple tags share the same position, preserve nesting structure:
        - bpt: insert the inner one (smaller ept_pos) first -> ends up further right
        - ept: insert the outer one (smaller bpt_pos) first -> ends up further right
      This guarantees correct nesting order such as <a><b>...</b></a>.

    Parameters
    ----------
    seg : Segment
            The segment to flatten.
    inline_tags : list[InlineTag] | None, optional
            Inline tags to use. If None, `seg.inline_tags` is used.

    Notes
    -----
    - Uses InlineTag.tag_id
    - Does not extract fragments from the original text corresponding to tags,
      nor re-parse XML. Uses the information provided by the parser as-is.
    - Assumes tag_rid has been set by normalize_tags_in_segment.
      If unset, nesting order is not guaranteed (falls back to tag_id).
    """
    if inline_tags is None:
        inline_tags = seg.inline_tags

    pair_map = _build_pair_position_map(inline_tags)

    def _sort_key(idx_tag: tuple[int, InlineTag]) -> tuple:
        """A 3-tier key: descending by position, then by nesting order for ties.

        With descending sort (reverse=True), tags "processed earlier" end up
        inserted further to the right.

        tiebreak1 (pair position):
          - bpt: process the inner one (smaller ept_pos) first -> -(ept_pos) is larger (less negative)
          - ept: process the outer one (smaller bpt_pos) first -> -(bpt_pos) is larger (less negative)

        tiebreak2 (index in the original list):
          Resolves the case where ept_pos / bpt_pos are equal due to full nesting.
          Tags that appear later (index, i.e. inner) in the XML are processed first -> end up right.
          Tags that appear earlier (outer) are processed later -> end up left (= ultimately outer).
        """
        idx, tag = idx_tag
        pair = pair_map.get(tag.tag_id)
        pos = tag.position
        if tag.tag == 'bpt':
            tiebreak1 = -(pair[1] if pair is not None else 0)
        elif tag.tag == 'ept':
            tiebreak1 = -(pair[0] if pair is not None else 0)
        else:
            tiebreak1 = 0
        return (pos, tiebreak1, idx)

    sorted_tags = sorted(enumerate(inline_tags), key=_sort_key, reverse=True)

    flat_text = seg.text

    for _, tag in sorted_tags:
        # determine token id: InlineTag.tag_id
        # 位置に挿入していく。flat_textにタグは含まれないため、置換はしない。
        tag_id_str = tag.tag_id if tag.tag_id is not None else f'pos{tag.position}'
        token = f'{TOKEN_OPEN}{tag_id_str}{TOKEN_CLOSE}'
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
