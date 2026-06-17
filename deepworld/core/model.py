from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Optional

from .enums import TrackType, TransitionType
from .timecode import Timecode


@dataclass
class ProjectMetadata:
    title: str = "Untitled"
    author: str = ""
    description: str = ""
    framerate: Fraction = Fraction(24000, 1001)
    drop_frame: bool = False
    source_format: str = ""
    source_path: str = ""
    software: str = ""


@dataclass
class Marker:
    name: str = ""
    timecode: Optional[Timecode] = None
    duration: Optional[Timecode] = None
    color: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class Transition:
    transition_type: TransitionType = TransitionType.CUT
    duration: Optional[Timecode] = None
    offset: Optional[Timecode] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class UnifiedClip:
    source_file: Optional[str] = None
    clip_name: str = ""
    reel_name: Optional[str] = None
    source_in: Optional[Timecode] = None
    source_out: Optional[Timecode] = None
    record_in: Optional[Timecode] = None
    record_out: Optional[Timecode] = None
    transition: Optional[Transition] = None
    speed: float = 100.0
    markers: list[Marker] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def source_duration(self) -> Optional[Timecode]:
        if self.source_in is not None and self.source_out is not None:
            return self.source_out - self.source_in
        return None

    @property
    def record_duration(self) -> Optional[Timecode]:
        if self.record_in is not None and self.record_out is not None:
            return self.record_out - self.record_in
        return None


@dataclass
class UnifiedTrack:
    name: str = ""
    track_type: TrackType = TrackType.VIDEO
    index: int = 1
    clips: list[UnifiedClip] = field(default_factory=list)


@dataclass
class UnifiedTimeline:
    name: str = "Timeline 1"
    framerate: Fraction = Fraction(24000, 1001)
    drop_frame: bool = False
    start_timecode: Optional[Timecode] = None
    tracks: list[UnifiedTrack] = field(default_factory=list)
    markers: list[Marker] = field(default_factory=list)


@dataclass
class UnifiedProject:
    metadata: ProjectMetadata = field(default_factory=ProjectMetadata)
    timelines: list[UnifiedTimeline] = field(default_factory=list)

    def clip_count(self) -> int:
        return sum(
            len(c.clips)
            for t in self.timelines
            for c in t.tracks
        )
