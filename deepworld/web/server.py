"""FastAPI web server for DEEPWORLD converter."""

from __future__ import annotations

import os
import tempfile
import uvicorn
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from ..converter import ConvertPipeline
from ..parsers import ParserRegistry
from ..exporters import ExporterRegistry

HERE = Path(__file__).parent
TEMPLATES = HERE / "templates"
STATIC = HERE / "static"

app = FastAPI(title="DEEPWORLD - Film Editor Converter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = TEMPLATES / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return HTMLResponse("<h1>DEEPWORLD</h1><p>Template not found.</p>")


@app.post("/api/parse")
async def parse_file(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix.lower()
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        project = ConvertPipeline.parse(Path(tmp_path))
        preview = _project_to_preview(project)
        return {"ok": True, "project": preview, "filename": file.filename}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@app.get("/api/formats")
async def list_formats():
    return {
        "input": ParserRegistry.list_format_names(),
        "output": ExporterRegistry.list_format_names(),
    }


@app.post("/api/export")
async def export_file(
    file: UploadFile = File(...),
    output_format: str = Form(...),
):
    suffix = Path(file.filename).suffix.lower()
    tmp_in = None
    try:
        # Save input
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_in = tmp.name

        project = ConvertPipeline.parse(Path(tmp_in))

        # Export
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_format}") as tmp_out:
            out_path = tmp_out.name

        ConvertPipeline.export(project, Path(out_path))

        media_types = {
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "csv": "text/csv",
        }
        mt = media_types.get(output_format, "application/octet-stream")
        out_name = Path(file.filename).stem + f"_report.{output_format}"

        return FileResponse(
            out_path,
            media_type=mt,
            filename=out_name,
            headers={"Content-Disposition": f'attachment; filename="{out_name}"'},
        )
    finally:
        try:
            if tmp_in:
                os.unlink(tmp_in)
        except Exception:
            pass
        # Note: FileResponse cleans up on GC, but we can't unlink immediately


def _project_to_preview(project):
    """Convert UnifiedProject to JSON for frontend preview."""
    timelines = []
    for ti, timeline in enumerate(project.timelines):
        tracks = []
        for track in timeline.tracks:
            clips_list = []
            for ci, clip in enumerate(track.clips, 1):
                clips_list.append({
                    "index": ci,
                    "clip_name": clip.clip_name,
                    "source_file": clip.source_file or "",
                    "source_in": clip.source_in.to_smpte_string() if clip.source_in else "",
                    "source_out": clip.source_out.to_smpte_string() if clip.source_out else "",
                    "record_in": clip.record_in.to_smpte_string() if clip.record_in else "",
                    "record_out": clip.record_out.to_smpte_string() if clip.record_out else "",
                    "duration": clip.record_duration.to_smpte_string() if clip.record_duration else "",
                    "speed": clip.speed,
                    "transition": clip.transition.transition_type.value if clip.transition else "Cut",
                    "markers": [{"name": m.name, "tc": m.timecode.to_smpte_string() if m.timecode else ""} for m in clip.markers],
                })
            tracks.append({
                "name": track.name,
                "type": track.track_type.value,
                "index": track.index,
                "clips": clips_list,
            })
        timelines.append({
            "name": timeline.name,
            "framerate": float(timeline.framerate),
            "tracks": tracks,
        })
    return {
        "title": project.metadata.title,
        "source_format": project.metadata.source_format,
        "framerate": float(project.metadata.framerate),
        "clip_count": project.clip_count(),
        "timelines": timelines,
    }


def start_server(host: str = "127.0.0.1", port: int = 8080):
    print(f"DEEPWORLD web UI starting: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
