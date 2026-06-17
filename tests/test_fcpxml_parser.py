"""Tests for FCPXML parser."""

from pathlib import Path
from deepworld.parsers import ParserRegistry

SAMPLES = Path(__file__).parent.parent / "samples"
SAMPLE_FCPXML = SAMPLES / "sample_fcpxml.fcpxml"


class TestFCPXMLParser:
    def setup_method(self):
        self.parser = ParserRegistry.get_parser(SAMPLE_FCPXML)

    def test_parser_type(self):
        assert "FCPXML" in self.parser.format_name()

    def test_parse_clips(self):
        proj = self.parser.parse(SAMPLE_FCPXML)
        assert proj.clip_count() >= 2

    def test_parse_timeline(self):
        proj = self.parser.parse(SAMPLE_FCPXML)
        assert len(proj.timelines) >= 1

    def test_clip_names(self):
        proj = self.parser.parse(SAMPLE_FCPXML)
        names = []
        for tl in proj.timelines:
            for t in tl.tracks:
                for c in t.clips:
                    names.append(c.clip_name)
        assert any("Sunrise" in n for n in names)

    def test_timecodes(self):
        proj = self.parser.parse(SAMPLE_FCPXML)
        for tl in proj.timelines:
            for t in tl.tracks:
                for c in t.clips:
                    if c.source_in and c.source_out:
                        assert c.source_out.total_frames > c.source_in.total_frames

    def test_parse_source_file(self):
        proj = self.parser.parse(SAMPLE_FCPXML)
        sources = []
        for tl in proj.timelines:
            for t in tl.tracks:
                for c in t.clips:
                    if c.source_file:
                        sources.append(c.source_file)
        assert any("Sunrise" in s for s in sources)
