from .vehicle_detector import VehicleDetector
from .color_classifier import ColorClassifier
from .vehicle_tracker import VehicleTracker
from .line_counter import LineCounter


class VehiclePipeline:
    def __init__(self):
        self.detector = VehicleDetector()
        self.color_classifier = ColorClassifier()
        self.tracker = VehicleTracker()
        self.line_counter = LineCounter()

    def process_frame(self, frame):
        detections = self.detector.detect(frame)
        tracked = self.tracker.update(detections)
        results = []

        for item in tracked:
            x1, y1, x2, y2 = map(int, item["bbox"])

            crop = frame[
                max(0, y1):max(0, y2),
                max(0, x1):max(0, x2)
            ]

            color = self.color_classifier.classify(crop)

            direction = self.line_counter.update(
                item["track_id"],
                item["center"][1],
                frame.shape[0]
            )

            item["color"] = color
            item["line_crossed"] = bool(direction)
            item["direction"] = direction if direction else None

            results.append(item)

        return results
