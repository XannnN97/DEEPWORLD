"""CSV exporter — stdlib csv module."""

from __future__ import annotations

import csv
from pathlib import Path
from ..core.model import UnifiedProject
from .base import BaseExporter, ExportError


class CsvExporter(BaseExporter):
    @classmethod
    def format_name(cls) -> str:
        return "CSV (Comma Separated Values)"

    @classmethod
    def file_extension(cls) -> str:
        return ".csv"

    def export(self, project: UnifiedProject, output_path: Path) -> Path:
        headers = [
            "Timeline", "Track", "Track Type", "#",
            "Clip Name", "Source File", "Source In", "Source Out",
            "Record In", "Record Out", "Duration", "Speed %",
            "Transition", "Transition Duration",
        ]

        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            for timeline in project.timelines:
                for track in timeline.tracks:
                    for i, clip in enumerate(track.clips, 1):
                        writer.writerow([
                            timeline.name,
                            track.name,
                            track.track_type.value,
                            i,
                            clip.clip_name,
                            clip.source_file or "",
                            clip.source_in.to_smpte_string() if clip.source_in else "",
                            clip.source_out.to_smpte_string() if clip.source_out else "",
                            clip.record_in.to_smpte_string() if clip.record_in else "",
                            clip.record_out.to_smpte_string() if clip.record_out else "",
                            clip.record_duration.to_smpte_string() if clip.record_duration else "",
                            clip.speed,
                            clip.transition.transition_type.value if clip.transition else "Cut",
                            clip.transition.duration.to_smpte_string() if clip.transition and clip.transition.duration else "",
                        ])

        return output_path


# Register
from .base import ExporterRegistry
ExporterRegistry.register(CsvExporter)
