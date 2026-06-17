"""Tests for data model."""

from fractions import Fraction
from deepworld.core.model import (
    UnifiedProject, UnifiedTimeline, UnifiedTrack, UnifiedClip,
    ProjectMetadata, Transition, Marker,
)
from deepworld.core.enums import TrackType, TransitionType
from deepworld.core.timecode import Timecode


class TestUnifiedProject:
    def test_empty_project(self):
        proj = UnifiedProject()
        assert proj.clip_count() == 0

    def test_project_with_clips(self):
        tc = Timecode(0, Fraction(24, 1))
        clip = UnifiedClip(clip_name="Test", record_in=tc, record_out=Timecode(50, Fraction(24, 1)))
        track = UnifiedTrack(name="V1", track_type=TrackType.VIDEO, clips=[clip])
        timeline = UnifiedTimeline(name="Seq1", tracks=[track])
        proj = UnifiedProject(
            metadata=ProjectMetadata(title="Test"),
            timelines=[timeline],
        )
        assert proj.clip_count() == 1
        assert proj.metadata.title == "Test"


class TestUnifiedClip:
    def test_record_duration(self):
        tc_in = Timecode(100, Fraction(24, 1))
        tc_out = Timecode(150, Fraction(24, 1))
        clip = UnifiedClip(record_in=tc_in, record_out=tc_out)
        assert clip.record_duration is not None
        assert clip.record_duration.total_frames == 50

    def test_source_duration(self):
        tc_in = Timecode(0, Fraction(24, 1))
        tc_out = Timecode(72, Fraction(24, 1))
        clip = UnifiedClip(source_in=tc_in, source_out=tc_out)
        assert clip.source_duration is not None
        assert clip.source_duration.total_frames == 72

    def test_no_duration(self):
        clip = UnifiedClip()
        assert clip.record_duration is None
        assert clip.source_duration is None


class TestUnifiedTrack:
    def test_track_creation(self):
        track = UnifiedTrack(name="V1", track_type=TrackType.VIDEO, index=1)
        assert track.name == "V1"
        assert track.track_type == TrackType.VIDEO
        assert track.index == 1
        assert len(track.clips) == 0


class TestTransition:
    def test_cut_default(self):
        t = Transition()
        assert t.transition_type == TransitionType.CUT

    def test_dissolve(self):
        t = Transition(transition_type=TransitionType.DISSOLVE)
        assert t.transition_type == TransitionType.DISSOLVE


class TestMarker:
    def test_marker_creation(self):
        tc = Timecode(100, Fraction(24, 1))
        m = Marker(name="Test", timecode=tc)
        assert m.name == "Test"
        assert m.timecode.total_frames == 100
