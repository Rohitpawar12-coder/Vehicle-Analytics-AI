from pathlib import Path
from ultralytics import YOLO
from backend.vision import process_video
from backend.database import init_db, save_detection

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT = BASE_DIR / "sample_videos" / "traffic.mp4"
OUTPUT = BASE_DIR / "sample_videos" / "traffic_detected.mp4"

def main():
    if not INPUT.exists():
        print(f"Video not found: {INPUT}")
        print("Upload a video from the dashboard or place traffic.mp4 in sample_videos.")
        return
    init_db()
    print("Loading YOLO model (first run downloads it)...")
    model = YOLO("yolo11n.pt")
    result = process_video(model, INPUT, OUTPUT, save_detection)
    print("Finished:", result)
    print("Output saved to:", OUTPUT)

if __name__ == "__main__":
    main()
