"""Dataclasses for TU / Segment / Tag

- Dataclass definitions that hold the minimal information required for XLIFF.
- Shared by parser, serializer, and YAML processing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import lxml.etree as etree


@dataclass
class InlineTag:
    """Inline tag information inside an XLIFF file.

    Stores only the minimal fields necessary for readability improvements,
    normalization, and reconstruction.
    """

    tag: str
    '''Tag name (e.g., ph, bpt, ept, it, ...)'''
    tag_id: str
    '''ID'''
    raw_inner: str | None = None
    '''String inside <*>...</*>'''
    tag_rid: str | None = None
    '''rid attribute (if present)'''
    position: int = -1
    '''Position of appearance in text (after flattening).

    Not exact; used as a reference for split/merge.'''

@dataclass
class Segment:
    """One side of a TU: either `source` or `target`.

    The minimal unit for split processing.

    Attributes
    ----------
    text : str
        Flattened text. May be destructively modified by the parser.
    inline_tags : list[InlineTag]
        List of inline tags contained in the segment.
    lang : str | None
        Language code for the segment, set if the parser provides it.
    tmx_text : str | None
        Original source text for TMX match calculations and reconstruction
        (includes invisible characters).
    raw_xml : etree.Element | None
        Raw XML of the segment, set by the parser if available.
        Used as a fallback if serialization fails.
    flattened_text : str | None
        Text after flattening (includes invisible characters).
        Used only during flattening.

    Methods
    -------
    is_empty() -> bool
        Whether the text is empty.
    """

    text: str
    '''Plain text after flattening. May be destructively modified by the parser.'''
    inline_tags: list[InlineTag] = field(default_factory=list)
    '''List of inline tags within the segment.'''
    lang: str | None = None
    '''Language code of the segment. Set if the parser can obtain it.'''
    raw_xml: etree.Element | None = None
    '''Raw XML of the segment. Set by the parser if available.
    Used as a fallback if the serializer fails.'''
    tmx_text: str | None = None
    '''Original source text for TMX match calculations
    and reconstruction (includes invisible characters).'''
    flattened_text: str | None = None
    '''Text after flattening (includes invisible characters). Used only during flattening.'''

    def is_empty(self) -> bool:
        """Return whether the text is empty."""
        return not self.text.strip()

    def with_text(self, text: str) -> Segment:
        """Return a new Segment with `text` replaced."""
        return Segment(
            text=text,
            inline_tags=self.inline_tags,
            flattened_text=self.text,
            tmx_text=self.tmx_text,
            lang=self.lang,
            raw_xml=self.raw_xml,
        )

    def with_flattened_text(self, flattened_text: str) -> Segment:
        """Return a new Segment with `flattened_text` replaced."""
        return Segment(
            text=self.text,
            inline_tags=self.inline_tags,
            flattened_text=flattened_text,
            tmx_text=self.tmx_text,
            lang=self.lang,
            raw_xml=self.raw_xml,
        )

    def with_inline_tags(self, inline_tags: list[InlineTag]) -> Segment:
        """Return a new Segment with `inline_tags` replaced."""
        return Segment(
            text=self.text,
            inline_tags=inline_tags,
            flattened_text=self.flattened_text,
            tmx_text=self.tmx_text,
            lang=self.lang,
            raw_xml=self.raw_xml,
        )

@dataclass
class TU:
    """Equivalent to an XLIFF trans-unit."""

    tu_id: str
    '''ID of the translation unit, starting from 1.'''

    source: Segment
    target: Segment | None = None

    context_id: str | None = None
    '''Context ID'''

    state: Literal[
        'new',
        'needs-review-translation',
        'translated',
        'final'
    ] = 'new'
    '''翻訳状態'''
    comment: str | None = None
    '''Comment from the tool'''

    order: int = -1
    '''Appearance order in the original file. Used for reconstruction and debugging.'''

    extra_attrs: dict[str, str] = field(default_factory=dict)
    '''Tool-specific attributes picked up by the parser. Used by the serializer for restoration.'''

    raw_xml: etree.Element | None = None
    '''Raw XML of the entire trans-unit.

    Not aiming for perfect restoration, but kept as a fallback.'''

    def has_target(self) -> bool:
        """Return whether a target exists and is non-empty."""
        return self.target is not None and not self.target.is_empty()

    def with_segments(
        self,
        source: Segment,
        target: Segment | None,
    ) -> TU:
        """Return a new TU with the source and target replaced.

        Parameters
        ----------
        source : Segment
            Source segment to replace
        target : Segment | None
            Target segment to replace

        Returns
        -------
        TU
            The new TU with replacements
        """
        return TU(
            tu_id=self.tu_id,
            source=source,
            target=target,
            context_id=self.context_id,
            state=self.state,
            comment=self.comment,
            order=self.order,
            extra_attrs=self.extra_attrs,
            raw_xml=self.raw_xml,
        )


@dataclass
class XliffDocument:
    """Container for a single XLIFF file."""

    tus: list[TU]

    from ..dialects.base import Dialect
    dialect: Dialect = field(default_factory=Dialect)
    '''Dialect information for this document'''

    source_lang: str | None = None
    target_lang: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)
    '''File, project, tool version, etc. Contents depend on the parser.'''

    raw_xml: etree.Element | None = None
    '''Raw XML of the entire file. Generally not used, but kept as a fallback.'''

    def with_tus(self, tus: list[TU]) -> XliffDocument:
        """Return a new XliffDocument with `tus` replaced."""
        return XliffDocument(
            tus=tus,
            dialect=self.dialect,
            source_lang=self.source_lang,
            target_lang=self.target_lang,
            metadata=self.metadata,
            raw_xml=self.raw_xml,
        )

    def reorder_tu_id(self) -> XliffDocument:
        """Return a new XliffDocument with `tu_id` reassigned in appearance order."""
        new_tus = []
        for index, tu in enumerate(self.tus, start=1):
            tu.tu_id = str(index)
            new_tus.append(tu)
        return self.with_tus(new_tus)
