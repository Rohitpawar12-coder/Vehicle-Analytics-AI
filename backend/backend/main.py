from pathlib import Path
from collections import Counter
import shutil
import uuid

import cv2
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from ultralytics import YOLO

from backend.database import init_db, save_detection, get_stats, get_recent_detections, clear_detections
from backend.vision import process_video

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "sample_videos" / "uploads"
OUTPUT_DIR = BASE_DIR / "sample_videos" / "processed"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Vehicle Analytics API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

_model = None

def get_model():
    global _model
    if _model is None:
        # First run downloads the small YOLO model automatically.
        _model = YOLO("yolo11n.pt")
    return _model

@app.on_event("startup")
def startup():
    init_db()

@app.get("/api/health")
def health():
    return {"status": "ok", "message": "Vehicle Analytics API is running"}

@app.get("/api/stats")
def stats():
    return get_stats()

@app.get("/api/detections")
def detections(limit: int = 50):
    return get_recent_detections(max(1, min(limit, 500)))

@app.delete("/api/detections")
def delete_all_detections():
    clear_detections()
    return {"message": "Detection history cleared"}

@app.post("/api/process-video")
async def process_video_endpoint(file: UploadFile = File(...)):
    allowed = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    suffix = Path(file.filename or "video.mp4").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail="Upload an MP4, AVI, MOV, MKV, or WEBM video.")

    job_id = uuid.uuid4().hex[:10]
    input_path = UPLOAD_DIR / f"{job_id}{suffix}"
    output_path = OUTPUT_DIR / f"{job_id}_annotated.mp4"

    try:
        with input_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        model = get_model()
        result = process_video(model, input_path, output_path, save_detection)
        return {
            "message": "Video processed successfully",
            "job_id": job_id,
            "video_url": f"/outputs/{output_path.name}",
            **result,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Video processing failed: {exc}") from exc
    finally:
        await file.close()
