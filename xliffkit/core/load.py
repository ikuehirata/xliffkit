"""xliff file loader that reads, fixes, normalizes, and returns an XliffDocument."""
from ..core.models import XliffDocument
from ..dialects import detect
from ..normalize import flatten, tags
from .internal.xml_parser import parse_xliff


def load(path: str, roundtrip: bool = False) -> XliffDocument:
    """Load an XLIFF file, fix and normalize it, and return an XliffDocument.

    Parameters
    ----------
    path : str
        Path to the XLIFF file to be loaded.
    roundtrip : bool
        Whether to operate in a mode intended for re-importing.

    Returns
    -------
    XliffDocument
        Internal representation of the loaded XLIFF.
    """
    # dialect判定
    dialect = detect.detect_dialect_from_filename(path, roundtrip=roundtrip)

    # 純粋パース
    doc = parse_xliff(path, dialect=dialect)

    # 修正と正規化
    doc = tags.normalize_all_tags(doc)
    doc = flatten.flatten_all_segments(doc)
    # flatten 後に空白正規化を行う
    doc = flatten.normalize_whitespace_all_segments(doc)
    return doc
