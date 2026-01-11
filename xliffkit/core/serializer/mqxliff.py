"""mqxliff serializer.

Includes serialize_mqxliff which writes the DOM as-is,
and a plain serializer which serializes based on tokens.
"""
from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path
from typing import Union

import lxml.etree as etree

from ..models import XliffDocument

# Public API
__all__ = ['serialize_mqxliff']


_INLINE_TAG_RE = re.compile(
    r'(<(?:ph|bpt|ept)\b[^>]*>)(.*?)(</(?:ph|bpt|ept)>)',
    re.DOTALL,
)

def _fix_memoq_inner_quotes(xml: str) -> str:
    """Restore " to &quot; in pseudo-XML inside memoQ inline tags.

    lxml decodes entities, so we fix the string after writing.
    """
    def repl(m: re.Match) -> str:
        open_tag, body, close_tag = m.group(1), m.group(2), m.group(3)

        # memoQ 疑似タグだけ対象（安全弁）
        stripped = body.lstrip()
        if stripped.startswith('&lt;mq:') or stripped.startswith('&lt;/mq:'):
            body = body.replace('"', '&quot;')

        return open_tag + body + close_tag

    return _INLINE_TAG_RE.sub(repl, xml)


def serialize_mqxliff(
    doc: XliffDocument,
    out_path: Union[str, Path],
    *,
    encoding: str = 'utf-8',
    xml_declaration: bool = True,
) -> None:
    """
    Write the mqxliff DOM (doc.raw_xml or doc.raw_tree) directly to a file.

    - Does not modify the DOM
    - Does not pretty_print
    - Does not tostring/fromstring
    - Does not re-register namespaces
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    root = getattr(doc, 'raw_xml', None)
    if root is None:
        raise ValueError('doc.raw_xml is required (root element).')

    # doc が ElementTree を保持しているならそれを優先（docinfo保持の可能性があるため）
    tree = getattr(doc, 'raw_tree', None)
    if tree is None:
        # root から ElementTree を作って write
        tree = etree.Element(root)

    # バイナリで一度バッファに書く
    buf = BytesIO()
    tree.write(
        buf,
        encoding=encoding,
        xml_declaration=xml_declaration,
        pretty_print=False,
        with_tail=False,
    )

    # 文字列に戻す
    xml = buf.getvalue().decode(encoding)

    # ★ ここが本質的な修正点
    xml = _fix_memoq_inner_quotes(xml)

    # 最終出力
    out_path.write_text(xml, encoding=encoding)
