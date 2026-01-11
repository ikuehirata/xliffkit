"""Serializer: internal models -> XLIFF 1.2 XML.

This module provides a minimal serializer that converts an
`XliffDocument` (see `xliffkit.core.models`) into an XLIFF 1.2 string.

The goal is pragmatic: produce valid XLIFF 1.2 that can be consumed
by tools and used for roundtrip tests. The implementation prefers
`InlineTag.xml` when present and falls back to a small synthesized
element for inline tags.
"""

from __future__ import annotations

import xml.sax.saxutils as saxutils
from pathlib import Path
from typing import Union

from ..models import InlineTag, Segment, XliffDocument


def _escape_attr(value: str) -> str:
    return saxutils.escape(value or '', {'"': '&quot;'})


def _escape_inner_text(inner: str) -> str:
    # inner は &lt;mq:...&gt; 形式を前提とする
    # ここでは " だけを XML 用に逃がす
    return inner.replace('"', '&quot;')


def _render_inline_tag(tag: InlineTag) -> str:
    if tag is None:
        return ''
    tag_name = tag.tag or 'ph'

    attrs = []
    if tag.tag_id:
        attrs.append(f'id="{_escape_attr(tag.tag_id)}"')
    if tag.tag_rid:
        attrs.append(f'rid="{_escape_attr(tag.tag_rid)}"')
    attr_text = ' ' + ' '.join(attrs) if attrs else ''

    inner = tag.raw_inner or ''
    inner = _escape_inner_text(inner)
    return f'<{tag_name}{attr_text}>{inner}</{tag_name}>'


def _render_segment(segment: Segment) -> str:
    """Render a Segment into an XML string for source/target element inner XML.

    Prefer using raw_inner when available: this preserves existing inline
    elements and avoids fragile string-only manipulations. The raw_inner is
    expected to be a string containing the full element (e.g. '<source>...</source>').
    """
    # Use token-based replacement (existing behaviour).
    text = segment.text or ''

    # Escape normal text parts, but keep tokens intact. Tokens are in a
    # private area and survive escaping.
    escaped = saxutils.escape(text)

    tags = segment.inline_tags or []
    if not tags:
        return escaped

    # マッピングを、tag_id順に、positionとxmlとで作成
    mapping: dict[int, dict] = {}
    for tag in tags:
        tid = int(tag.tag_id)
        position = tag.position
        mapping[tid] = {
            'position': position,
            'xml': _render_inline_tag(tag),
        }
    # mappingをtidの逆順にソート（置換で位置がずれないようにするため）
    sorted_items = sorted(mapping.items(), key=lambda x: x[0], reverse=True)

    # positionの位置にxmlを挿入していく
    result = escaped
    for _, info in sorted_items:
        pos = info['position']
        xml = info['xml']
        result = result[:pos] + xml + result[pos:]

    return result


def serialize(xdoc: XliffDocument, out_path: Union[str, Path]) -> None:
    """Serialize XliffDocument to an XLIFF 1.2 XML string.

    Parameters
    ----------
    xdoc : XliffDocument
        Document to serialize.
    out_path : str
        Output file path (used for writing).

    """
    lines: list[str] = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    # declare xliffkit prefix so attributes like xliffkit:origin-tu-id are valid XML
    lines.append('<xliff version="1.2" xmlns:xliffkit="urn:xliffkit">')

    # file-level attributes
    assert xdoc.raw_xml is not None, 'XliffDocument.raw_xml is required for serialization'
    # raw_xml をそのまま使う

    lines.append('  <body>')

    # sort TU: use TU.order if set, otherwise keep original order
    indexed = list(enumerate(xdoc.tus))

    def _key(item):
        idx, tu = item
        return tu.order if getattr(tu, 'order', -1) and tu.order >= 0 else idx

    for _, tu in sorted(indexed, key=_key):
        attrs = [f'id="{_escape_attr(tu.tu_id)}"']
        for k, v in (tu.extra_attrs or {}).items():
            # extra_attrs の中で xliffkit で始まるものは memoQに消去されるので、避ける
            if k.startswith('xliffkit'):
                continue
            attrs.append(f'{k}="{_escape_attr(v)}"')
        lines.append('    <trans-unit ' + ' '.join(attrs) + '>')

        if tu.comment:
            lines.append('      <note>' + saxutils.escape(tu.comment) + '</note>')

        # # context_xml の書き出し  # TODO
        # if tu.context_xml:
        #     lines.append('      ' + tu.context_xml.strip())

        # source
        s_lang = f' xml:lang="{_escape_attr(tu.source.lang)}"' \
            if tu.source and tu.source.lang else ''
        s_text = _render_segment(tu.source) if tu.source else ''
        lines.append(f'      <source{s_lang} xml:space="preserve">' + s_text + '</source>')

        # target
        if tu.target is None or tu.target.is_empty():
            lines.append('      <target xml:space="preserve"></target>')
        else:
            t_lang = f' xml:lang="{_escape_attr(tu.target.lang)}"' \
                if tu.target and tu.target.lang else ''
            t_text = _render_segment(tu.target)
            lines.append(f'      <target{t_lang} xml:space="preserve">' + t_text + '</target>')

        lines.append('    </trans-unit>')

    lines.append('  </body>')
    lines.append('</file>')
    lines.append('</xliff>')

    txt = '\n'.join(lines)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(txt)


__all__ = ['serialize']
