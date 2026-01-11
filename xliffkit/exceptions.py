"""Project-wide exception definitions."""


class MergeError(Exception):
    """Raised when a merge operation fails.

    Due to invalid input or internal inconsistency.

    This is the recommended exception to be used by ``segment.merge``.
    """

    pass
