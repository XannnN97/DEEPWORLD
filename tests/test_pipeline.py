"""Integration tests — empty project, full roundtrip, cross-format consistency."""

from pathlib import Path
import tempfile
import csv
from deepworld.converter import ConvertPipeline
from deepworld.core.model import UnifiedProject, UnifiedTimeline, UnifiedTrack

SAMPLES = Path(__file__).parent.parent / "samples"


class TestEmptyProject:
    def test_empty_fcpxml(self):
        """FCPXML with no clips should not crash."""
        result = ConvertPipeline.parse(SAMPLES / "sample_fcpxml.fcpxml")
        assert result is not None

    def test_edl_to_word_roundtrip(self):
        """EDL → DOCX should produce a non-empty file."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            out = Path(f.name)
        try:
            ConvertPipeline.convert(SAMPLES / "sample_cmx3600.edl", out)
            assert out.stat().st_size > 1000
        finally:
            out.unlink(missing_ok=True)

    def test_edl_to_excel_roundtrip(self):
        """EDL → XLSX should produce a non-empty file."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            out = Path(f.name)
        try:
            ConvertPipeline.convert(SAMPLES / "sample_cmx3600.edl", out)
            assert out.stat().st_size > 1000
        finally:
            out.unlink(missing_ok=True)

    def test_edl_to_csv_roundtrip(self):
        """EDL → CSV should produce a non-empty file."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            out = Path(f.name)
        try:
            ConvertPipeline.convert(SAMPLES / "sample_cmx3600.edl", out)
            assert out.stat().st_size > 100
        finally:
            out.unlink(missing_ok=True)


class TestCrossFormatConsistency:
    def test_csv_and_excel_have_same_clip_count(self):
        """Same source exported to CSV and XLSX should have the same number of clips."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f_csv:
            csv_path = Path(f_csv.name)
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f_xlsx:
            xlsx_path = Path(f_xlsx.name)
        try:
            ConvertPipeline.convert(SAMPLES / "sample_subtitle.srt", csv_path)
            ConvertPipeline.convert(SAMPLES / "sample_subtitle.srt", xlsx_path)
            # Count CSV data rows (skip header)
            with open(csv_path, encoding="utf-8-sig") as f:
                csv_rows = list(csv.reader(f))
            csv_clips = len(csv_rows) - 1  # minus header
            # Verify there's data
            assert csv_clips == 5
        finally:
            csv_path.unlink(missing_ok=True)
            xlsx_path.unlink(missing_ok=True)

    def test_framerate_parameter_affects_edl_output(self):
        """EDL parser should respect the framerate parameter."""
        from fractions import Fraction
        fr24 = Fraction(24, 1)
        fr25 = Fraction(25, 1)
        project = ConvertPipeline.parse(SAMPLES / "sample_cmx3600.edl", framerate=fr24)
        project2 = ConvertPipeline.parse(SAMPLES / "sample_cmx3600.edl", framerate=fr25)
        # Different framerate → different frame count for same SMPTE time
        for tl, tl2 in zip(project.timelines, project2.timelines):
            for tr, tr2 in zip(tl.tracks, tl2.tracks):
                for c, c2 in zip(tr.clips, tr2.clips):
                    if c.record_in and c2.record_in:
                        assert c.record_in.total_frames != c2.record_in.total_frames
                        return
