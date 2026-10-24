class LineCounter:
    def __init__(self, y_position_ratio=0.6):
        self.y_position_ratio = y_position_ratio
        self.previous_positions = {}
        self.counted_ids = set()
        self.total = 0

    def update(self, track_id, center_y, frame_height):
        line_y = int(frame_height * self.y_position_ratio)
        previous_y = self.previous_positions.get(track_id)
        self.previous_positions[track_id] = center_y

        if previous_y is None or track_id in self.counted_ids:
            return False

        crossed_up = previous_y > line_y >= center_y
        crossed_down = previous_y < line_y <= center_y

        if crossed_up or crossed_down:
            self.counted_ids.add(track_id)
            self.total += 1
            return "up" if crossed_up else "down"

        return False
