from collections import defaultdict


class TrajectoryAnalyzer:

    def __init__(self):

        # Store center-point history for each vehicle
        self.trajectories = defaultdict(list)

    def get_center(self, bbox):

        x1, y1, x2, y2 = bbox

        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        return center_x, center_y

    def update(self, tracked_objects):

        for obj in tracked_objects:

            track_id = obj["track_id"]
            bbox = obj["bbox"]

            center = self.get_center(bbox)

            self.trajectories[track_id].append(
                center
            )

    def get_trajectory(self, track_id):

        return self.trajectories.get(
            track_id,
            []
        )