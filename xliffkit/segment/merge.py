"""Merge split TUs back into original TUs by context_id.

Implements ``merge_document(doc)`` according to docs/specs/merge.md.
"""

from __future__ import annotations

import logging
import re
from typing import List

from .. import exceptions
from ..core.constants import NO_WORD_SEPARATION_LANGS
from ..core.models import TU, InlineTag, Segment, XliffDocument
from ..normalize.flatten import TOKEN_CLOSE, TOKEN_OPEN
from ..normalize.tags import normalize_tags_in_segment
from .split import normalize_flatten, reconstruct_segment_from_chunk

logger = logging.getLogger(__name__)

__all__ = ['merge_document']


def _merge_segments(segments: list[Segment]) -> Segment:
    """Merge a collection of segments

    Follows the step-by-step algorithm:
    0. Initialize empty `merged_flat_parts` and `merged_tags`.
    1. For each TU, normalize `source.flattened_text` via `normalize_flatten()`.
    2. In that normalized flattened text, add the current `len(merged_tags)` to
       every token id (TOKEN_OPEN <id> TOKEN_CLOSE).
    3. Append the adjusted flattened text into the merged flat (space-separated).
    4. For each `source.inline_tags`, increment its `tag_id` by `len(merged_tags)` and
       append to `merged_tags`.
    5. After all TUs processed, call `reconstruct_tu_from_chunk()` with a temporary TU
       whose `source.inline_tags` is `merged_tags` and the merged flattened chunk.
    6. Use the reconstructed `Segment` as the merged source.
    """
    def _inc(m):
        """Increments token IDs in the flattened text by the given offset."""
        try:
            return f'{TOKEN_OPEN}{int(m.group(1)) + offset}{TOKEN_CLOSE}'
        except Exception:
            return m.group(0)

    base = segments[0]

    merged_flat_parts: list[str] = []
    merged_tags: list[InlineTag] = []

    # Build a token regex using TOKEN_OPEN/TOKEN_CLOSE
    token_re = re.compile(re.escape(TOKEN_OPEN) + r'(\d+)' + re.escape(TOKEN_CLOSE))

    previous_adjusted = ''  # to check for spacing
    for segment in segments:
        # 1. For each TU, normalize `source.flattened_text` via `normalize_flatten()`.
        src_flat = segment.flattened_text or ''
        norm = normalize_flatten(src_flat)

        offset = len(merged_tags)

        # 2. In that normalized flattened text, add the current `len(merged_tags)` to
        #    every token id (TOKEN_OPEN <id> TOKEN_CLOSE).
        adjusted = token_re.sub(_inc, norm)

        # 3. Append the adjusted flattened text into the merged flat
        # (space-separated if not structured tag or Japanese).
        adjusted_notag = token_re.sub('', adjusted)
        if len(merged_flat_parts) > 0 and previous_adjusted.strip() and adjusted_notag.strip() and \
            base.lang not in NO_WORD_SEPARATION_LANGS:
            merged_flat_parts.append(' ')
        merged_flat_parts.append(adjusted)
        previous_adjusted = adjusted

        for t in (segment.inline_tags or []):
            try:
                orig = int(t.tag_id)
                new_id = str(orig + offset)
            except Exception:
                new_id = t.tag_id
            newt = InlineTag(
                tag=t.tag,
                tag_id=new_id,
                raw_inner=t.raw_inner,
                tag_rid=t.tag_rid,
                position=t.position,
            )
            merged_tags.append(newt)

    # 5. After all TUs processed, call `reconstruct_segment_from_chunk()` with a temporary TU
    if base.lang is None:
        raise ValueError('Segment.lang must not be None when merging segments.')
    new_source = reconstruct_segment_from_chunk(
        original_tags=merged_tags,
        original_lang=base.lang,
        flat=''.join(merged_flat_parts),
    )
    # 6. Normalize tags in the new source segment
    new_source = normalize_tags_in_segment(new_source)

    return new_source


def _merge_tu_group(group: List[TU]) -> TU:
    """Merge a contiguous group of TUs that share the same context_id.

    Returns a new TU based on the first TU in the group with merged
    `source` and `target` segments and renumbered inline tags.
    """
    # TUが1個しかないならそのまま返す
    if len(group) == 1:
        return group[0]

    # 複数個ある場合
    sources = [tu.source for tu in group]
    targets = [tu.target for tu in group if tu.target is not None]

    new_source = _merge_segments(sources)
    new_target = _merge_segments(targets) if targets else None

    base = group[0]
    return base.with_segments(source=new_source, target=new_target)


def merge_document(doc: XliffDocument) -> XliffDocument:
    """Merge ``doc.tus`` by ``context_id`` and return a new XliffDocument.

    This function follows the rules in docs/specs/merge.md. It performs
    fail-fast validation and logs errors before raising
    ``exceptions.MergeError``.

    """
    if not doc.tus:
        return doc

    # 連続グループと context_id 非空の検証
    for i, tu in enumerate(doc.tus):
        if not tu.context_id:
            logger.error('TU at index %d missing context_id (tu_id=%s)', i, tu.tu_id)
            raise exceptions.MergeError(f'Missing context_id at index {i} (tu_id={tu.tu_id})')

    new_tus: List[TU] = []

    # まず連続する同一 context_id の TU をグループ化する
    i = 0
    n = len(doc.tus)
    while i < n:
        ctx = doc.tus[i].context_id
        j = i + 1
        group = [doc.tus[i]]
        while j < n and doc.tus[j].context_id == ctx:
            group.append(doc.tus[j])
            j += 1

        # group に対してマージを行う
        merged = _merge_tu_group(group)
        new_tus.append(merged)

        i = j

    # 最終チェック: 出力で context_id が一意であることを確認
    ctxs = [t.context_id for t in new_tus]
    if len(set(ctxs)) != len(ctxs):
        logger.error('context_id collision after merge: %s', ctxs)
        raise exceptions.MergeError('context_id collision after merge')

    # 新しいドキュメントを返す
    return doc.with_tus(new_tus)
