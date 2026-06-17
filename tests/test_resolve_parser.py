"""Tests for DaVinci Resolve XML parser."""

from pathlib import Path
from deepworld.parsers import ParserRegistry

SAMPLES = Path(__file__).parent.parent / "samples"
SAMPLE_RESOLVE = SAMPLES / "sample_resolve.xml"


class TestResolveXMLParser:
    def setup_method(self):
        self.parser = ParserRegistry.get_parser(SAMPLE_RESOLVE)

    def test_parser_type(self):
        assert "Resolve" in self.parser.format_name() or "XML" in self.parser.format_name()

    def test_parse_clips(self):
        proj = self.parser.parse(SAMPLE_RESOLVE)
        assert proj.clip_count() >= 3

    def test_parse_timeline(self):
        proj = self.parser.parse(SAMPLE_RESOLVE)
        assert len(proj.timelines) == 1

    def test_video_track(self):
        proj = self.parser.parse(SAMPLE_RESOLVE)
        tl = proj.timelines[0]
        video_tracks = [t for t in tl.tracks if "Video" in t.name]
        assert len(video_tracks) >= 1

    def test_audio_track(self):
        proj = self.parser.parse(SAMPLE_RESOLVE)
        tl = proj.timelines[0]
        audio_tracks = [t for t in tl.tracks if "Audio" in t.name]
        assert len(audio_tracks) >= 1

    def test_clip_names(self):
        proj = self.parser.parse(SAMPLE_RESOLVE)
        names = [c.clip_name for tl in proj.timelines for t in tl.tracks for c in t.clips]
        assert any("Opening" in n for n in names)
        assert any("Interview" in n for n in names)

    def test_timecodes(self):
        proj = self.parser.parse(SAMPLE_RESOLVE)
        for tl in proj.timelines:
            for t in tl.tracks:
                for c in t.clips:
                    if c.record_in is not None and c.record_out is not None:
                        assert c.record_out.total_frames >= c.record_in.total_frames
