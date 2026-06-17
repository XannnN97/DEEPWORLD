"""Tests for CSV exporter."""

from pathlib import Path
import csv
import tempfile
from deepworld.parsers import ParserRegistry
from deepworld.exporters import ExporterRegistry

SAMPLES = Path(__file__).parent.parent / "samples"
SAMPLE_EDL = SAMPLES / "sample_cmx3600.edl"


class TestCsvExporter:
    def setup_method(self):
        self.parser = ParserRegistry.get_parser(SAMPLE_EDL)
        self.exporter = ExporterRegistry.get_exporter(Path("test.csv"))
        self.project = self.parser.parse(SAMPLE_EDL)

    def test_exporter_type(self):
        assert "CSV" in self.exporter.format_name()

    def test_export_creates_file(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = Path(f.name)
        try:
            result = self.exporter.export(self.project, path)
            assert result.exists()
            assert result.stat().st_size > 0
        finally:
            path.unlink(missing_ok=True)

    def test_export_has_header(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = Path(f.name)
        try:
            self.exporter.export(self.project, path)
            with open(path, encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                header = next(reader)
                assert "Clip Name" in header
                assert "Record In" in header
        finally:
            path.unlink(missing_ok=True)

    def test_export_has_data(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = Path(f.name)
        try:
            self.exporter.export(self.project, path)
            with open(path, encoding="utf-8-sig") as f:
                rows = list(csv.reader(f))
                assert len(rows) > 1  # Header + data rows
        finally:
            path.unlink(missing_ok=True)
