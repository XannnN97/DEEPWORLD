"""Parser registry — importing each parser module triggers self-registration."""

# Import parsers so they register themselves
from . import edl_parser
from . import srt_parser
from . import fcpxml_parser
from . import resolve_parser

from .base import BaseParser, ParserRegistry, ParseError

__all__ = ["BaseParser", "ParserRegistry", "ParseError"]
