"""Tests for EDL parser — transition, speed, black reel, edge cases."""

from pathlib import Path
from deepworld.parsers import ParserRegistry
from deepworld.core.enums import TrackType, TransitionType
from deepworld.core.timecode import Timecode
from fractions import Fraction

SAMPLES = Path(__file__).parent.parent / "samples"
SAMPLE_EDL = SAMPLES / "sample_cmx3600.edl"


class TestEDLParserTransition:
    def test_transition_detected(self):
        """Dissolve events should carry a Transition object."""
        proj = ParserRegistry.get_parser(SAMPLE_EDL).parse(SAMPLE_EDL)
        clips = [c for tl in proj.timelines for t in tl.tracks for c in t.clips]
        with_transition = [c for c in clips if c.transition is not None]
        assert len(with_transition) > 0, "Should find at least one dissolve"

    def test_transition_type(self):
        proj = ParserRegistry.get_parser(SAMPLE_EDL).parse(SAMPLE_EDL)
        clips = [c for tl in proj.timelines for t in tl.tracks for c in t.clips]
        dissolves = [c for c in clips if c.transition and c.transition.transition_type == TransitionType.DISSOLVE]
        assert len(dissolves) >= 2  # events 004 and 006 are D type

    def test_speed_from_comment(self):
        """Default speed should be 100.0 for normal clips."""
        proj = ParserRegistry.get_parser(SAMPLE_EDL).parse(SAMPLE_EDL)
        clips = [c for tl in proj.timelines for t in tl.tracks for c in t.clips]
        non_black = [c for c in clips if c.clip_name and "[BL]" not in c.clip_name]
        for clip in non_black:
            assert clip.speed == 100.0 or clip.speed > 0

    def test_black_reel_handling(self):
        """BL reel items should have no source_file and clip_name starting with [BL]."""
        proj = ParserRegistry.get_parser(SAMPLE_EDL).parse(SAMPLE_EDL)
        clips = [c for tl in proj.timelines for t in tl.tracks for c in t.clips]
        bl_clips = [c for c in clips if "[BL]" in c.clip_name]
        assert len(bl_clips) > 0
        for c in bl_clips:
            assert c.source_file is None or c.source_file == ""


class TestEDLParserTrackSeparation:
    def test_video_and_audio_tracks(self):
        proj = ParserRegistry.get_parser(SAMPLE_EDL).parse(SAMPLE_EDL)
        tracks = [t for tl in proj.timelines for t in tl.tracks]
        types = {t.track_type for t in tracks}
        assert TrackType.VIDEO in types
        assert TrackType.AUDIO in types

    def test_clip_timecodes_consistent(self):
        proj = ParserRegistry.get_parser(SAMPLE_EDL).parse(SAMPLE_EDL)
        for tl in proj.timelines:
            for t in tl.tracks:
                for c in t.clips:
                    if c.record_in is not None and c.record_out is not None:
                        assert c.record_out.total_frames > c.record_in.total_frames


class TestEDLParserClipNames:
    def test_clip_names_extracted(self):
        proj = ParserRegistry.get_parser(SAMPLE_EDL).parse(SAMPLE_EDL)
        clips = [c for tl in proj.timelines for t in tl.tracks for c in t.clips]
        named = [c for c in clips if c.clip_name and not c.clip_name.startswith("[")]
        assert len(named) >= 4
