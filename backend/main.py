from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Vehicle Analytics API",
    description="Vehicle detection and video analytics",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")


@app.get("/")
def home():
    return {
        "message": "Vehicle Analytics API is running",
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "vehicle-analytics"}


@app.get("/api/stats")
def stats():
    return {
        "total_detections": 0,
        "cars": 0,
        "trucks": 0,
        "buses": 0,
        "motorcycles": 0,
        "line_crossings": 0,
    }


@app.get("/api/detections")
def detections():
    return []


@app.delete("/api/detections")
def clear_detections():
    return {"message": "Detection list cleared"}


@app.post("/api/process-video")
async def process_video(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    allowed_extensions = {".mp4", ".avi", ".mov", ".mkv"}
    extension = Path(file.filename).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Upload an MP4, AVI, MOV, or MKV video",
        )

    video_path = OUTPUT_DIR / f"input_video{extension}"

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        video_path.write_bytes(content)

        return {
            "message": "Video uploaded successfully. Detection processing is not connected yet.",
            "filename": video_path.name,
            "status": "uploaded",
        }
    finally:
        await file.close()
