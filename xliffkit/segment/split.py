"""Sentence-based TU splitting utilities (spec-compliant).

This module implements splitting according to the project specification
(`xliffkit/docs/specs/segment_split.md`). It is sentence-based,
language-agnostic and conservative: it preserves inline tags,
treats structural token spans (e.g. <br>/newline tokens) as independent
segments, and does not embed split metadata into the XLIFF.
"""

from __future__ import annotations

import re
from typing import Pattern

from ..core.models import TU, InlineTag, Segment, XliffDocument
from ..normalize.context_id import normalize_context_ids
from ..normalize.flatten import TOKEN_CLOSE, TOKEN_OPEN


def _default_trigger() -> Pattern[str]:
    return re.compile(r'\.\s+')


def split_tu(
        tu: TU,
        trigger: Pattern[str] | str | None = None,
    ) -> list[TU]:
    """Split a single ``TU`` into multiple ``TU``s.

    The process is carried out in the following stages:
    1. Normalize the flatten text (``normalize_flatten``)
    2. Detect split points (``detect_split_points``)
    3. Split the flatten text into chunks (``split_flatten``)
    4. Reconstruct new TUs from each chunk (``reconstruct_tu_from_chunk``)
    """
    flat = tu.source.flattened_text or ''
    if not flat:
        # 空テキストはそのまま返す
        new_tu = TU(
            tu_id='',
            source=tu.source.with_text(tu.source.text),
            target=(tu.target.with_text(tu.target.text) if tu.target is not None else None),
            context_id=tu.context_id,
            raw_xml=tu.raw_xml,
        )
        return [new_tu]

    # 1. 正規化
    norm = normalize_flatten(flat)

    # 1.5 構造的分割: 改行/BR系タグで先に分割する
    structural_chunks = split_by_structural_tags(norm, tu.source.inline_tags or [])

    # 2. 各構造チャンクに対して文分割をかける
    result_chunks: list[str] = []
    pattern = _default_trigger()
    for sch in structural_chunks:
        result_chunks.extend(split_by_pattern(sch, pattern))

    # 3. triggerがある場合は分割、ない場合はそのまま
    trigger_chunks: list[str] = []
    if trigger is not None:
        trigger_pattern = re.compile(trigger)
        for sch in result_chunks:
            trigger_chunks.extend(split_by_pattern(sch, trigger_pattern))
    else:
        trigger_chunks = result_chunks

    # trigger_chunks の終端を調整する
    trigger_chunks = adjust_trigger_chunks(trigger_chunks, tu.source.inline_tags)

    # 4. 各チャンクから新 TU を再構築
    parts: list[TU] = []
    for idx, chunk in enumerate(trigger_chunks):
        assert tu.context_id is not None, 'Original TU must have context_id.'
        new_tu = reconstruct_tu_from_chunk(tu, chunk, tu.context_id, is_first=(idx == 0))
        parts.append(new_tu)

    if not parts:
        return [tu]

    return parts


def adjust_trigger_chunks(
    chunks: list[str], inline_tags: list[InlineTag] | None
) -> list[str]:
    """Adjust chunks end.

    if next chunk starts with a closing tag, move it to the end of the current chunk.

    Parameters
    ----------
    chunks : list[str]
        List of split chunks.
    inline_tags : list[InlineTag] | None
        Inline tags list of the original segment.

    Returns
    -------
    list[str]
        Adjusted list of chunks.
    """
    if not chunks:
        return chunks

    # 安全のため inline_tags を辞書化しておく (tag_id -> InlineTag)
    tag_map: dict[str, InlineTag] = {}
    for t in (inline_tags or []):
        tid = getattr(t, 'tag_id', None)
        if tid is not None:
            tag_map[tid] = t

    i = 0
    # 先頭から走査して、次のチャンクの先頭に ept トークンがあれば移動する
    while i < len(chunks) - 1:
        # 次チャンクを参照
        next_chunk = chunks[i + 1]
        moved = False
        # next_chunk の先頭にトークンがある限り繰り返す
        while next_chunk.startswith(TOKEN_OPEN):
            end_idx = next_chunk.find(TOKEN_CLOSE, len(TOKEN_OPEN))
            if end_idx == -1:
                break
            tag_id = next_chunk[len(TOKEN_OPEN):end_idx]
            inline_tag = tag_map.get(tag_id)
            # 該当タグが存在し、かつタグ名が 'ept' の場合に移動する
            if inline_tag is None or getattr(inline_tag, 'tag', None) != 'ept':
                break
            # トークン部を切り出して前チャンクの末尾に追加
            token = next_chunk[: end_idx + len(TOKEN_CLOSE)]
            chunks[i] = (chunks[i] or '') + token
            # next_chunk から先頭トークンを取り除く
            next_chunk = next_chunk[end_idx + len(TOKEN_CLOSE) :]
            chunks[i + 1] = next_chunk
            moved = True
        # 移動後、もし次チャンクが空になっていたら削除して同じ i を再チェック
        if moved and chunks[i + 1].strip() == '':
            chunks.pop(i + 1)
            # 次チャンクが消えたので同じ i で再度確認
            continue
        i += 1

    return chunks


def normalize_flatten(flat: str) -> str:
    """Normalize flatten text while preserving token regions.

    Replace consecutive whitespace with a single space and trim leading/trailing whitespace,
    but do not modify token regions enclosed by TOKEN_OPEN/TOKEN_CLOSE.
    """
    parts = flat.split(TOKEN_OPEN)
    out_parts: list[str] = []
    for i, p in enumerate(parts):
        if i == 0:
            out_parts.append(re.sub(r'\s+', ' ', p).strip())
            continue
        if TOKEN_CLOSE in p:
            token_content, rest = p.split(TOKEN_CLOSE, 1)
            out_parts.append(TOKEN_OPEN + token_content + TOKEN_CLOSE + re.sub(r'\s+', ' ', rest))
        else:
            out_parts.append(TOKEN_OPEN + p)
    return ''.join(out_parts)


def split_by_structural_tags(flat: str, inline_tags: list[InlineTag]) -> list[str]:
    """Split `flat` at structural (newline/br) tag tokens.

    Check the specified `inline_tags` for tag IDs whose
    `raw_inner` contains newlines or `<br>` equivalents, and split at those token positions.
    """
    # special tag ids
    special_ids = {
        t.tag_id for t in (inline_tags or [])
        if t.raw_inner and (
            '\n' in t.raw_inner or '&lt;br' in t.raw_inner.lower())
        and t.tag_id is not None}
    if not special_ids:
        return [flat]

    # special_ids に対応するトークン表現だけを検索し、その前後で分割する
    special_tokens = [TOKEN_OPEN + tid + TOKEN_CLOSE for tid in special_ids]
    positions: list[tuple[int, int]] = []
    for tok in special_tokens:
        start_idx = 0
        while True:
            idx = flat.find(tok, start_idx)
            if idx == -1:
                break
            positions.append((idx, idx + len(tok)))
            start_idx = idx + len(tok)

    positions.sort()
    chunks: list[str] = []
    prev = 0
    for start, end in positions:
        if prev < start:
            chunks.append(flat[prev:start])
        # structural token を独立チャンクとして追加
        chunks.append(flat[start:end])
        prev = end
    if prev < len(flat):
        chunks.append(flat[prev:])

    # normalize chunks (strip and drop empty)
    return [c.strip() for c in chunks if c.strip() != '']


def split_by_pattern(chunk: str, pattern: Pattern[str]) -> list[str]:
    """Apply sentence-splitting rules to a chunk and return sentence chunks."""
    points = detect_split_points(chunk, pattern)
    return split_flatten(chunk, points)


def detect_split_points(flat: str, pattern: Pattern[str]) -> list[int]:
    """Detect split points (end offsets) that are not inside token regions."""
    points: list[int] = []
    for m in pattern.finditer(flat):
        end = m.end()
        # トークン内部かどうかを判定（end までの TOKEN_OPEN/CLOSE の数を比較）
        opens = flat.count(TOKEN_OPEN, 0, end)
        closes = flat.count(TOKEN_CLOSE, 0, end)
        if opens == closes:
            points.append(end)
    return points


def split_flatten(flat: str, points: list[int]) -> list[str]:
    """Split flattened text into chunks using end-offset points."""
    if not points:
        return [flat]
    chunks: list[str] = []
    prev = 0
    for p in points:
        chunks.append(flat[prev:p])
        prev = p
    if prev < len(flat):
        chunks.append(flat[prev:])
    # strip each chunk
    return [c for c in (c.strip() for c in chunks) if c != '']


def reconstruct_segment_from_chunk(
        original_tags: list[InlineTag], original_lang: str, flat: str) -> Segment:
    """Reconstruct a Segment from a chunk of normalized flatten text."""
    # チャンクを左から走査して new_text と tag_id -> position の写像を作る
    i = 0  # index in chunk
    j = 0  # index in new_text
    new_chars: list[str] = []
    tag_positions: dict[str, int] = {}
    L = len(flat)
    while i < L:
        if flat.startswith(TOKEN_OPEN, i):
            end_idx = flat.find(TOKEN_CLOSE, i + len(TOKEN_OPEN))
            if end_idx == -1:
                # malformed token, treat as literal
                new_chars.append(flat[i])
                i += 1
                j += 1
                continue
            tag_id = flat[i + len(TOKEN_OPEN):end_idx]
            # 記録: 現在の new_text 側インデックスをこの tag_id の位置とする
            tag_positions[tag_id] = j
            i = end_idx + len(TOKEN_CLOSE)
            continue
        # 通常の文字
        new_chars.append(flat[i])
        i += 1
        j += 1

    # これが新しいタグ無しテキスト
    new_text = ''.join(new_chars)

    # 新しい inline_tags を作る
    new_inline: list[InlineTag] = []
    for tag_id, pos in tag_positions.items():
        # 元の inline_tags から tag_id に対応するタグを探す
        inline_tags = original_tags or []
        matched = None
        for t in inline_tags:
            if getattr(t, 'tag_id', None) == tag_id:
                matched = t
                break
        if matched is not None:
            newt = InlineTag(
                tag=matched.tag,
                tag_id=matched.tag_id,
                raw_inner=matched.raw_inner,
                tag_rid=matched.tag_rid,
                position=pos,
            )
            new_inline.append(newt)

    new_source = Segment(
        text=new_text,
        inline_tags=new_inline,
        lang=original_lang,
        raw_xml=None,
    )

    return new_source

def reconstruct_tu_from_chunk(
        original: TU,
        chunk: str,
        parent_context_id: str,
        is_first: bool) -> TU:
    """Reconstruct a TU from a chunk of normalized flatten text.

    - Extract tag tokens (TOKEN_OPEN id TOKEN_CLOSE) contained in the chunk,
      and select the corresponding tags from the original inline_tags.
    - Scan the chunk from the left to identify the positions of tag tokens,
      and set these as the positions of the inline_tags.
    - Simultaneously create a new text by removing the chunk,
      resulting in new_text.
    """
    # chunk 本体も flattenする
    flat = normalize_flatten(chunk)

    # ソースセグメントを再構築
    new_source = reconstruct_segment_from_chunk(
        original.source.inline_tags or [],
        original.source.lang or '',
        flat)

    new_target = None
    if is_first and original.target is not None:
        new_target = original.target.with_text(original.target.text)

    new_tu = TU(
        tu_id='',
        source=new_source,
        target=new_target,
        context_id=parent_context_id,
        raw_xml=original.raw_xml,
    )
    return new_tu


def is_to_release_new_context_id(tus: list[TU]) -> bool:
    """Release new context IDs for `tus` in-place."""
    # context_idが存在しない場合は新規発行する
    ctx_ids = [(t.context_id, t.tu_id) for t in tus]
    if any(cid is None for cid, _ in ctx_ids):
        return True
    # 全部のcontext idが50文字以上ならそのまま採用
    if all(cid is not None and len(cid) >= 50 for cid, _ in ctx_ids):
        return False
    # 一意でない場合
    # 各 id の出現回数をカウント（None を除外）
    counts: dict[str, int] = {}
    for cid, _ in ctx_ids:
        if cid is None:
            continue
        counts[cid] = counts.get(cid, 0) + 1
    if any(v > 1 for v in counts.values()):
        return True
    return False


def split_document(
        doc: XliffDocument,
        trigger: Pattern[str] | str | None = None,
        split_policy: dict[str, bool] | None = None,
    ) -> XliffDocument:
    """Return a new XliffDocument with `tus` split by sentence.

    Parameters
    ----------
    doc : XliffDocument
        The XLIFF document to split.
    trigger : Pattern[str] | str | None, optional
        The sentence split trigger pattern. If None, no sentence splitting
        is applied (only structural splitting). By default None.
    split_policy : dict[str, bool] | None, optional
        A mapping from `tu_id` to a boolean indicating whether to split
        that TU. If None, all TUs are split. By default None.
    """
    # 新規context_id 発行の要否を判定
    if is_to_release_new_context_id(doc.tus):
        doc = normalize_context_ids(doc)

    new_tus: list[TU] = []
    for tu in doc.tus:
        # split_policy がある場合はそれに従う
        if split_policy is not None:
            do_split = split_policy.get(tu.tu_id, True)
            if not do_split:
                new_tus.append(tu)
                continue
        parts = split_tu(tu, trigger=trigger)
        new_tus.extend(parts)

    # 新規docを作成
    new_doc = doc.with_tus(new_tus)
    # tu_id を振り直す
    new_doc = new_doc.reorder_tu_id()

    return new_doc
