"""Module defining the generic XLIFF dialect."""
from .base import Dialect


class GenericXLIFF(Dialect):
    """Generic XLIFF dialect definition."""

    name = 'generic'

    inline_tags = {'ph', 'g'}
    preserve_tu_attrs = False
    preserve_versioninfos = False
    roundtrip_safe = False
