"""Parser system — BaseParser abstract class + ParserRegistry auto-discovery."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ..core.model import UnifiedProject


class ParseError(Exception):
    """Raised when a parser cannot process the input file."""


class BaseParser(ABC):
    """All parsers inherit from BaseParser and register themselves."""

    @classmethod
    @abstractmethod
    def format_name(cls) -> str:
        """Human-readable name, e.g. 'CMX3600 EDL'."""
        ...

    @classmethod
    @abstractmethod
    def file_extensions(cls) -> list[str]:
        """List of file extensions this parser handles, e.g. ['.edl']."""
        ...

    @classmethod
    def can_parse(cls, file_path: Path) -> bool:
        """Heuristic detection — override for format-specific magic-byte checks."""
        ext = file_path.suffix.lower()
        return ext in cls.file_extensions()

    @abstractmethod
    def parse(self, file_path: Path) -> UnifiedProject:
        """Parse file into the unified model. Raises ParseError on failure."""
        ...


class ParserRegistry:
    _parsers: dict[str, type[BaseParser]] = {}

    @classmethod
    def register(cls, parser_cls: type[BaseParser]) -> None:
        for ext in parser_cls.file_extensions():
            cls._parsers[ext.lower()] = parser_cls

    @classmethod
    def get_parser(cls, file_path: Path | str) -> BaseParser:
        path = Path(file_path)
        ext = path.suffix.lower()

        # 1. Try exact extension match
        if ext in cls._parsers:
            return cls._parsers[ext]()

        # 2. Try heuristic can_parse() on all registered parsers
        for parser_cls in cls._parsers.values():
            if parser_cls.can_parse(path):
                return parser_cls()

        raise ParseError(f"No parser found for: {path.name}")

    @classmethod
    def list_extensions(cls) -> list[str]:
        return list(cls._parsers.keys())

    @classmethod
    def list_format_names(cls) -> list[str]:
        names = set()
        for p in cls._parsers.values():
            names.add(p.format_name())
        return sorted(names)
