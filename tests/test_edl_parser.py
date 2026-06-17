"""Tests for EDL parser."""

from pathlib import Path
from deepworld.parsers import ParserRegistry
from deepworld.core.enums import TrackType

SAMPLES = Path(__file__).parent.parent / "samples"
SAMPLE_EDL = SAMPLES / "sample_cmx3600.edl"


class TestEDLParser:
    def setup_method(self):
        self.parser = ParserRegistry.get_parser(SAMPLE_EDL)

    def test_parser_type(self):
        assert self.parser.format_name() == "CMX3600 EDL"

    def test_parse_title(self):
        proj = self.parser.parse(SAMPLE_EDL)
        assert "Sample EDL" in proj.metadata.title

    def test_parse_clip_count(self):
        proj = self.parser.parse(SAMPLE_EDL)
        assert proj.clip_count() == 6

    def test_parse_timeline(self):
        proj = self.parser.parse(SAMPLE_EDL)
        assert len(proj.timelines) == 1
        assert proj.timelines[0].framerate == self.parser.default_framerate

    def test_parse_tracks(self):
        proj = self.parser.parse(SAMPLE_EDL)
        tracks = proj.timelines[0].tracks
        assert len(tracks) > 0

    def test_parse_has_video_track(self):
        proj = self.parser.parse(SAMPLE_EDL)
        has_video = any(t.track_type == TrackType.VIDEO for tl in proj.timelines for t in tl.tracks)
        assert has_video

    def test_parse_clip_names(self):
        proj = self.parser.parse(SAMPLE_EDL)
        clips = [c for tl in proj.timelines for t in tl.tracks for c in t.clips]
        named = [c for c in clips if c.clip_name]
        assert len(named) > 0

    def test_parse_timecodes(self):
        proj = self.parser.parse(SAMPLE_EDL)
        for tl in proj.timelines:
            for t in tl.tracks:
                for c in t.clips:
                    if c.record_in is not None:
                        assert c.record_in.total_frames >= 0

    def test_parse_black_reel(self):
        proj = self.parser.parse(SAMPLE_EDL)
        clips = [c for tl in proj.timelines for t in tl.tracks for c in t.clips]
        black_clip = next((c for c in clips if c.reel_name is None and c.source_file is None), None)
        # BL reel items exist, source_file should be None for them
        assert any(c.source_file is None or "BL" in (c.clip_name or "") for c in clips)
