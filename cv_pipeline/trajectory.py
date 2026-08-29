from collections import defaultdict


class TrajectoryAnalyzer:

    def __init__(self, min_movement=50):

        self.min_movement = min_movement

        # Track center-point history
        self.trajectories = defaultdict(list)

        # Current direction for each track
        self.directions = {}

        # Vehicles already counted
        self.counted_ids = set()

        # Direction-wise counts
        self.counts = {
            "UP": {
                "car": 0,
                "motorcycle": 0,
                "bus": 0,
                "truck": 0
            },
            "DOWN": {
                "car": 0,
                "motorcycle": 0,
                "bus": 0,
                "truck": 0
            },
            "LEFT": {
                "car": 0,
                "motorcycle": 0,
                "bus": 0,
                "truck": 0
            },
            "RIGHT": {
                "car": 0,
                "motorcycle": 0,
                "bus": 0,
                "truck": 0
            }
        }

    def get_center(self, bbox):

        x1, y1, x2, y2 = bbox

        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        return center_x, center_y

    def update(self, tracked_objects):

        movement_events = []

        for obj in tracked_objects:

            track_id = obj["track_id"]
            class_name = obj["class_name"]
            bbox = obj["bbox"]

            center = self.get_center(bbox)

            # Store center point
            self.trajectories[track_id].append(center)

            trajectory = self.trajectories[track_id]

            if len(trajectory) < 2:
                continue

            start_x, start_y = trajectory[0]
            current_x, current_y = trajectory[-1]

            delta_x = current_x - start_x
            delta_y = current_y - start_y

            movement_distance = (
                delta_x ** 2 +
                delta_y ** 2
            ) ** 0.5

            # Ignore small jitter
            if movement_distance < self.min_movement:
                continue

            direction = self.get_direction(
                delta_x,
                delta_y
            )

            previous_direction = self.directions.get(track_id)

            self.directions[track_id] = direction

            # Count vehicle only once
            if track_id not in self.counted_ids:

                self.counted_ids.add(track_id)

                if class_name in self.counts[direction]:

                    self.counts[direction][class_name] += 1

                movement_events.append({
                    "track_id": track_id,
                    "vehicle_type": class_name,
                    "direction": direction,
                    "delta_x": delta_x,
                    "delta_y": delta_y,
                    "movement_pixels": round(
                        movement_distance,
                        2
                    )
                })

            # Direction changed
            elif previous_direction != direction:

                movement_events.append({
                    "track_id": track_id,
                    "vehicle_type": class_name,
                    "direction": direction,
                    "event": "DIRECTION_CHANGED"
                })

        return movement_events

    def get_direction(self, delta_x, delta_y):

        if abs(delta_x) > abs(delta_y):

            if delta_x > 0:
                return "RIGHT"

            return "LEFT"

        else:

            if delta_y > 0:
                return "DOWN"

            return "UP"

    def get_trajectory(self, track_id):

        return self.trajectories.get(
            track_id,
            []
        )

    def get_counts(self):

        return self.counts