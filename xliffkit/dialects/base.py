"""XLIFF basic dialect definition module."""
import lxml.etree as etree


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

    def normalize_state(self, raw_state: str, attrs: dict[str, str]) -> str:
        """Normalize the state attribute."""
        return raw_state

    def get_context_id(self, elem: etree.Element) -> str | None:
        """Get context_id from context_xml."""
        return None
