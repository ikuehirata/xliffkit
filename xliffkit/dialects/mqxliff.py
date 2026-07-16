"""memoQ XLIFF (mqXLIFF) dialect definition"""
import logging
from typing import Any, cast

import lxml.etree as etree

from ..core.models import TU
from .base import Dialect, State

logger = logging.getLogger(__name__)

STATE_MAPPING = {
    'NotStarted': 'needs-translation',
    'Edited': 'needs-review-translation',
    'PartiallyEdited': 'needs-review-translation',
    'MachineTranslated': 'needs-review-translation',
    'PreTranslated': 'needs-review-translation',
    'Confirmed': 'translated',  # TODO これって存在する？
    'ManuallyConfirmed': 'translated',
    'Reviewer1Confirmed': 'signed-off',
    'Proofread': 'final',
}


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


    def extend_stream_dict(self, tu: TU) -> dict[str, Any]:
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

        cg = None
        if tu.raw_xml is not None:
            for child in tu.raw_xml:
                if etree.QName(child).localname == 'context-group':
                    cg = child
                    break
        context_id = self.get_context_id(cg)
        if context_id is not None and context_id != '':
            extra['context_id'] = context_id

        return extra

    def get_state(self, elem: etree.Element) -> State:
        """Normalize memoQ-specific state attribute."""
        for k, v in elem.attrib.items():
            if 'status' in k:
                xliff_state = STATE_MAPPING.get(v, 'needs-translation')
                return cast(State, xliff_state)

        logger.warning(
            'mqXLIFF: no state attribute found for TU %s.', elem.attrib.get('id'))
        return 'needs-translation'

    def get_context_id(self, elem: etree.Element) -> str | None:
        """Normalize memoQ-specific context attribute."""
        if elem is None:
            # print('elem is None')  # TODO なんか対処が必要
            return None
        for child in elem:
            tag = child.tag
            if isinstance(tag, str) and tag.startswith('{'):
                tag = tag.split('}', 1)[1]
            if tag == 'context' and child.attrib.get('context-type') == 'x-mmq-context':
                return child.text

        return None

    def is_locked(self, elem: etree.Element) -> bool:
        """Check if the TU is locked based on memoQ-specific attributes."""
        for k, v in elem.attrib.items():
            if 'locked' in k.lower() and 'locked' in v.lower():
                return True

        return False
