"""Module defining the base XLIFF dialect."""
from typing import cast

import lxml.etree as etree

from ..core.models import _ALLOWED_STATES, State


class Dialect:
    """Base class for XLIFF dialects.

    Subclass for each dialect.

    Attributes
    ----------
    name : str
        Dialect name
    inline_tags : set[str]
        Element names treated as inline tags
    preserve_context : bool
        Preserve context-group / context
    preserve_tu_attrs : bool
        Preserve TU attributes
    preserve_versioninfos : bool
        Preserve file header information
    roundtrip_safe : bool
        Whether to assume round-trip
    """

    name: str
    '''Dialect name'''

    inline_tags: set[str]
    '''Element names treated as inline tags'''
    preserve_context: bool
    '''Preserve context-group / context'''

    preserve_tu_attrs: bool
    '''Preserve TU attributes'''

    preserve_versioninfos: bool
    '''Preserve file header information'''

    roundtrip_safe: bool
    '''Whether to assume round-trip'''

    def __init__(self, *, roundtrip: bool = False) -> None:
        """Initialize the dialect.

        Parameters
        ----------
        roundtrip : bool
            Whether to operate in a mode intended for re-importing.
        """
        self.roundtrip_safe = roundtrip

    def extract_metadata(self, root: etree.Element) -> dict[str, str]:
        """Extract metadata to be stored in XliffDocument.metadata.

        Parameters
        ----------
        root : ET.Element
            xliff root element
        file_elm : ET.Element | None
            xliff file element. May be None.

        Returns
        -------
        dict[str, str]
            Extracted metadata dictionary
        """
        return {}

    def get_attr_by_local_name(self, attrs: dict[str, str], local_name: str) -> str | None:
        """Get attribute value by local name from attribute dictionary."""
        for k, v in attrs.items():
            # namespace付き: {xxx}status
            if k.endswith(f'}}{local_name}'):
                return v
            # 念のため namespace無し
            if k == local_name:
                return v
        return None

    def extend_stream_dict(self, tu) -> dict[str, str]:
        """Extend the output dict of iter_tus.

        Additional TU information can be added as needed.
        """
        return {}

    def get_state(self, elem: etree.Element) -> State:
        """Get the state of a TU from the XML element."""
        raw_state = elem.attrib.get('state', 'new')
        if raw_state in _ALLOWED_STATES:
            return cast(State, raw_state)
        return 'new'

    def get_context_id(self, elem: etree.Element) -> str | None:
        """Get the context_id from the context_xml element."""
        # context-group を探す
        for child in elem:
            if 'context-group' in child.tag:
                return child
        return None

    def is_locked(self, elem: etree.Element) -> bool:
        """Check if the TU is locked based on attributes."""
        return False
