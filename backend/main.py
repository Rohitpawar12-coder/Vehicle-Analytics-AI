from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import (
    init_db,
    save_detection,
    get_recent_detections,
    get_stats,
    clear_detections as clear_database_detections,
)
from vision.video_detector import process_video_file

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

init_db()

app = FastAPI(
    title="Vehicle Analytics API",
    description="Vehicle detection and video analytics",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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


@app.get("/")
def home():
    return {"message": "Vehicle Analytics API is running", "docs": "/docs"}


@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "vehicle-analytics"}


@app.get("/api/stats")
def stats():
    database_stats = get_stats()
    return {
        **database_stats,
        "line_crossings": CURRENT_STATS["line_crossings"],
        "processed_frames": CURRENT_STATS["processed_frames"],
    }


@app.get("/api/detections")
def detections():
    records = get_recent_detections(100)
    result = []

    for record in records:
        record["class_name"] = record["vehicle_type"]
        result.append(record)

    return result


@app.delete("/api/detections")
def clear_detections():
    clear_database_detections()

    for key in CURRENT_STATS:
        CURRENT_STATS[key] = 0

    return {"message": "Detection records cleared"}


@app.post("/api/process-video")
async def process_video(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    extension = Path(file.filename).suffix.lower()
    allowed_extensions = {".mp4", ".avi", ".mov", ".mkv"}

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Upload an MP4, AVI, MOV, or MKV video",
        )

    video_path = OUTPUT_DIR / f"input_video{extension}"
    output_path = OUTPUT_DIR / "processed_video.mp4"

    try:
        content = await file.read()

        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        video_path.write_bytes(content)
    finally:
        await file.close()

    try:
        result = process_video_file(video_path, output_path)
        video_stats = result["stats"]
        video_detections = result["detections"]

        clear_database_detections()

        for item in video_detections:
            save_detection(
                vehicle_type=item.get("vehicle_type", item.get("class_name", "unknown")),
                color=item.get("color", "Unknown"),
                confidence=item.get("confidence", 0),
                track_id=item.get("track_id"),
            )

        CURRENT_STATS.update(video_stats)

        return {
            "message": "Video processing completed successfully",
            "status": "processed",
            "filename": video_path.name,
            "processed_video": "/outputs/processed_video.mp4",
            "output_video": "/outputs/processed_video.mp4",
            "stats": {**get_stats(), **{
                "line_crossings": CURRENT_STATS["line_crossings"],
                "processed_frames": CURRENT_STATS["processed_frames"],
            }},
            "detections": [
                {**item, "class_name": item.get("vehicle_type", item.get("class_name", "unknown"))}
                for item in video_detections
            ],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Video processing failed: {str(exc)}",
        ) from exc
