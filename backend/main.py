from pathlib import Path
from threading import Thread, Lock
from time import time

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.database import (
    init_db,
    save_detection,
    save_vehicle_event,
    get_recent_detections,
    get_stats,
    clear_detections as clear_database_detections,
)
from vision.video_detector import process_video_file, process_video_source

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

init_db()

app = FastAPI(
    title="Vehicle Analytics API",
    description="Vehicle detection and video analytics with RTSP support",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

CURRENT_STATS = {
    "total_detections": 0,
    "cars": 0,
    "trucks": 0,
    "buses": 0,
    "motorcycles": 0,
    "line_crossings": 0,
    "processed_frames": 0,
}

RTSP_STATE = {
    "status": "stopped",
    "url": None,
    "error": None,
    "started_at": None,
}
RTSP_LOCK = Lock()
RTSP_THREAD = None


class RTSPRequest(BaseModel):
    url: str = "rtsp://127.0.0.1:8554/traffic"


def run_rtsp_worker(url: str):
    global RTSP_THREAD

    try:
        with RTSP_LOCK:
            RTSP_STATE.update(status="running", url=url, error=None)

        # Process a limited batch so the API worker can return to status polling.
        result = process_video_source(url, max_frames=300)

        stats = result["stats"]
        with RTSP_LOCK:
            CURRENT_STATS.update(stats)

        clear_database_detections()

        for item in result.get("detections", []):
            save_detection(
                vehicle_type=item.get("vehicle_type", item.get("class_name", "unknown")),
                color=item.get("color", "Unknown"),
                confidence=item.get("confidence", 0),
                track_id=item.get("track_id"),
            )

        for event in result.get("crossing_events", []):
            save_vehicle_event(
                vehicle_id=event["vehicle_id"],
                color=event["color"],
                direction=event["direction"],
            )

        with RTSP_LOCK:
            RTSP_STATE.update(status="completed", error=None)

    except Exception as exc:
        with RTSP_LOCK:
            RTSP_STATE.update(status="error", error=str(exc))
    finally:
        RTSP_THREAD = None


@app.get("/")
def home():
    return {"message": "Vehicle Analytics API is running", "docs": "/docs"}


@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "vehicle-analytics"}


@app.get("/api/stats")
def stats():
    database_stats = get_stats()
    with RTSP_LOCK:
        extra_stats = {
            "line_crossings": CURRENT_STATS["line_crossings"],
            "processed_frames": CURRENT_STATS["processed_frames"],
        }
    return {**database_stats, **extra_stats}


@app.get("/api/detections")
def detections():
    records = get_recent_detections(100)
    for record in records:
        record["class_name"] = record["vehicle_type"]
    return records


@app.delete("/api/detections")
def clear_detections():
    clear_database_detections()
    with RTSP_LOCK:
        for key in CURRENT_STATS:
            CURRENT_STATS[key] = 0
    return {"message": "Detection records cleared"}


@app.get("/api/rtsp/status")
def rtsp_status():
    with RTSP_LOCK:
        return dict(RTSP_STATE)


@app.post("/api/rtsp/start")
def rtsp_start(request: RTSPRequest):
    global RTSP_THREAD

    url = request.url.strip()
    if not url.lower().startswith(("rtsp://", "rtsps://")):
        raise HTTPException(status_code=400, detail="A valid RTSP URL is required")

    if RTSP_THREAD is not None and RTSP_THREAD.is_alive():
        raise HTTPException(status_code=409, detail="RTSP processing is already active")

    RTSP_THREAD = Thread(target=run_rtsp_worker, args=(url,), daemon=True)
    RTSP_THREAD.start()

    return {"message": "RTSP processing started", "url": url, "status": "starting"}


@app.post("/api/rtsp/stop")
def rtsp_stop():
    # The current OpenCV processing batch cannot be safely interrupted mid-read.
    # This endpoint reports status rather than pretending to terminate the worker.
    with RTSP_LOCK:
        return {
            "message": "The current RTSP batch cannot be force-stopped safely. "
                       "It will finish after 300 frames or report an error.",
            "status": RTSP_STATE["status"],
        }


@app.post("/api/process-video")
async def process_video(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    extension = Path(file.filename).suffix.lower()
    if extension not in {".mp4", ".avi", ".mov", ".mkv"}:
        raise HTTPException(
            status_code=400,
            detail="Upload an MP4, AVI, MOV, or MKV video",
        )

    video_path = OUTPUT_DIR / f"input_video{extension}"
    output_path = OUTPUT_DIR / "processed_video.mp4"

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded video is empty")
        video_path.write_bytes(content)
    finally:
        await file.close()

    try:
        result = process_video_file(video_path, output_path)
        video_stats = result["stats"]
        video_detections = result["detections"]
        crossing_events = result.get("crossing_events", [])

        clear_database_detections()

        for item in video_detections:
            save_detection(
                vehicle_type=item.get("vehicle_type", item.get("class_name", "unknown")),
                color=item.get("color", "Unknown"),
                confidence=item.get("confidence", 0),
                track_id=item.get("track_id"),
            )

        for event in crossing_events:
            save_vehicle_event(
                vehicle_id=event["vehicle_id"],
                color=event["color"],
                direction=event["direction"],
            )

        with RTSP_LOCK:
            CURRENT_STATS.update(video_stats)

        return {
            "message": "Video processing completed successfully",
            "status": "processed",
            "filename": video_path.name,
            "processed_video": "/outputs/processed_video.mp4",
            "output_video": "/outputs/processed_video.mp4",
            "stats": {
                **get_stats(),
                "line_crossings": CURRENT_STATS["line_crossings"],
                "processed_frames": CURRENT_STATS["processed_frames"],
            },
            "detections": [
                {
                    **item,
                    "class_name": item.get(
                        "vehicle_type", item.get("class_name", "unknown")
                    ),
                }
                for item in video_detections
            ],
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Video processing failed: {exc}",
        ) from exc
