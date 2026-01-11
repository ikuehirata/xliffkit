"""Parser for XLIFF files into internal representation."""
from __future__ import annotations

import re

import lxml.etree as etree

from ...dialects.base import Dialect
from ..models import (
    TU,
    InlineTag,
    Segment,
    XliffDocument,
)

# -----------------------------
# helpers
# -----------------------------

def _strip_ns(tag: str) -> str:
    """{namespace}tag -> tag"""
    return tag.split('}', 1)[-1]


def _trim_xml_fragment(fragment: str) -> str:
    """Remove trailing plain text mistakenly appended to the end of an XML fragment string.

    - Returns up to the last closing tag if possible.
    - Returns up to '/>' if self-closing.
    - Returns the original string if neither is found.
    """
    if not fragment:
        return fragment

    # find last closing tag like '</...>'
    idx_last_close = fragment.rfind('</')
    if idx_last_close != -1:
        idx_gt = fragment.find('>', idx_last_close)
        if idx_gt != -1:
            return fragment[: idx_gt + 1]

    # fallback: look for self-closing '/>'
    idx_self = fragment.find('/>')
    if idx_self != -1:
        return fragment[: idx_self + 2]

    return fragment


def parse_inline_tag(child: etree.Element, position: int) -> tuple[InlineTag, str]:
    """Helper to generate InlineTag from a child element.

    - Trims the result of `ET.tostring(child)` and removes namespaces,
        storing it in InlineTag.original.
    - Uses the id or rid attribute for tag_id.
    """
    tag = _strip_ns(child.tag)
    raw_xml = etree.tostring(child, encoding='unicode')
    raw_xml = _trim_xml_fragment(raw_xml)
    raw_xml = _strip_namespace_from_fragment(raw_xml)
    raw_inner = re.sub(r'^<[^>]+>|</[^>]+>$', '', raw_xml).strip()

    return InlineTag(
        tag=tag,
        tag_id=child.attrib.get('id'),
        tag_rid=child.attrib.get('rid'),
        raw_inner=raw_inner,
        position=position,
    ), raw_xml


def _strip_namespace_from_fragment(fragment: str) -> str:
        """Remove XML namespace declarations and namespace prefixes from a fragment.

        Examples:
            '<ns0:bpt xmlns:ns0="..." id="1">' -> '<bpt id="1">'
        This operates on the raw XML fragment string and does not reparse XML.
        """
        if not fragment:
                return fragment

        # remove xmlns declarations: xmlns or xmlns:prefix
        fragment = re.sub(r'\s+xmlns(?::[A-Za-z0-9_]+)?="[^"]+"', '', fragment)

        # remove namespace prefixes on tags: <ns0:tag -> <tag, </ns0:tag -> </tag
        fragment = re.sub(r'<(/?)(?:[A-Za-z0-9_]+):([A-Za-z0-9_]+)', r'<\1\2', fragment)

        return fragment


def _parse_segment(elem: etree.Element | None, lang: str | None = None) -> Segment:
    """Convert <source> / <target> to Segment.

    - text is flattened
    - inline tags are kept as InlineTag
    """
    if elem is None:  # TODO インラインタグ処理がdialect 依存になってない
        return Segment(text='', lang=lang)

    pure_texts: list[str] = []  # 平文化テキスト断片
    raw_texts: list[str] = []  # rawテキスト断片 タグを含む
    inline_tags: list[InlineTag] = []

    # source.text
    if elem.text:
        pure_texts.append(elem.text)
        raw_texts.append(elem.text)

    # 子要素を順に処理: elem.text の蓄積長を position として渡す
    for child in elem:
        pos = len(''.join(pure_texts))
        tag, raw_xml = parse_inline_tag(child, position=pos)
        inline_tags.append(tag)
        raw_texts.append(raw_xml)

        # child.tail = タグ直後のテキスト
        if child.tail:
            pure_texts.append(child.tail)
            raw_texts.append(child.tail)

    pure_text = ''.join(pure_texts).strip()
    raw_text = ''.join(raw_texts).strip()

    return Segment(
        text=pure_text,
        tmx_text=raw_text,
        inline_tags=inline_tags,
        lang=lang,
        raw_xml=elem,
    )


# -----------------------------
# main parser
# -----------------------------

def parse_xliff(path: str, dialect: Dialect) -> XliffDocument:
    """Parse XLIFF file into internal representation."""
    tree = etree.parse(path)
    root = tree.getroot()

    tus: list[TU] = []

    # source_lang, traget_lang は file 要素から取得
    file_elm = root.find('.//{*}file')
    if file_elm is not None:
        source_lang = file_elm.attrib.get('source-language')
        target_lang = file_elm.attrib.get('target-language')
    else:
        source_lang = root.attrib.get('source-language')
        target_lang = root.attrib.get('target-language')

    order = 0

    for elem in root.iter():
        if _strip_ns(elem.tag) != 'trans-unit':
            continue

        tu_id = elem.attrib.get('id', '')
        raw_state = elem.attrib.get('state', 'new')  # 後で extra_attrs と合わせて正規化する

        source_elem = None
        target_elem = None
        note_elem = None

        for child in elem:
            tag = _strip_ns(child.tag)
            if tag == 'source':
                source_elem = child
            elif tag == 'target':
                target_elem = child
            elif tag == 'note':
                note_elem = child

        source = _parse_segment(source_elem, lang=source_lang)
        target = (
            _parse_segment(target_elem, lang=target_lang)
            if target_elem is not None
            else None
        )

        # context-group を探す
        context_group_elem = None
        for child in elem:
            if _strip_ns(child.tag) == 'context-group':
                context_group_elem = child
                break

        # ツール依存属性
        extra_attrs = {}
        if dialect.preserve_tu_attrs:
            for k, v in elem.attrib.items():
                if k.startswith('{'):
                    extra_attrs[k] = v
        # ここで正規化する
        state = dialect.normalize_state(raw_state, extra_attrs)

        comment = None
        if note_elem is not None:
            comment = ''.join(note_elem.itertext()).strip()

        tus.append(TU(
            tu_id=tu_id,
            source=source,
            target=target,
            state=state,
            context_id=dialect.get_context_id(context_group_elem),
            comment=comment,
            order=order,
            extra_attrs=extra_attrs,
            raw_xml=elem,
        ))

        order += 1

    return XliffDocument(
        tus=tus,
        dialect=dialect,
        source_lang=source_lang,
        target_lang=target_lang,
        raw_xml=root,
        metadata=dialect.extract_metadata(root)
    )
