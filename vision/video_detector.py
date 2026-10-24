import cv2
import subprocess
import imageio_ffmpeg
from pathlib import Path
from vision.pipeline import VehiclePipeline


def process_video_file(video_path, output_path):
    video_path = Path(video_path).resolve()
    output_path = Path(output_path).resolve()

    capture = cv2.VideoCapture(str(video_path))

    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = capture.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 25.0

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if width <= 0 or height <= 0:
        capture.release()
        raise RuntimeError("Invalid video dimensions")

    temp_video = output_path.with_name(output_path.stem + "_temp.mp4")

    writer = cv2.VideoWriter(
        str(temp_video),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    if not writer.isOpened():
        capture.release()
        raise RuntimeError(f"Could not create output video: {temp_video}")

    pipeline = VehiclePipeline()
    vehicles_seen = {}
    processed_frames = 0

    try:
        while True:
            success, frame = capture.read()
            if not success:
                break

            detections = pipeline.process_frame(frame)

            for item in detections:
                x1, y1, x2, y2 = map(int, item["bbox"])
                track_id = int(item["track_id"])
                vehicle_type = item["class_name"]
                color = item.get("color", "Unknown")

                vehicles_seen[track_id] = {
                    "track_id": track_id,
                    "vehicle_type": vehicle_type,
                    "class_name": vehicle_type,
                    "color": color,
                    "confidence": round(float(item.get("confidence", 0)), 3),
                    "bbox": [x1, y1, x2, y2],
                }

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    f"ID {track_id} | {vehicle_type} | {color}",
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2,
                )

            line_y = int(height * pipeline.line_counter.y_position_ratio)
            cv2.line(frame, (0, line_y), (width, line_y), (0, 0, 255), 2)
            cv2.putText(
                frame,
                f"Line crossings: {pipeline.line_counter.total}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2,
            )

            writer.write(frame)
            processed_frames += 1

            if processed_frames % 50 == 0:
                print(f"Processed {processed_frames} frames")

    finally:
        capture.release()
        writer.release()

    if processed_frames == 0:
        temp_video.unlink(missing_ok=True)
        raise RuntimeError("No frames were processed")

    try:
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

        command = [
            ffmpeg,
            "-y",
            "-i", str(temp_video),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-an",
            str(output_path),
        ]

        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"H.264 conversion failed: {result.stderr[-2000:]}")

    finally:
        temp_video.unlink(missing_ok=True)

    counts = {
        "cars": 0,
        "trucks": 0,
        "buses": 0,
        "motorcycles": 0,
    }

    for item in vehicles_seen.values():
        kind = item["vehicle_type"].lower()

        if kind == "car":
            counts["cars"] += 1
        elif kind == "truck":
            counts["trucks"] += 1
        elif kind == "bus":
            counts["buses"] += 1
        elif kind in ("motorcycle", "motorbike"):
            counts["motorcycles"] += 1

    return {
        "stats": {
            "total_detections": len(vehicles_seen),
            **counts,
            "line_crossings": pipeline.line_counter.total,
            "processed_frames": processed_frames,
        },
        "detections": list(vehicles_seen.values()),
    }
