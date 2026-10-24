"""Line-crossing counter helper. Feed each tracked object's center on each frame."""
class LineCrossingCounter:
    def __init__(self, y_line):
        self.y_line = y_line
        self.previous_side = {}
        self.count = 0

    def update(self, track_id, center_y):
        side = center_y >= self.y_line
        previous = self.previous_side.get(track_id)
        self.previous_side[track_id] = side
        if previous is not None and previous != side:
            self.count += 1
            return True
        return False
