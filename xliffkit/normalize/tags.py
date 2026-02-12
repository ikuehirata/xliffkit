"""Module for normalizing tags within XLIFF documents.

This module primarily targets mqxliff. Dialect support may be added
in the future.
"""
import html
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Literal

from ..core.models import InlineTag, Segment, XliffDocument


@dataclass
class InlineTagToken:
    """Intermediate representation of an InlineTag used during normalization.

    Attributes
    ----------
    idx : int
        Index in the original InlineTag list
    tag_id : str
        InlineTag.tag_id
    original_tag : str
        元の InlineTag.tag（ほぼ ph）
    corrected_tag : Literal['x', 'ph', 'bpt', 'ept']
        tags corrected to their proper types based on analysis
    tag_name : str | None
        e.g. 'style', 'b', 'i', or None
    is_open : bool
        Whether this token represents an opening tag
    is_close : bool
        Whether this token represents a closing tag
    pair_with : int | None
        Index of the matching tag (filled in later)
    rid : str | None
        The rid attribute, if present
    """

    idx: int
    tag_id: str | None
    original_tag: str
    ''''元の InlineTag.tag（ほぼ ph）'''
    corrected_tag: Literal['x', 'ph', 'bpt', 'ept']
    tag_name: str | None
    '''style / b / i / その他'''
    is_open: bool
    is_close: bool
    pair_with: int | None = None
    '''対応するタグの idx'''
    rid: str | None = None


_MQ_VAL_RE = re.compile(r'val="([^"]+)"')
_TAG_RE = re.compile(
    r'^(?:<|\[)\s*(/)?\s*([a-zA-Z0-9:_-]+)',
    re.VERBOSE,
)


def extract_mq_val(raw: str) -> str | None:
    """Extract the `val` attribute from mq:rxt raw and return it after double-unescaping."""
    # まず raw 全体を unescape
    unescaped = html.unescape(raw)

    # val 属性を抽出
    m = _MQ_VAL_RE.search(unescaped)
    if not m:
        return None

    # val の中身もさらに unescape
    val = html.unescape(m.group(1))
    return val


def analyze_plain_tag(plain: str) -> tuple[bool, bool, str | None]:
    """Determine the plain name of a tag.

    Examples of `plain`:
        "<style>"
        "</style>"
        "<b>"
        "</i>"
    """
    s = plain.strip()
    m = _TAG_RE.match(s)
    if not m:
        return False, False, None

    is_close = m.group(1) is not None
    is_open = not is_close
    tag_name = m.group(2).lower()

    return is_open, is_close, tag_name


def build_inline_tag_tokens(
    inline_tags: list[InlineTag],
) -> list[InlineTagToken]:
    """Scan and construct.

    Scan the InlineTag list and construct a list of InlineTagToken intermediate representations.
    """
    tokens: list[InlineTagToken] = []

    for idx, tag in enumerate(inline_tags):
        tag_name: str | None = None
        is_open = False
        is_close = False

        # mq:rxt を含む ph のみ解析対象
        if tag.tag == 'ph':
            assert tag.raw_inner is not None
            plain = extract_mq_val(tag.raw_inner)
            if plain:
                is_open, is_close, tag_name = analyze_plain_tag(plain)
            corrected_tag = 'ph'
        # bpt / ept は強制的に開閉を決定
        elif tag.tag == 'bpt':
            is_open = True
            tag_name = 'unknown'  # 不明
            corrected_tag = 'bpt'
        elif tag.tag == 'ept':
            is_close = True
            tag_name = 'unknown'  # 不明
            corrected_tag = 'ept'
        elif tag.tag == 'x':
            is_close = False
            tag_name = 'x'
            corrected_tag = 'x'
        else:
            raise ValueError(f'Unexpected tag: {tag.tag}')

        token = InlineTagToken(
            idx=idx,
            tag_id=tag.tag_id,
            original_tag=tag.tag,
            corrected_tag=corrected_tag,
            tag_name=tag_name,
            is_open=is_open,
            is_close=is_close,
            pair_with=None,
        )
        tokens.append(token)

    return tokens


def pair_inline_tag_tokens(
    tokens: list[InlineTagToken],
) -> None:
    """Scan an InlineTagToken list from the end to fill `pair_with` and set tag types (bpt/ept).

    The `tokens` list is modified in-place.
    """
    close_stack: dict[str, list[int]] = defaultdict(list)

    # 後ろから走査
    for token in reversed(tokens):
        tag_name = token.tag_name
        if not tag_name:
            continue

        # --- 閉じタグ ---
        if token.is_close:
            close_stack[tag_name].append(token.idx)
            continue

        # --- 開きタグ ---
        if token.is_open:
            stack = close_stack.get(tag_name)
            if stack:
                close_idx = stack.pop()
                close_token = tokens[close_idx]

                # pair を確定
                token.pair_with = close_idx
                close_token.pair_with = token.idx

                # tag を昇格
                token.corrected_tag = 'bpt'
                close_token.corrected_tag = 'ept'

            # stack が空 → 相手なし、ph のまま


def dump_tokens(tokens: list[InlineTagToken]) -> None:
    """Debug helper that dumps an InlineTagToken list to stdout."""
    for t in tokens:
        print(t)


def assign_rids(tokens: list[InlineTagToken]) -> None:
    """Assign `rid` values to InlineTagTokens that have confirmed `pair_with` links.

    - Assign `rid` = 1,2,3... in the order bpt tags appear
    - ept tags receive the same `rid` as their corresponding bpt
    """
    rid_counter = 1

    # idx 昇順 = テキスト出現順
    for token in sorted(tokens, key=lambda t: t.idx):
        if token.corrected_tag != 'bpt':
            continue
        if token.pair_with is None:
            continue
        if token.rid is not None:
            continue  # 念のため（通常不要）

        rid = str(rid_counter)
        rid_counter += 1

        token.rid = rid

        # 対応する ept にも付与
        other = tokens[token.pair_with]
        other.rid = rid


# raw末尾の "/&gt;"（スペース有無）を検出
_RXT_SELF_CLOSING_RE = re.compile(r'\s*/&gt;\s*$')

def normalize_mq_rxt_raw_for_tag(
        raw_xml: str,
        outer_tag: Literal['ph', 'bpt', 'ept']) -> str:
    """Format the inner part of `raw_xml` to match memoQ expectations."""
    # raw_xml から <>囲みを取り除き、inner部分だけを取り出す
    s = re.sub(r'<[^>]+>', '', raw_xml).strip()

    if outer_tag == 'ph':
        # すでに self-closing ならスペース付きに正規化
        if _RXT_SELF_CLOSING_RE.search(s):
            return _RXT_SELF_CLOSING_RE.sub(' /&gt;', s)

        # 末尾が "&gt;" なら " /&gt;" に変換
        if s.endswith('&gt;'):
            return s[:-4] + ' /&gt;'

        # 末尾が予期しない場合：触らない（安全側）
        return s

    if outer_tag in {'bpt', 'ept'}:
        # self-closing を non-self-closing に
        if _RXT_SELF_CLOSING_RE.search(s):
            s = _RXT_SELF_CLOSING_RE.sub('&gt;', s)

        # bptの場合、&lt;/mq があるなら &lt;mq に変換
        if outer_tag == 'bpt' and s.startswith('&lt;/mq'):
            s = '&lt;mq' + s[7:]
        # eptの場合、&lt;mq があるなら &lt;/mq に変換
        if outer_tag == 'ept' and s.startswith('&lt;mq'):
            s = '&lt;/mq' + s[6:]

        # 末尾が "&gt;" ならOK
        return s

    # それ以外は変更しない
    return s


def rebuild_inline_tags(
    original: list[InlineTag],
    tokens: list[InlineTagToken],
) -> list[InlineTag]:
    """Rebuild an InlineTag list from a normalized InlineTagToken list.

    Parameters
    ----------
    original : list[InlineTag]
        The original InlineTag list
    tokens : list[InlineTagToken]
        The normalized InlineTagToken list

    Returns
    -------
    list[InlineTag]
        The reconstructed InlineTag list
    """
    if len(original) != len(tokens):
        raise ValueError('original and tokens length mismatch')

    new_tags: list[InlineTag] = []

    for orig, token in zip(original, tokens):
        tag = token.corrected_tag
        rid = token.rid if tag in {'bpt', 'ept'} else None
        assert orig.tag_id is not None

        new_tags.append(
            InlineTag(
                tag=tag,
                tag_id=orig.tag_id,
                raw_inner=orig.raw_inner,
                tag_rid=rid,
                position=orig.position,
            )
        )

    return new_tags


def normalize_tags_in_segment(seg: Segment) -> Segment:
    """Destructive operation that normalizes ph/bpt/ept tags within a segment.

    Fixes inconsistencies where tags that should be bpt/ept are represented
    as ph, and similar issues.

    Parameters
    ----------
    seg : Segment
        Segment to normalize

    Returns
    -------
    Segment
        Normalized segment
    """
    # セグメントの元々の inline tag 列を中間生成物列に変換
    tokens = build_inline_tag_tokens(seg.inline_tags)
    # TODO markdown で ** などの装飾タグに対応するためには、seg を渡して
    # TODO raw_inner を直接解析する必要がある
    # TODO ただしそこまでする必要ある？
    # ペアリングを実行
    pair_inline_tag_tokens(tokens)
    # rid を付与
    assign_rids(tokens)
    # 正規化済み inline tag 列を再構築
    new_tags = rebuild_inline_tags(seg.inline_tags, tokens)

    return seg.with_inline_tags(new_tags)

def normalize_all_tags(doc: XliffDocument) -> XliffDocument:
    """Destructive operation that normalizes all ph/bpt/ept tags in the document.

    Parameters
    ----------
    doc : XliffDocument
        XLIFF document to normalize

    Returns
    -------
    XliffDocument
        Normalized XLIFF document
    """
    for tu in doc.tus:
        tu.source = normalize_tags_in_segment(tu.source)
        if tu.target is not None:
            tu.target = normalize_tags_in_segment(tu.target)

    return doc.with_tus(doc.tus)
