"""CLI entry point: python -m deepworld [--web|input -o output]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        prog="python -m deepworld",
        description="DEEPWORLD — Film media intermediate file converter",
    )
    parser.add_argument("input", nargs="?", help="Input file (.edl/.srt/.fcpxml/.xml)")
    parser.add_argument("-o", "--output", help="Output file path (extension selects format)")
    parser.add_argument(
        "-f", "--format", choices=["docx", "xlsx", "csv"],
        help="Output format (overrides extension detection)",
    )
    parser.add_argument("--web", action="store_true", help="Start web UI server")
    parser.add_argument("--port", type=int, default=8090, help="Web server port")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--list-formats", action="store_true", help="List supported formats")

    args = parser.parse_args()

    if args.list_formats:
        from .parsers import ParserRegistry
        from .exporters import ExporterRegistry
        print("Input formats:")
        for name in ParserRegistry.list_format_names():
            print(f"  - {name}")
        print("Output formats:")
        for name in ExporterRegistry.list_format_names():
            print(f"  - {name}")
        return

    if args.web:
        from .web.server import start_server
        start_server(host="127.0.0.1", port=args.port)
        return

    if not args.input:
        parser.print_help()
        sys.exit(1)

    from .converter import ConvertPipeline

    output = args.output
    if not output and args.format:
        input_path = Path(args.input)
        output = str(input_path.parent / f"{input_path.stem}_report.{args.format}")

    ConvertPipeline.convert(Path(args.input), output, verbose=args.verbose)


if __name__ == "__main__":
    main()
