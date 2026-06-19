"""SRT subtitle parser."""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path

from .base import BaseParser, ParseError
from ..core.model import (
    UnifiedClip,
    UnifiedProject,
    UnifiedTimeline,
    UnifiedTrack,
    ProjectMetadata,
)
from ..core.enums import TrackType
from ..core.timecode import Timecode


_RE_BLOCK = re.compile(
    r"(\d+)\s*\n"
    r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*\n"
    r"((?:.+\n?)*?)(?:\n\n|\n*$)",
    re.MULTILINE,
)


class SRTParser(BaseParser):
    @classmethod
    def format_name(cls) -> str:
        return "SRT Subtitle"

    @classmethod
    def file_extensions(cls) -> list[str]:
        return [".srt"]

    def parse(self, file_path: Path) -> UnifiedProject:
        text = file_path.read_text(encoding="utf-8", errors="replace")

        # Normalize line endings
        text = text.replace("\r\n", "\n")

        metadata = ProjectMetadata(
            source_format="srt",
            source_path=str(file_path),
        )
        # SRT is time-based, default framerate is arbitrary (25)
        fr = Fraction(25, 1)
        timeline = UnifiedTimeline(name="Subtitles", framerate=fr)
        track = UnifiedTrack(name="Subtitle 1", track_type=TrackType.SUBTITLE, index=1)

        matches = _RE_BLOCK.findall(text)

        for seq, start_str, end_str, text_content in matches:
            text_clean = text_content.strip().replace("\r\n", "\n")
            # Normalize to comma separator for from_srt_time
            start_str_norm = start_str.replace(".", ",")
            end_str_norm = end_str.replace(".", ",")
            start = Timecode.from_srt_time(start_str_norm, fr)
            end = Timecode.from_srt_time(end_str_norm, fr)

            clip = UnifiedClip(
                clip_name=text_clean,
                source_in=start,
                source_out=end,
                record_in=start,
                record_out=end,
            )
            track.clips.append(clip)

        if not track.clips:
            raise ParseError(f"No valid SRT blocks found in {file_path}")

        timeline.tracks = [track]
        return UnifiedProject(metadata=metadata, timelines=[timeline])


# Register parser
from .base import ParserRegistry
ParserRegistry.register(SRTParser)
