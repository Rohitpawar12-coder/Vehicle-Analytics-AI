import math


class VehicleTracker:
    def __init__(self, max_distance=100, max_missing=10):
        self.max_distance = max_distance
        self.max_missing = max_missing
        self.next_id = 1
        self.tracks = {}

    def update(self, detections):
        updated = {}
        unmatched = set(self.tracks.keys())

        for detection in detections:
            x1, y1, x2, y2 = detection["bbox"]
            center = ((x1 + x2) // 2, (y1 + y2) // 2)
            class_name = detection.get("class_name", "car").lower()

            # Use ByteTrack ID when available.
            raw_id = detection.get("track_id")

            if raw_id is not None:
                track_id = int(raw_id)
                self.next_id = max(self.next_id, track_id + 1)
                unmatched.discard(track_id)
            else:
                # Fallback matching for detections without a tracker ID.
                best_id = None
                best_dist = self.max_distance

                for candidate_id in unmatched:
                    previous = self.tracks[candidate_id]

                    if previous.get("class_name", "car").lower() != class_name:
                        continue

                    distance = math.dist(center, previous["center"])
                    if distance < best_dist:
                        best_dist = distance
                        best_id = candidate_id

                if best_id is None:
                    track_id = self.next_id
                    self.next_id += 1
                else:
                    track_id = best_id
                    unmatched.discard(track_id)

            updated[track_id] = {
                **detection,
                "track_id": track_id,
                "center": center,
                "missing_frames": 0,
            }

        for track_id in unmatched:
            previous = self.tracks[track_id]
            missing = previous.get("missing_frames", 0) + 1

            if missing <= self.max_missing:
                updated[track_id] = {
                    **previous,
                    "missing_frames": missing,
                }

        self.tracks = updated

        return [
            item for item in updated.values()
            if item.get("missing_frames", 0) == 0
        ]
