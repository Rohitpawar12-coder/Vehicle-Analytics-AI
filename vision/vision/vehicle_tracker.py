"""Minimal centroid tracker utility for future integration."""
import math

class CentroidTracker:
    def __init__(self, max_distance=80):
        self.max_distance = max_distance
        self.next_id = 1
        self.objects = {}

    def update(self, boxes):
        """boxes is a list of (x1, y1, x2, y2). Returns [(track_id, box), ...]."""
        results = []
        unused_ids = set(self.objects.keys())
        new_objects = {}
        for box in boxes:
            x1, y1, x2, y2 = box
            center = ((x1 + x2) // 2, (y1 + y2) // 2)
            best_id, best_dist = None, self.max_distance
            for object_id in unused_ids:
                old_center = self.objects[object_id][0]
                distance = math.dist(center, old_center)
                if distance < best_dist:
                    best_id, best_dist = object_id, distance
            if best_id is None:
                best_id = self.next_id
                self.next_id += 1
            else:
                unused_ids.remove(best_id)
            new_objects[best_id] = (center, box)
            results.append((best_id, box))
        self.objects = new_objects
        return results
