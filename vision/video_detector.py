import cv2
import subprocess
import imageio_ffmpeg
from pathlib import Path
from vision.pipeline import VehiclePipeline


def process_video_file(video_path, output_path):
    return process_video_source(video_path, output_path)


def process_video_source(video_source, output_path=None, max_frames=None):
    is_stream = isinstance(video_source, str) and video_source.lower().startswith(
        ("rtsp://", "rtsps://")
    )

    output = None
    temp_video = None
    writer = None

    if not is_stream:
        if output_path is None:
            raise ValueError("output_path is required for file processing")
        output = Path(output_path).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)

    if is_stream:
        capture = cv2.VideoCapture(video_source, cv2.CAP_FFMPEG)
        capture.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
        capture.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)
    else:
        capture = cv2.VideoCapture(str(Path(video_source).resolve()))

    if not capture.isOpened():
        raise RuntimeError(f"Could not open video source: {video_source}")

    pipeline = VehiclePipeline()
    vehicles_seen = {}
    crossing_events = []
    processed_frames = 0

    try:
        fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
        if fps <= 0:
            fps = 25.0

        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if not is_stream:
            if width <= 0 or height <= 0:
                raise RuntimeError("Invalid video dimensions")

            temp_video = output.with_name(output.stem + "_temp.mp4")
            writer = cv2.VideoWriter(
                str(temp_video),
                cv2.VideoWriter_fourcc(*"mp4v"),
                fps,
                (width, height),
            )
            if not writer.isOpened():
                raise RuntimeError(f"Could not create output video: {temp_video}")

        while max_frames is None or processed_frames < max_frames:
            success, frame = capture.read()
            if not success:
                if is_stream:
                    raise RuntimeError("RTSP stream disconnected or frame read failed")
                break

            height, width = frame.shape[:2]
            detections = pipeline.process_frame(frame)

            for item in detections:
                x1, y1, x2, y2 = map(int, item["bbox"])
                track_id = int(item["track_id"])
                vehicle_type = item["class_name"]
                color = item.get("color", "Unknown")
                direction = item.get("direction")

                vehicles_seen[track_id] = {
                    "track_id": track_id,
                    "vehicle_type": vehicle_type,
                    "class_name": vehicle_type,
                    "color": color,
                    "confidence": round(float(item.get("confidence", 0)), 3),
                    "bbox": [x1, y1, x2, y2],
                }

                if item.get("line_crossed") and direction in ("up", "down"):
                    crossing_events.append({
                        "vehicle_id": str(track_id),
                        "color": color,
                        "direction": direction,
                        "frame_number": processed_frames + 1,
                    })

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

            if writer is not None:
                writer.write(frame)

            processed_frames += 1

            if processed_frames % 50 == 0:
                print(f"Processed {processed_frames} frames")

    finally:
        capture.release()
        if writer is not None:
            writer.release()

    if processed_frames == 0:
        raise RuntimeError("No frames were processed")

    if not is_stream:
        try:
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            result = subprocess.run(
                [
                    ffmpeg, "-y", "-i", str(temp_video),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", "-an", str(output),
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(f"H.264 conversion failed: {result.stderr[-2000:]}")
        finally:
            if temp_video:
                temp_video.unlink(missing_ok=True)

    counts = {"cars": 0, "trucks": 0, "buses": 0, "motorcycles": 0}
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
        "crossing_events": crossing_events,
    }
