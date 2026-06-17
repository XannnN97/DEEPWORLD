"""Tests for SRT parser."""

from pathlib import Path
from deepworld.parsers import ParserRegistry
from deepworld.core.enums import TrackType

SAMPLES = Path(__file__).parent.parent / "samples"
SAMPLE_SRT = SAMPLES / "sample_subtitle.srt"


class TestSRTParser:
    def setup_method(self):
        self.parser = ParserRegistry.get_parser(SAMPLE_SRT)

    def test_parser_type(self):
        assert "SRT" in self.parser.format_name()

    def test_parse_clip_count(self):
        proj = self.parser.parse(SAMPLE_SRT)
        assert proj.clip_count() == 5

    def test_parse_timeline(self):
        proj = self.parser.parse(SAMPLE_SRT)
        assert len(proj.timelines) == 1

    def test_subtitle_track(self):
        proj = self.parser.parse(SAMPLE_SRT)
        track = proj.timelines[0].tracks[0]
        assert track.track_type == TrackType.SUBTITLE

    def test_text_content(self):
        proj = self.parser.parse(SAMPLE_SRT)
        clip = proj.timelines[0].tracks[0].clips[0]
        assert "welcome" in clip.clip_name.lower()

    def test_timecodes(self):
        proj = self.parser.parse(SAMPLE_SRT)
        clip = proj.timelines[0].tracks[0].clips[0]
        assert clip.record_in is not None
        assert clip.record_out is not None
        assert clip.record_out.total_frames > clip.record_in.total_frames

    def test_chinese_text(self):
        proj = self.parser.parse(SAMPLE_SRT)
        clips = proj.timelines[0].tracks[0].clips
        last = clips[-1]
        assert len(last.clip_name) > 0
