import math

class VehicleTracker:
    def __init__(self, max_distance=70):
        self.max_distance = max_distance
        self.next_id = 1
        self.tracks = {}

    def update(self, detections):
        # detections: list of dictionaries with bbox, class_name, confidence
        updated = {}
        unmatched = set(self.tracks.keys())

        for detection in detections:
            x1, y1, x2, y2 = detection["bbox"]
            center = ((x1 + x2) // 2, (y1 + y2) // 2)
            best_id, best_dist = None, self.max_distance

            for track_id in list(unmatched):
                old = self.tracks[track_id]["center"]
                distance = math.dist(center, old)
                if distance < best_dist:
                    best_id, best_dist = track_id, distance

            if best_id is None:
                best_id = self.next_id
                self.next_id += 1
            else:
                unmatched.discard(best_id)

            updated[best_id] = {
                "center": center,
                **detection,
                "track_id": best_id,
            }

        self.tracks = updated
        return list(updated.values())
