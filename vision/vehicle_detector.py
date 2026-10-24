from ultralytics import YOLO

VEHICLE_CLASSES = [2, 3, 5, 7]


class VehicleDetector:
    def __init__(self, model_path="yolo11n.pt", confidence=0.35):
        self.model = YOLO(model_path)
        self.confidence = confidence

    def detect(self, frame):
        results = self.model.predict(
            source=frame,
            classes=VEHICLE_CLASSES,
            conf=self.confidence,
            verbose=False
        )

        detections = []

        if not results or results[0].boxes is None:
            return detections

        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            detections.append({
                "bbox": (int(x1), int(y1), int(x2), int(y2)),
                "class_name": self.model.names[class_id],
                "confidence": confidence
            })

        return detections
