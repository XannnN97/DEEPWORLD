"""DaVinci Resolve XML parser (FCP 7 XMEML variant)."""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path
from urllib.parse import unquote, urlparse

from .base import BaseParser, ParseError
from ..core.model import (
    UnifiedClip,
    UnifiedProject,
    UnifiedTimeline,
    UnifiedTrack,
    ProjectMetadata,
    Transition,
)
from ..core.enums import TrackType, TransitionType
from ..core.timecode import Timecode


try:
    from lxml import etree
except ImportError:
    etree = None


class ResolveXMLParser(BaseParser):
    @classmethod
    def format_name(cls) -> str:
        return "DaVinci Resolve XML"

    @classmethod
    def file_extensions(cls) -> list[str]:
        return [".xml", ".aaf"]

    @classmethod
    def can_parse(cls, file_path: Path) -> bool:
        """Check if first few bytes indicate a Resolve FCP7 XML."""
        if etree is None:
            return False
        try:
            text = file_path.read_bytes()[:2000]
            # Resolve XML typically has <xmeml> root or <fcpxml> - but we check
            # for xmeml specifically (fcpxml goes to the other parser)
            return b"<xmeml" in text
        except Exception:
            return False

    def parse(self, file_path: Path) -> UnifiedProject:
        if etree is None:
            raise ImportError("lxml is required for XML parsing")

        tree = etree.parse(str(file_path))
        root = tree.getroot()

        if root.tag.lower() != "xmeml":
            raise ParseError("Not a valid DaVinci Resolve XML (missing <xmeml> root)")

        metadata = ProjectMetadata(
            source_format="resolve-xml",
            source_path=str(file_path),
            software="DaVinci Resolve",
        )

        # Build file lookup from project elements
        project_elem = root.find("project")
        if project_elem is not None:
            name_elem = project_elem.find("name")
            if name_elem is not None and name_elem.text:
                metadata.title = name_elem.text.strip()

        # Build clip file mapping
        file_map = self._build_file_map(root)

        timelines = []
        for seq in root.iter("sequence"):
            timeline, fr = self._parse_sequence(seq, file_map)
            if timeline is not None:
                timelines.append(timeline)
                if fr is not None:
                    metadata.framerate = fr

        if not timelines:
            raise ParseError("No sequences found in Resolve XML")

        return UnifiedProject(metadata=metadata, timelines=timelines)

    def _build_file_map(self, root) -> dict:
        """Build mapping from clip id -> file info."""
        file_map = {}
        for clip_elem in root.iter("clip"):
            clip_id = clip_elem.get("id", "")
            if not clip_id:
                clip_id_elem = clip_elem.find("id")
                if clip_id_elem is not None and clip_id_elem.text:
                    clip_id = clip_id_elem.text.strip()
            if clip_id:
                file_map[clip_id] = clip_elem
        return file_map

    def _parse_sequence(self, seq_elem, file_map) -> tuple:
        """Parse a single sequence into UnifiedTimeline."""
        # Get sequence name
        name_elem = seq_elem.find("name")
        seq_name = name_elem.text.strip() if name_elem is not None and name_elem.text else "Sequence 1"

        # Get framerate from timecode
        tc_elem = seq_elem.find("timecode")
        fr = self._parse_framerate(tc_elem) if tc_elem is not None else Fraction(24000, 1001)
        drop = self._parse_drop_frame(tc_elem) if tc_elem is not None else False

        timeline = UnifiedTimeline(name=seq_name, framerate=fr, drop_frame=drop)

        # Media section contains video/audio tracks
        media = seq_elem.find("media")
        if media is None:
            return timeline, fr

        tracks = []

        # Parse video tracks
        video = media.find("video")
        if video is not None:
            for track_elem in video.iter("track"):
                track = self._parse_track(track_elem, "video", fr, file_map)
                if track is not None:
                    tracks.append(track)

        # Parse audio tracks
        audio = media.find("audio")
        if audio is not None:
            for track_elem in audio.iter("track"):
                track = self._parse_track(track_elem, "audio", fr, file_map)
                if track is not None:
                    tracks.append(track)

        timeline.tracks = tracks
        return timeline, fr

    def _parse_track(self, track_elem, track_type_str, fr, file_map):
        """Parse a track element into UnifiedTrack."""
        # Track number/label
        track_num = 1
        track_name = f"{track_type_str.title()} Track"
        tn_elem = track_elem.find("tracknumber")
        if tn_elem is not None and tn_elem.text:
            track_num = int(tn_elem.text.strip())
            track_name = f"{track_type_str.title()} {track_num}"
        elif "currentExplodedTrackIndex" in track_elem.attrib:
            track_num = int(track_elem.get("currentExplodedTrackIndex"))
            track_name = f"{track_type_str.title()} {track_num}"

        track_type = TrackType.VIDEO if track_type_str == "video" else TrackType.AUDIO
        track = UnifiedTrack(name=track_name, track_type=track_type, index=track_num)

        # Parse clip items
        for clipitem in track_elem.iter("clipitem"):
            clip = self._parse_clipitem(clipitem, fr, file_map, track_type)
            if clip is not None:
                track.clips.append(clip)

        # Handle transitions between clips
        # (transitions are separate elements in Resolve XML)
        for trans_elem in track_elem.iter("transitionitem"):
            pass  # Could parse transition items

        return track

    def _parse_clipitem(self, clipitem, fr, file_map, track_type):
        """Parse a clipitem element into UnifiedClip."""
        clip = UnifiedClip()

        # Clip name
        name_elem = clipitem.find("name")
        if name_elem is not None and name_elem.text:
            clip.clip_name = name_elem.text.strip()

        # Duration (in frames)
        dur_elem = clipitem.find("duration")
        duration_frames = None
        if dur_elem is not None and dur_elem.text:
            try:
                duration_frames = int(dur_elem.text.strip())
            except ValueError:
                pass

        # Source file
        file_id = clipitem.get("id", "") or self._get_file_id(clipitem)
        file_elem = file_map.get(file_id) if file_id else None
        if file_elem is not None and track_type == TrackType.VIDEO:
            path_elem = file_elem.find("pathurl")
            if path_elem is not None and path_elem.text:
                clip.source_file = self._decode_url(path_elem.text.strip())

        # Rate info
        rate = fr
        rate_elem = clipitem.find("rate")
        if rate_elem is not None:
            tb_elem = rate_elem.find("timebase")
            if tb_elem is not None and tb_elem.text:
                try:
                    tb = int(tb_elem.text.strip())
                    ntsc = rate_elem.find("ntsc")
                    ntsc_flag = ntsc is not None and ntsc.text and ntsc.text.strip().upper() == "TRUE"
                    if ntsc_flag:
                        rate = Fraction(tb * 1000, 1001)
                    else:
                        rate = Fraction(tb, 1)
                except (ValueError, TypeError):
                    pass

        # In/Out source points
        start_elem = clipitem.find("start")
        end_elem = clipitem.find("end")
        if start_elem is not None and start_elem.text:
            try:
                start_frames = int(start_elem.text.strip())
                clip.source_in = Timecode(start_frames, rate)
            except ValueError:
                pass
        if end_elem is not None and end_elem.text:
            try:
                end_frames = int(end_elem.text.strip())
                clip.source_out = Timecode(end_frames, rate)
            except ValueError:
                pass

        # Record In/Out
        record_in_elem = clipitem.find("recordin")
        record_out_elem = clipitem.find("recordout")
        if record_in_elem is not None and record_in_elem.text:
            try:
                ri = int(record_in_elem.text.strip())
                clip.record_in = Timecode(ri, rate)
            except ValueError:
                pass
        if record_out_elem is not None and record_out_elem.text:
            try:
                ro = int(record_out_elem.text.strip())
                clip.record_out = Timecode(ro, rate)
            except ValueError:
                pass

        # If we have start/end and duration, use them
        if clip.source_in is not None and duration_frames is not None and clip.source_out is None:
            clip.source_out = Timecode(clip.source_in.total_frames + duration_frames, rate)

        # Speed
        for field in clipitem.iter("field"):
            pass  # Parse speed info

        return clip

    def _get_file_id(self, clipitem):
        """Extract file ID from clipitem by looking for file element references."""
        file_elem = clipitem.find("file")
        if file_elem is not None:
            return file_elem.get("id", file_elem.text or "")
        return ""

    def _parse_framerate(self, tc_elem) -> Fraction:
        """Extract framerate from timecode element."""
        rate_elem = tc_elem.find("rate")
        if rate_elem is None:
            return Fraction(24000, 1001)
        tb_elem = rate_elem.find("timebase")
        if tb_elem is None or not tb_elem.text:
            return Fraction(24000, 1001)
        try:
            tb = int(tb_elem.text.strip())
            ntsc = rate_elem.find("ntsc")
            if ntsc is not None and ntsc.text and ntsc.text.strip().upper() == "TRUE":
                return Fraction(tb * 1000, 1001)
            return Fraction(tb, 1)
        except ValueError:
            return Fraction(24000, 1001)

    def _parse_drop_frame(self, tc_elem) -> bool:
        """Check if timecode is drop-frame."""
        if tc_elem is None:
            return False
        df_elem = tc_elem.find("frame")
        if df_elem is not None and df_elem.text:
            t = df_elem.text.strip()
            return ";" in t
        return False

    def _decode_url(self, url: str) -> str:
        """Decode file:// URL to local path."""
        if url.startswith("file://"):
            path = url[7:]
            path = unquote(path)
            # Handle Windows paths: file://localhost/C%3A/...
            if path.startswith("localhost/"):
                path = path[10:]
                if len(path) >= 2 and path[1] == ":":
                    pass  # Already a Windows path like C:/
                else:
                    path = "/" + path
            return path
        return url


# Register parser
from .base import ParserRegistry
ParserRegistry.register(ResolveXMLParser)
