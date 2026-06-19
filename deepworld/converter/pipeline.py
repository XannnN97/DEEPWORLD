"""Converter pipeline — orchestrate parse → model → export."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

from ..core.model import UnifiedProject
from ..parsers import ParserRegistry, ParseError
from ..exporters import ExporterRegistry, ExportError


class ConvertPipeline:
    @staticmethod
    def parse(input_path: Path | str, framerate: Fraction | None = None) -> UnifiedProject:
        path = Path(input_path)
        if not path.exists():
            raise ParseError(f"File not found: {path}")
        parser = ParserRegistry.get_parser(path)
        if framerate is not None and hasattr(parser, "default_framerate"):
            parser.default_framerate = framerate
        return parser.parse(path)

    @staticmethod
    def export(project: UnifiedProject, output_path: Path | str) -> Path:
        path = Path(output_path)
        exporter = ExporterRegistry.get_exporter(path)
        return exporter.export(project, path)

    @staticmethod
    def convert(
        input_path: Path | str,
        output_path: Path | str | None = None,
        verbose: bool = False,
        framerate: Fraction | None = None,
    ) -> Path:
        input_path = Path(input_path)
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_report.docx"

        if verbose:
            fr_str = f" @ {float(framerate):.3f}fps" if framerate else ""
            print(f"Parsing: {input_path}{fr_str}")

        project = ConvertPipeline.parse(input_path, framerate=framerate)

        if verbose:
            tc = project.clip_count()
            print(f"  Parsed: {len(project.timelines)} timeline(s), {tc} clip(s)")

        result = ConvertPipeline.export(project, output_path)

        if verbose:
            print(f"  Exported: {result}")

        return result
