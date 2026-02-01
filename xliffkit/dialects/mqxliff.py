"""memoQ XLIFF (mqXLIFF) dialect definition"""
from typing import cast

import lxml.etree as etree

from ..core.models import TU
from .base import Dialect, State


class MQXLIFF(Dialect):
    """memoQ XLIFF dialect definition."""

    name = 'mqxliff'
    inline_tags = {'ph', 'bpt', 'ept', 'g', 'it', 'x'}
    preserve_context = True
    preserve_tu_attrs = True
    include_context_in_yaml = True

    TEXT_CONTAINER_TAGS = {
        'source',
        'target',
    }
    '''Tags treated as text within source/target'''

    preserve_versioninfos = True
    roundtrip_safe = False

    # -----------------------------
    # Attribute definitions
    # -----------------------------
    KNOWN_ATTRIBUTES = {
        'id',
        'rid',
        'state',
        'approved',
        'wb:name',
    }
    '''memoQ-specific attributes that are nice to have'''

    # -----------------------------
    # memoQ quirks (encoded)
    # -----------------------------
    PH_CONTAINS_ESCAPED_XML = True
    '''ph contents are often escaped tag strings'''

    BPT_EPT_ARE_FORMATTING = True
    '''bpt / ept are often used for formatting purposes'''

    INLINE_TAG_POSITION_IS_APPROXIMATE = True
    '''inline tag order may differ from the logical text order'''

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
        file_elm = root.find('.//{*}file')
        # file_elm 内の要素を辞書にする
        metadata = {}
        if file_elm is not None:
            for key, val in file_elm.attrib.items():
                metadata[key] = val
        return metadata


    def extend_stream_dict(self, tu: TU) -> dict[str, str]:
        """Extend the output dict of iter_tus.

        memoQ adds the following:
          - Segment lock state
          - context_id: If present, the context attribute value of context-group / context
        """
        extra = {}

        # セグメントのロック状態
        state_locked = self.get_attr_by_local_name(tu.extra_attrs, 'locked')
        if state_locked is not None and state_locked == 'locked':
            extra['locked'] = True
        else:
            extra['locked'] = False

        context_id = self.get_context_id(tu.raw_xml)
        if context_id is not None and context_id != '':
            extra['context_id'] = context_id

        return extra

    def normalize_state(
            self, raw_state: str, extra_attrs: dict[str, str]
    ) -> State:
        """Normalize memoQ-specific state attribute."""
        mapping = {
            'NotStarted': 'new',
            'Edited': 'needs-review-translation',
            'PreTranslated': 'translated',
            'Confirmed': 'final',
            'ManuallyConfirmed': 'final',
        }
        mq_status = self.get_attr_by_local_name(extra_attrs, 'status')
        if mq_status:
            return cast(State, mapping.get(mq_status, 'new'))

        return cast(State, raw_state)

    def get_context_id(self, elem: etree.Element) -> str | None:
        """Normalize memoQ-specific state attribute."""
        if elem is None:
            return None
        for child in elem:
            tag = child.tag
            if isinstance(tag, str) and tag.startswith('{'):
                tag = tag.split('}', 1)[1]
            if tag == 'context' and child.attrib.get('context-type') == 'x-mmq-context':
                return child.text

        return None
