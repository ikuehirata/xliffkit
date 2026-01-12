"""xliffkit.core

`core` package aggregates internal data models (TU / Segment / InlineTag / XliffDocument),
parsers/serializers, and dialect definitions.

It re-exports lightweight types and main submodules from the top level.
"""

from __future__ import annotations

from . import load
from .internal import xml_parser
from .models import TU, InlineTag, Segment, XliffDocument
from .serializer import plain

__all__ = [
	'load',
	'TU', 'Segment', 'InlineTag', 'XliffDocument',
	'xml_parser', 'plain',
]
