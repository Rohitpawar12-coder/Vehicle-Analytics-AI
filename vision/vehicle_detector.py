from ultralytics import YOLO

VEHICLE_CLASSES = [2, 3, 5, 7]

VEHICLE_CLASS_NAMES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


class VehicleDetector:
    def __init__(self, model_path="yolo11n.pt", confidence=0.20):
        self.model = YOLO(model_path)
        self.confidence = confidence

    def detect(self, frame):
        results = self.model.track(
            source=frame,
            persist=True,
            tracker="bytetrack.yaml",
            classes=VEHICLE_CLASSES,
            conf=self.confidence,
            iou=0.5,
            verbose=False,
        )

        detections = []

        if not results or results[0].boxes is None:
            return detections

        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            class_id = int(box.cls[0].item())

            track_id = None
            if box.id is not None:
                track_id = int(box.id[0].item())

            detections.append({
                "bbox": (int(x1), int(y1), int(x2), int(y2)),
                "class_name": VEHICLE_CLASS_NAMES.get(class_id, "vehicle"),
                "confidence": float(box.conf[0].item()),
                "track_id": track_id,
            })

        return detections
