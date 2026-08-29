class VehicleCounter:

    def __init__(self, line_y):

        self.line_y = line_y

        # Previous center position of each tracked vehicle
        self.previous_positions = {}

        # IDs that have already been counted
        self.counted_ids = set()

        # Vehicle counts
        self.counts = {
            "car": 0,
            "motorcycle": 0,
            "bus": 0,
            "truck": 0
        }

    def get_center(self, bbox):

        x1, y1, x2, y2 = bbox

        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        return center_x, center_y

    def update(self, tracked_objects):

        crossing_events = []

        for obj in tracked_objects:

            track_id = obj["track_id"]

            class_name = obj["class_name"]

            bbox = obj["bbox"]

            center_x, center_y = self.get_center(bbox)

            # Get previous position
            previous_position = self.previous_positions.get(track_id)

            # Store current position
            self.previous_positions[track_id] = (
                center_x,
                center_y
            )

            # Need at least two positions
            if previous_position is None:
                continue

            previous_y = previous_position[1]

            # Has the vehicle crossed the line?
            crossed_down = (
                previous_y < self.line_y
                and center_y >= self.line_y
            )

            crossed_up = (
                previous_y > self.line_y
                and center_y <= self.line_y
            )

            if (
                (crossed_down or crossed_up)
                and track_id not in self.counted_ids
            ):

                direction = (
                    "DOWN"
                    if crossed_down
                    else "UP"
                )

                self.counted_ids.add(track_id)

                if class_name in self.counts:
                    self.counts[class_name] += 1

                crossing_events.append({
                    "track_id": track_id,
                    "vehicle_type": class_name,
                    "direction": direction
                })

        return crossing_events

    def get_counts(self):
        return self.counts.copy()