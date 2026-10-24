from collections import Counter
import cv2

VEHICLE_CLASS_NAMES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

def estimate_color(crop):
    """Simple dominant-color estimate; this is a baseline, not a trained classifier."""
    if crop is None or crop.size == 0:
        return "Unknown"
    crop = cv2.resize(crop, (64, 64))
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    h, s, v = hsv.mean(axis=(0, 1))
    if v < 55:
        return "Black"
    if s < 35 and v > 190:
        return "White"
    if s < 35:
        return "Gray"
    if h < 10 or h >= 170:
        return "Red"
    if h < 22:
        return "Orange"
    if h < 35:
        return "Yellow"
    if h < 85:
        return "Green"
    if h < 130:
        return "Blue"
    return "Purple"

def process_video(model, input_path, output_path, save_callback):
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise ValueError("OpenCV could not open the uploaded video.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if width <= 0 or height <= 0:
        cap.release()
        raise ValueError("The uploaded video has invalid dimensions.")

    writer = cv2.VideoWriter(
        str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )
    if not writer.isOpened():
        cap.release()
        raise ValueError("Could not create the output video.")

    frame_number = 0
    total_vehicle_detections = 0
    type_counts = Counter()
    color_counts = Counter()
    # Simple centroid-based IDs are assigned per frame; full persistent tracking is not enabled here.
    next_track_id = 1

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_number += 1
            # Process every frame for the baseline. CPU users can reduce resolution if it is slow.
            prediction = model.predict(frame, classes=list(VEHICLE_CLASS_NAMES), conf=0.35, verbose=False)[0]
            annotated = frame.copy()

            for box in prediction.boxes:
                cls_id = int(box.cls[0].item())
                vehicle_type = VEHICLE_CLASS_NAMES.get(cls_id, "vehicle")
                confidence = float(box.conf[0].item())
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(width, x2), min(height, y2)
                crop = frame[y1:y2, x1:x2]
                color = estimate_color(crop)
                track_id = next_track_id
                next_track_id += 1

                cv2.rectangle(annotated, (x1, y1), (x2, y2), (40, 220, 120), 2)
                label = f"{vehicle_type} | {color} | {confidence:.2f}"
                cv2.putText(annotated, label, (x1, max(22, y1 - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (40, 220, 120), 2)

                save_callback(vehicle_type, color, confidence, track_id, frame_number)
                total_vehicle_detections += 1
                type_counts[vehicle_type] += 1
                color_counts[color] += 1

            cv2.line(annotated, (0, int(height * 0.65)), (width, int(height * 0.65)), (0, 200, 255), 2)
            cv2.putText(annotated, "Counting line (prototype)", (15, int(height * 0.65) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
            writer.write(annotated)
    finally:
        cap.release()
        writer.release()

    return {
        "frames_processed": frame_number,
        "vehicle_detections": total_vehicle_detections,
        "by_type": [{"name": k, "count": v} for k, v in type_counts.most_common()],
        "by_color": [{"name": k, "count": v} for k, v in color_counts.most_common()],
    }
