"""CMX3600 EDL parser — line-based state machine."""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path
from typing import Optional

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
from ..core.enums import TrackType, TransitionType, EditType
from ..core.timecode import Timecode


# Regex patterns for EDL lines
_RE_EVENT = re.compile(
    r"^(\d{3})\s+"  # Event number
    r"(\S{0,8})\s+"  # Reel name
    r"(\S+)\s+"  # Track type (V, A1, A2, AA, B, etc.)
    r"(\S+)\s+"  # Edit type (C, D, W, K, M)
    r"(\d{2}:\d{2}:\d{2}[:;]\d{2})\s+"  # Source IN
    r"(\d{2}:\d{2}:\d{2}[:;]\d{2})\s+"  # Source OUT
    r"(\d{2}:\d{2}:\d{2}[:;]\d{2})\s+"  # Record IN
    r"(\d{2}:\d{2}:\d{2}[:;]\d{2})"  # Record OUT
)
_RE_M2 = re.compile(r"^M2\s+(\S+)\s+(\S+)\s+(\S+)\s+(\d{2}:\d{2}:\d{2}[:;]\d{2})\s+(\d{2}:\d{2}:\d{2}[:;]\d{2})\s+(\d{2}:\d{2}:\d{2}[:;]\d{2})\s+(\d{2}:\d{2}:\d{2}[:;]\d{2})")
_RE_SPEED = re.compile(r"^\*\s*SPEED\s*:\s*([\d.-]+)", re.IGNORECASE)
_RE_CLIP_NAME = re.compile(r"^\*\s*FROM\s+CLIP\s+NAME\s*:\s*(.+)", re.IGNORECASE)
_RE_SOURCE_FILE = re.compile(r"^\*\s*SOURCE\s+FILE\s*:\s*(.+)", re.IGNORECASE)
_RE_TRANS_DUR = re.compile(r"^\*\s*TRANSITION\s+DURATION\s*:\s*(\d+)", re.IGNORECASE)
_RE_AUDIO_PATCH = re.compile(r"^\*\s*AUDIO\s+(?:PATCH\s+)?(?:\w+)?\s*:\s*(.+)")


_AUDIO_TRACKS = {"A1", "A2", "A3", "A4", "AA", "A", "B", "A2/A3", "A3/A4"}


def _parse_track_type(raw: str) -> TrackType:
    raw = raw.strip().upper()
    if raw == "V":
        return TrackType.VIDEO
    # Check for audio types
    if raw.startswith("A") or raw == "B" or raw.startswith("AA"):
        return TrackType.AUDIO
    return TrackType.UNKNOWN


class EDLParser(BaseParser):
    @classmethod
    def format_name(cls) -> str:
        return "CMX3600 EDL"

    @classmethod
    def file_extensions(cls) -> list[str]:
        return [".edl"]

    def __init__(self, default_framerate: Fraction = Fraction(24, 1)):
        self.default_framerate = default_framerate

    def parse(self, file_path: Path) -> UnifiedProject:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        metadata = ProjectMetadata(
            source_format="edl",
            source_path=str(file_path),
        )
        timeline = UnifiedTimeline(framerate=self.default_framerate)
        tracks: dict[str, UnifiedTrack] = {}
        current_event: Optional[dict] = None
        clip_name_map: dict[int, str] = {}  # event_num -> clip_name
        source_file_map: dict[int, str] = {}

        for line in lines:
            line = line.rstrip("\n\r")

            # Header lines
            if line.upper().startswith("TITLE:"):
                metadata.title = line.split(":", 1)[1].strip()
                continue
            if line.upper().startswith("FCM:"):
                fcm = line.split(":", 1)[1].strip().upper()
                metadata.drop_frame = "DROP" in fcm
                timeline.drop_frame = "DROP" in fcm
                continue

            # Event line
            m = _RE_EVENT.match(line)
            if m:
                event_num = int(m[1])
                reel = m[2].strip()
                track_raw = m[3].strip()
                edit_raw = m[4].strip().upper()
                src_in = m[5]
                src_out = m[6]
                rec_in = m[7]
                rec_out = m[8]

                current_event = {
                    "event_num": event_num,
                    "reel": reel,
                    "track": track_raw,
                    "edit": edit_raw,
                    "src_in": src_in,
                    "src_out": src_out,
                    "rec_in": rec_in,
                    "rec_out": rec_out,
                }
                continue

            # M2 motion effect line
            m2 = _RE_M2.match(line)
            if m2 and current_event is not None:
                src_in = m2[4]
                src_out = m2[5]
                rec_in = m2[6]
                rec_out = m2[7]
                current_event["src_in"] = src_in
                current_event["src_out"] = src_out
                current_event["rec_in"] = rec_in
                current_event["rec_out"] = rec_out
                continue

            # Comment lines
            m_cn = _RE_CLIP_NAME.match(line)
            if m_cn and current_event is not None:
                clip_name_map[current_event["event_num"]] = m_cn[1].strip()
                continue

            m_sf = _RE_SOURCE_FILE.match(line)
            if m_sf and current_event is not None:
                source_file_map[current_event["event_num"]] = m_sf[1].strip()
                continue

            m_sp = _RE_SPEED.match(line)
            if m_sp and current_event is not None:
                current_event["speed"] = float(m_sp[1])
                continue

            m_td = _RE_TRANS_DUR.match(line)
            if m_td and current_event is not None:
                current_event["transition_frames"] = int(m_td[1])
                continue

        # Build clips from collected events
        # Collect all event lines first, then handle transition pairs
        events = []
        for line in lines:
            m = _RE_EVENT.match(line)
            if m:
                events.append(m)

        # Process events, handling transition pairs
        i = 0
        while i < len(events):
            m = events[i]
            event_num = int(m[1])
            reel = m[2].strip()
            track_raw = m[3].strip()
            edit_raw = m[4].strip().upper()
            src_in_str = m[5]
            src_out_str = m[6]
            rec_in_str = m[7]
            rec_out_str = m[8]

            drop = metadata.drop_frame
            fr = self.default_framerate

            # Check if this is a transition (dissolve/wipe) — two lines with same event number
            is_transition = edit_raw in ("D", "W", "K")
            transition_frames = None
            speed = 100.0

            # Look for transition duration comment
            if is_transition:
                for line in lines:
                    if _RE_TRANS_DUR.match(line):
                        transition_frames = int(_RE_TRANS_DUR.match(line)[1])

            # Look for speed comments for this event
            speed_val = self._find_speed_for_event(events, event_num, lines)

            transition = None
            if is_transition:
                duration = None
                if transition_frames is not None:
                    duration = Timecode(transition_frames, fr, drop)
                edit_map = {"D": TransitionType.DISSOLVE, "W": TransitionType.WIPE, "K": TransitionType.KEY}
                transition = Transition(
                    transition_type=edit_map.get(edit_raw, TransitionType.DISSOLVE),
                    duration=duration,
                )

            clip = UnifiedClip(
                clip_name=clip_name_map.get(event_num, ""),
                reel_name=reel if reel and reel != "BL" and reel != "AX" and not reel.startswith("00") else None,
                source_in=Timecode.from_string(src_in_str, fr, drop),
                source_out=Timecode.from_string(src_out_str, fr, drop),
                record_in=Timecode.from_string(rec_in_str, fr, drop),
                record_out=Timecode.from_string(rec_out_str, fr, drop),
                source_file=source_file_map.get(event_num),
                transition=transition,
                speed=speed_val or 100.0,
            )

            if reel == "BL" or reel == "AX":
                clip.source_file = None
                clip.clip_name = clip.clip_name or (f"[{reel}]")

            track_type = _parse_track_type(track_raw)
            track_key = track_raw.upper()
            if track_key not in tracks:
                track_index = len(tracks) + 1
                tracks[track_key] = UnifiedTrack(
                    name=track_raw,
                    track_type=track_type,
                    index=track_index,
                )
            tracks[track_key].clips.append(clip)

            i += 1

        timeline.tracks = list(tracks.values())
        project = UnifiedProject(metadata=metadata, timelines=[timeline])
        return project

    def _find_speed_for_event(self, events, event_num, lines) -> Optional[float]:
        """Find M2 lines for this event to determine speed."""
        for line in lines:
            m2 = _RE_M2.match(line)
            if m2:
                # M2 lines come after the main event line for the same event
                pass
        # Look for SPEED comments after this event's lines
        found = False
        for line in lines:
            if _RE_EVENT.match(line) and int(_RE_EVENT.match(line)[1]) != event_num:
                if found:
                    break
                continue
            if _RE_EVENT.match(line) and int(_RE_EVENT.match(line)[1]) == event_num:
                found = True
                continue
            if found:
                m_sp = _RE_SPEED.match(line)
                if m_sp:
                    return float(m_sp[1])

        # Also search M2 lines
        for line in lines:
            m2 = _RE_M2.match(line)
            if m2:
                try:
                    sp = float(line.split("*")[-1].split(":")[-1].strip()) if "*" in line else 100.0
                    return sp
                except (ValueError, IndexError):
                    pass
        return None


# Register parser
from .base import ParserRegistry
ParserRegistry.register(EDLParser)
