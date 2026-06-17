"""FCPX XML (FCPXML) parser — Final Cut Pro exchange format using lxml."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

from .base import BaseParser, ParseError
from ..core.model import (
    UnifiedClip,
    UnifiedProject,
    UnifiedTimeline,
    UnifiedTrack,
    ProjectMetadata,
    Transition,
    Marker,
)
from ..core.enums import TrackType, TransitionType
from ..core.timecode import Timecode

try:
    from lxml import etree
except ImportError:
    etree = None  # type: ignore


_NS = "{http://www.apple.com/finalcutpro}"
_NSFCP7 = "{http://www.apple.com/finalcutpro/XMLSchema}"

_TRACK_TYPE_MAP = {
    "video": TrackType.VIDEO,
    "audio": TrackType.AUDIO,
    "subtitle": TrackType.SUBTITLE,
    "titles": TrackType.GENERATOR,
}


def _parse_rational(s: str, default_framerate: Fraction) -> Timecode:
    """Parse FCPXML time string. Rational '1001/24000s' or plain '30s'."""
    s = s.strip()
    if "/" in s:
        return Timecode.from_rational(s, default_framerate)
    if s.endswith("s"):
        sec = float(s[:-1])
        return Timecode.from_seconds(sec, default_framerate)
    # Maybe it's a frame count
    try:
        return Timecode(int(s), default_framerate)
    except ValueError:
        raise ParseError(f"Cannot parse FCPXML time: {s!r}")


class FCPXMLParser(BaseParser):
    @classmethod
    def format_name(cls) -> str:
        return "FCPXML (Final Cut Pro)"

    @classmethod
    def file_extensions(cls) -> list[str]:
        return [".fcpxml"]

    def parse(self, file_path: Path) -> UnifiedProject:
        if etree is None:
            raise ImportError("lxml is required for FCPXML parsing")

        tree = etree.parse(str(file_path))
        root = tree.getroot()

        # Strip namespace for easier access
        ns = root.tag.replace("fcpxml", "")  # e.g. "{http://...}"

        metadata = ProjectMetadata(
            title=self._get_attr(root, "name", "Untitled"),
            source_format="fcpxml",
            source_path=str(file_path),
            software="Final Cut Pro",
        )

        projects = []

        for proj_elem in root.iter(f"{ns}project"):
            proj_name = proj_elem.get("name", "Untitled")
            seq_elem = proj_elem.find(f"{ns}sequence")

            if seq_elem is None:
                continue

            # Get framerate from sequence
            tc_elem = seq_elem.find(f"{ns}timecode")
            fr = self._parse_framerate(tc_elem) if tc_elem is not None else Fraction(24000, 1001)
            duration_str = seq_elem.get("duration", "")
            drop_frame = (tc_elem.get("format", "") if tc_elem is not None else "") in (
                "dd/mm/ss", "NDF"
            )

            # Build resource library
            resources = root.find(f"{ns}resources")
            asset_map = {}
            format_map = {}
            if resources is not None:
                for fmt in resources.iter(f"{ns}format"):
                    fmt_id = fmt.get("id")
                    if fmt_id:
                        format_map[fmt_id] = self._parse_framerate(fmt)
                for asset in resources.iter(f"{ns}asset"):
                    asset_id = asset.get("id")
                    if asset_id:
                        src_url = asset.get("src", "")
                        asset_map[asset_id] = src_url

            timeline = UnifiedTimeline(
                name=proj_name,
                framerate=fr,
                drop_frame=drop_frame,
            )

            # Walk spine (primary storyline)
            spine = seq_elem.find(f"{ns}spine")
            if spine is not None:
                # Primary track (V1 timeline)
                main_track = UnifiedTrack(name="Video 1", track_type=TrackType.VIDEO, index=1)
                # Connected clips go into additional tracks
                connected_tracks: list[UnifiedTrack] = []

                # Parse all clip items in the spine
                self._parse_spine_clips(spine, ns, main_track, connected_tracks, fr, asset_map, format_map)

                timeline.tracks = [main_track] + connected_tracks

            projects.append(timeline)

        return UnifiedProject(
            metadata=metadata,
            timelines=projects if projects else [UnifiedTimeline()],
        )

    def _parse_framerate(self, tc_elem) -> Fraction:
        """Extract framerate from a timecode element (FCPXML)."""
        fr_str = tc_elem.get("frameDuration", "")
        if fr_str:
            try:
                return _parse_rational(fr_str, Fraction(24, 1)).framerate
            except Exception:
                pass
        # Fall through to rate attribute
        rate_elem = tc_elem.find(f"*//rate")
        if rate_elem is not None:
            timebase_str = rate_elem.get("timebase", "")
            ntsc_str = rate_elem.get("ntsc", "")
            if timebase_str:
                tb = int(timebase_str)
                ntsc_flag = ntsc_str == "TRUE" if ntsc_str else False
                if ntsc_flag:
                    return Fraction(tb * 1000, 1001)
                return Fraction(tb, 1)
        return Fraction(24000, 1001)

    def _parse_spine_clips(self, spine, ns, main_track, connected_tracks, fr, asset_map, format_map):
        """Walk spine children (primary storyline clips + gaps)."""
        for child in spine:
            tag = child.tag.replace(ns, "")
            if tag == "clip":
                clip = self._build_clip(child, ns, fr, asset_map)
                if clip:
                    main_track.clips.append(clip)
            elif tag == "gap":
                pass  # Skip gaps
            elif tag == "transition":
                pass  # Handle transitions on spine

        # Look for connected clips (children with lane attribute)
        conn_idx = 2
        for spine_child in spine:
            for grandchild in spine_child:
                tag = grandchild.tag.replace(ns, "")
                if tag == "clip" and grandchild.get("lane"):
                    lane = grandchild.get("lane")
                    # Reuse or create track for this lane
                    while len(connected_tracks) < int(lane):
                        connected_tracks.append(
                            UnifiedTrack(
                                name=f"Video {conn_idx}",
                                track_type=TrackType.VIDEO,
                                index=conn_idx,
                            )
                        )
                        conn_idx += 1
                    clip = self._build_clip(grandchild, ns, fr, asset_map)
                    if clip:
                        track_idx = int(lane) - 1
                        if 0 <= track_idx < len(connected_tracks):
                            connected_tracks[track_idx].clips.append(clip)

    def _build_clip(self, elem, ns, fr, asset_map):
        """Build a UnifiedClip from a FCPXML clip element."""
        clip = UnifiedClip()
        clip.clip_name = elem.get("name", "")
        clip.source_file = asset_map.get(elem.get("ref", ""), "")

        # Duration
        duration_str = elem.get("duration", "")
        if duration_str:
            try:
                duration = _parse_rational(duration_str, fr)
            except Exception:
                duration = None
        else:
            duration = None

        # Offsets
        offset_str = elem.get("offset", "")
        if offset_str:
            try:
                offset = _parse_rational(offset_str, fr)
            except Exception:
                offset = None
        else:
            offset = None

        start_str = elem.get("start", "")
        if start_str:
            try:
                start = _parse_rational(start_str, fr)
            except Exception:
                start = None
        else:
            start = None

        # For primary storyline clips, record_in is the one we track
        if offset is not None:
            clip.record_in = offset

        if start is not None:
            clip.source_in = start

        if duration is not None and clip.source_in is not None:
            clip.source_out = clip.source_in + duration

        # Markers
        marker_elem = elem.find(f"{ns}marker")
        if marker_elem is not None:
            marker_time_str = marker_elem.get("start", "") or marker_elem.get("value", "")
            if marker_time_str:
                try:
                    mt = _parse_rational(marker_time_str, fr)
                    clip.markers.append(Marker(
                        name=marker_elem.get("value", ""),
                        timecode=mt,
                    ))
                except Exception:
                    pass

        return clip

    def _get_attr(self, elem, attr, default=""):
        return elem.get(attr, default)


# Register parser
from .base import ParserRegistry
ParserRegistry.register(FCPXMLParser)
