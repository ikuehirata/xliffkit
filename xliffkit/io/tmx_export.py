"""mqxliff/merged objects -> TMX `<tu>` element streaming conversion module

This module provides utilities to sequentially generate TMX `<tu>` elements
from a list of merged mqxliff TU objects (in memory).
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterator

import lxml.etree as etree

from ..core.models import TU, InlineTag, Segment, XliffDocument
from ..core.serializer.plain import _render_segment


def _tag_renderer_for_tmx(tag: InlineTag) -> str:
    """Render an InlineTag for TMX.

    Parameters
    ----------
    tag : InlineTag
        Inline tag to convert.

    Returns
    -------
    str
        Rendered string.
    """
    if tag is None:
        return ''

    # ph で末尾に " /&gt;" が入らないタグは開き/閉じタグ → it として描画 (元オブジェクトは変更しない)
    effective_tag = tag.tag
    if tag.raw_inner and tag.tag == 'ph' and not tag.raw_inner.endswith(' /&gt;'):
        effective_tag = 'it'

    attrs = []
    # x タグの場合は <ph type='fmt'>{}</ph> に
    if effective_tag == 'x':
        return "<ph type='fmt'>{}</ph>"
    # it の場合は pos="begin" / "end" を付与する
    if effective_tag == 'it':
        if tag.raw_inner and tag.raw_inner.startswith('&lt;/'):
            attrs.append('pos="end"')
        else:
            attrs.append('pos="begin"')
    # tag_id を i として追加する
    if tag.tag_rid:
        attrs.append(f"i='{tag.tag_rid}'")
    attr_text = ' ' + ' '.join(attrs) if attrs else ''

    inner = tag.raw_inner or ''
    # TMX 用にエスケープ
    inner = inner.replace('<', '&lt;').replace('>', '&gt;')
    return f'<{effective_tag}{attr_text}>{inner}</{effective_tag}>'


def make_tuv_from_seg(seg: Segment) -> etree.SubElement:
    """Create an etree.SubElement 'tuv' from a Segment.

    Parameters
    ----------
    seg : Segment
        Segment to convert.

    Returns
    -------
    etree.SubElement
        Created 'tuv' element.
    """
    # tuv を作成
    elem = etree.Element('tuv')
    if seg.lang is None:
        raise ValueError(
            'Segment.lang is None — cannot write TMX tuv without xml:lang. '
            'Ensure source-language and target-language are set in the XLIFF file element.'
        )
    elem.set('{http://www.w3.org/XML/1998/namespace}lang', seg.lang)
    seg_elem = etree.SubElement(elem, 'seg')

    # seg_elem の中身相当するものは、レンダラーを使って平文レンダリング
    rendered = _render_segment(seg, tag_renderer=_tag_renderer_for_tmx)
    # ダミールートで包んで再パース
    wrapper = etree.fromstring(f'<wrapper>{rendered}</wrapper>')
    # text
    seg_elem.text = wrapper.text
    # 子要素
    for child in wrapper:
        seg_elem.append(child)

    return elem


def convert_tu_to_element(
    org_tu: TU,
    include_locked: bool = False,
    escape_markup: bool = True,
    document_name: str | None = None,
    client: str | None = None,
    project: str | None = None,
    domain: str | None = None,
    subject: str | None = None,
) -> etree.Element | None:
    """Convert a TU object (or dict) to a TMX `<tu>` Element.

    Parameters
    ----------
    item : TU | dict
        TU to convert (expected xliffkit.core.models.TU or dict).
    include_locked : bool, optional
        Whether to include locked TUs.
    escape_markup : bool, optional
        If True, markup will be included as text (escaping occurs on output).
    client : str | None, optional
        Override client property.
    project : str | None, optional
        Override project property.
    domain : str | None, optional
        Override domain property.
    subject : str | None, optional
        Override subject property.

    Returns
    -------
    etree.Element | None
        Generated `<tu>` element, or None if conversion is not possible.
    """
    def get_attr(obj, name, default=None):
        try:
            if isinstance(obj, dict):
                return obj.get(name, default)
            return getattr(obj, name, default)
        except Exception:
            return default

    # 判定: locked 属性
    if org_tu.is_locked and not include_locked:
        return None

    changedate = get_attr(org_tu.extra_attrs, '{MQXliff}lastchangedtimestamp', '')
    creationdate = get_attr(org_tu.extra_attrs, '{MQXliff}translatorcommittimestamp', '')
    changeid = get_attr(org_tu.extra_attrs, '{MQXliff}lastchanginguser', '')
    creationid = get_attr(org_tu.extra_attrs, '{MQXliff}translatorcommitusername', '')

    tu = etree.Element('tu')
    if changedate:
        tu.set('changedate', changedate.replace(':', '').replace('-', ''))
    if creationdate:
        tu.set('creationdate', creationdate.replace(':', '').replace('-', ''))
    if creationid:
        tu.set('creationid', creationid)
    if changeid:
        tu.set('changeid', changeid)

    meta = get_attr(org_tu, 'meta', {}) or {}
    for key in ('client', 'project', 'domain', 'subject'):
        val = meta.get(key) if isinstance(meta, dict) else ' '
        if key == 'client' and client is not None:
            val = client
        elif key == 'project' and project is not None:
            val = project
        elif key == 'domain' and domain is not None:
            val = domain
        elif key == 'subject' and subject is not None:
            val = subject
        p = etree.SubElement(tu, 'prop', {'type': f'x-{key}'})
        p.text = val or ' '

    # document はここで追加
    p = etree.SubElement(tu, 'prop', {'type': 'x-document'})
    if document_name is not None:
        p.text = document_name
    else:
        p.text = ' '

    # ここで `make_tuv_from_seg` を呼んで、返り値の `tuv` 要素を `tu` に追加する。
    # source 側の tuv を作成して tu に追加
    src_seg = org_tu.source
    src_tuv = make_tuv_from_seg(src_seg)
    tu.append(src_tuv)

    # target 側の tuv を作成して tu に追加
    tgt_seg = org_tu.target
    if tgt_seg is not None:
        tgt_tuv = make_tuv_from_seg(tgt_seg)
        tu.append(tgt_tuv)

    return tu


class TuIterator:
    """Iterator wrapper. `.failures` is available after iteration.

    Use as `for x in iter_tu_elements(...):`.
    """

    def __init__(
        self,
        tus: list[TU],
        include_locked: bool = False,
        batch_size: int | None = None,
        progress_callback: Callable | None = None,
        escape_markup: bool = True,
        document_name: str | None = None,
        client: str | None = None,
        project: str | None = None,
        domain: str | None = None,
        subject: str | None = None,
    ) -> None:
        """Initialize the iterator.

        Parameters
        ----------
        tus : list[TU]
            List of TUs.
        include_locked : bool, optional
            Whether to include locked TUs. Default is False.
        batch_size : int | None, optional
            Batch size. If None, yields one TU at a time.
        progress_callback : callable | None, optional
            Progress callback receiving (processed_count, skipped_count, error_count).
        escape_markup : bool, optional
            If True, escape markup within XLIFF and place it in `seg`.
        document_name : str | None, optional
            Value to forcefully specify the document name.
        client : str | None, optional
            Value to override the client property with.
        project : str | None, optional
            Value to override the project property with.
        domain : str | None, optional
            Value to override the domain property with.
        subject : str | None, optional
            Value to override the subject property with.

        """
        self.tus = tus
        self.include_locked = include_locked
        self.batch_size = batch_size
        self.progress_callback = progress_callback
        self.escape_markup = escape_markup
        self.failures: list[dict] = []
        self.document_name = document_name
        self.client = client
        self.project = project
        self.domain = domain
        self.subject = subject

    def __iter__(self) -> Iterator[etree.Element] | Iterator[list[etree.Element]]:
        """Return an iterator. Failures are accumulated to `.failures` during iteration."""
        processed = 0
        skipped = 0
        errors = 0
        batch: list[etree.Element] = []

        def _report():
            if self.progress_callback:
                try:
                    self.progress_callback(processed, skipped, errors)
                except Exception:
                    pass

        # 提供された TU リストを順に処理する
        try:
            iterator = iter(self.tus)
        except TypeError:
            raise TypeError('unsupported tus type')

        for item in iterator:
            try:
                tu = self._convert_from_item(item)
                if tu is None:
                    skipped += 1
                else:
                    processed += 1
                    if self.batch_size:
                        batch.append(tu)
                        if len(batch) >= self.batch_size:
                            _report()
                            yield batch[:]
                            batch.clear()
                    else:
                        _report()
                        yield tu
            except Exception as e:
                errors += 1
                # try to obtain an id for reporting
                tu_id = None
                try:
                    tu_id = getattr(item, 'id', None)
                    if tu_id is None and isinstance(item, dict):
                        tu_id = item.get('id')
                except Exception:
                    tu_id = None
                self.failures.append({'tu_id': tu_id, 'reason': str(e)})
        if self.batch_size and batch:
            _report()
            yield batch

    def _convert_from_item(self, item) -> etree.Element | None:
        return (
            convert_tu_to_element(
                item,
                include_locked=self.include_locked,
                escape_markup=self.escape_markup,
                document_name=self.document_name,
                client=self.client,
                project=self.project,
                domain=self.domain,
                subject=self.subject,
            )
        )


def iter_tu_elements(
    doc: XliffDocument,
    include_locked: bool = False,
    batch_size: int | None = None,
    progress_callback: Callable | None = None,
    escape_markup: bool = True,
    client: str | None = None,
    project: str | None = None,
    domain: str | None = None,
    subject: str | None = None,
) -> TuIterator:
    """Return an iterator that yields `<tu>` elements from a TU stream.

    Parameters
    ----------
    doc : XliffDocument
        The XliffDocument to convert.
    include_locked : bool, optional
        If True, include locked TUs (default False).
    batch_size : int | None, optional
        If None, yields one TU per iteration; if set, yields batches of that size.
    progress_callback : callable | None, optional
        Callback to receive progress as (processed_count, skipped_count, error_count).
    escape_markup : bool, optional
        If True, escape XLIFF markup when populating `seg` (recommended).
    client : str | None, optional
        Value to override the client property with.
    project : str | None, optional
        Value to override the project property with.
    domain : str | None, optional
        Value to override the domain property with.
    subject : str | None, optional
        Value to override the subject property with.

    Returns
    -------
    TuIterator
        An iterable iterator. After iteration, see `.failures` for failures.
    """
    return TuIterator(
        tus=doc.tus,
        include_locked=include_locked,
        batch_size=batch_size,
        progress_callback=progress_callback,
        escape_markup=escape_markup,
        document_name=doc.document_name,
        client=client,
        project=project,
        domain=domain,
        subject=subject,
    )


def convert_xliffdoc_to_tmx(
    doc: XliffDocument,
    out_path: Path,
    include_locked: bool = False
) -> None:
    """Convert an entire XliffDocument to TMX.

    Parameters
    ----------
    doc : XliffDocument
        XliffDocument to convert.
    out_path : Path
        Output path for the generated TMX file.
    include_locked : bool, optional
        If True, include locked TUs (default False).

    Returns
    -------
    etree.Element
        TMX root element after conversion.
    """
    # イテレータ
    it = iter_tu_elements(doc, include_locked=include_locked, escape_markup=True)

    # tmxkit の import を試みる。見つからない場合は導入手順を案内する。
    try:
        from tmxkit.io.writer import write_tu_stream
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            'tmxkit is not installed in the current environment. '
            'Try `pip install tmxkit`. If that does not resolve the issue, '
            'obtain and install the source from: https://github.com/ikuehirata/tmxkit'
        ) from e

    write_tu_stream(it, header_path=None, out_path=out_path)
