"""Exporter system — BaseExporter abstract class + ExporterRegistry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..core.model import UnifiedProject


class ExportError(Exception):
    """Raised when an exporter cannot write output."""


class BaseExporter(ABC):
    """All exporters inherit from BaseExporter and register themselves."""

    @classmethod
    @abstractmethod
    def format_name(cls) -> str:
        """Human-readable name, e.g. 'Microsoft Word (docx)'."""

    @classmethod
    @abstractmethod
    def file_extension(cls) -> str:
        """File extension this exporter produces, e.g. '.docx'."""

    @abstractmethod
    def export(self, project: UnifiedProject, output_path: Path) -> Path:
        """Write file. Returns output_path for chaining."""


class ExporterRegistry:
    _exporters: dict[str, type[BaseExporter]] = {}

    @classmethod
    def register(cls, exporter_cls: type[BaseExporter]) -> None:
        cls._exporters[exporter_cls.file_extension().lower()] = exporter_cls

    @classmethod
    def get_exporter(cls, ext_or_path: Path | str) -> BaseExporter:
        path = Path(ext_or_path) if isinstance(ext_or_path, str) else ext_or_path
        ext = path.suffix.lower()
        if ext not in cls._exporters:
            raise ExportError(f"No exporter for format: {ext}")
        return cls._exporters[ext]()

    @classmethod
    def list_extensions(cls) -> list[str]:
        return list(cls._exporters.keys())

    @classmethod
    def list_format_names(cls) -> list[str]:
        return [p.format_name() for p in cls._exporters.values()]
