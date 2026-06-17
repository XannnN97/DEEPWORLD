"""Integration tests for converter pipeline."""

from pathlib import Path
import tempfile
from deepworld.converter import ConvertPipeline

SAMPLES = Path(__file__).parent.parent / "samples"


class TestConvertPipeline:
    def test_parse_edl(self):
        project = ConvertPipeline.parse(SAMPLES / "sample_cmx3600.edl")
        assert project is not None
        assert project.clip_count() > 0

    def test_parse_srt(self):
        project = ConvertPipeline.parse(SAMPLES / "sample_subtitle.srt")
        assert project is not None
        assert project.clip_count() > 0

    def test_parse_fcpxml(self):
        project = ConvertPipeline.parse(SAMPLES / "sample_fcpxml.fcpxml")
        assert project is not None
        assert project.clip_count() >= 2

    def test_parse_resolve(self):
        project = ConvertPipeline.parse(SAMPLES / "sample_resolve.xml")
        assert project is not None
        assert project.clip_count() >= 3

    def test_edl_to_csv_roundtrip(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            out = Path(f.name)
        try:
            result = ConvertPipeline.convert(SAMPLES / "sample_cmx3600.edl", out, verbose=False)
            assert result.exists()
            assert result.stat().st_size > 0
        finally:
            out.unlink(missing_ok=True)

    def test_srt_to_csv(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            out = Path(f.name)
        try:
            result = ConvertPipeline.convert(SAMPLES / "sample_subtitle.srt", out, verbose=False)
            assert result.exists()
        finally:
            out.unlink(missing_ok=True)

    def test_srt_to_excel(self):
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            out = Path(f.name)
        try:
            result = ConvertPipeline.convert(SAMPLES / "sample_subtitle.srt", out, verbose=False)
            assert result.exists()
        finally:
            out.unlink(missing_ok=True)

    def test_srt_to_word(self):
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            out = Path(f.name)
        try:
            result = ConvertPipeline.convert(SAMPLES / "sample_subtitle.srt", out, verbose=False)
            assert result.exists()
        finally:
            out.unlink(missing_ok=True)
