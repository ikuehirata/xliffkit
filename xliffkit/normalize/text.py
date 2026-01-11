"""Text normalization utilities"""

import re

from ..core.models import XliffDocument


def normalize_text_segment(text: str) -> str:
    r"""Normalize text within a segment.

    - Normalize consecutive whitespace
        - \u00A0 (NBSP) -> ' '
        - \t -> ' '
    - Remove zero-width characters
        - \u200b etc.
    - Handling of leading/trailing whitespace
        - Whether to call .strip() is policy-dependent
    - Remove invisible junk from memoQ/CAT
        - Items that may be introduced by copy & paste

    Parameters
    ----------
    text : str
        Text to normalize

    Returns
    -------
    str
        Normalized text
    """
    if not text:
        return text

    # 改行コード統一
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # NBSP → space
    text = text.replace('\u00A0', ' ')
    # ゼロ幅文字除去
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)

    return text


def normalize_all_texts(doc: XliffDocument) -> XliffDocument:
    r"""Destructive operation that normalizes the text of all source/target

    Parameters
    ----------
    doc : XliffDocument
        XLIFF document to normalize

    Returns
    -------
    XliffDocument
        Normalized XLIFF document
    """
    new_tus = []
    for tu in doc.tus:
        new_source = tu.source.with_text(
            normalize_text_segment(tu.source.text)
        )
        if tu.target is not None:
            new_target = tu.target.with_text(
                normalize_text_segment(tu.target.text)
            )
        else:
            new_target = None
        new_tus.append(tu.with_segments(source=new_source, target=new_target))

    return doc.with_tus(new_tus)
