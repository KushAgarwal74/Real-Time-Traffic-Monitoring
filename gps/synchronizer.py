from bisect import bisect_left


class GPSSynchronizer:

    def __init__(self, gps_points):
        self.gps_points = gps_points

        # Extract timestamps separately for efficient searching
        self.timestamps = [
            point["timestamp"]
            for point in gps_points
        ]

    def get_location(self, target_timestamp):
        """
        Returns interpolated GPS location for a given timestamp.
        """

        # Before first GPS point
        if target_timestamp <= self.timestamps[0]:
            return self.gps_points[0]

        # After last GPS point
        if target_timestamp >= self.timestamps[-1]:
            return self.gps_points[-1]

        # Find where target timestamp belongs
        index = bisect_left(
            self.timestamps,
            target_timestamp
        )

        previous_point = self.gps_points[index - 1]
        next_point = self.gps_points[index]

        previous_time = previous_point["timestamp"]
        next_time = next_point["timestamp"]

        total_seconds = (
            next_time - previous_time
        ).total_seconds()

        elapsed_seconds = (
            target_timestamp - previous_time
        ).total_seconds()

        # How far between the two GPS points?
        ratio = elapsed_seconds / total_seconds

        latitude = (
            previous_point["latitude"]
            +
            ratio
            * (
                next_point["latitude"]
                - previous_point["latitude"]
            )
        )

        longitude = (
            previous_point["longitude"]
            +
            ratio
            * (
                next_point["longitude"]
                - previous_point["longitude"]
            )
        )

        elevation = None

        if (
            previous_point["elevation"] is not None
            and next_point["elevation"] is not None
        ):
            elevation = (
                previous_point["elevation"]
                +
                ratio
                * (
                    next_point["elevation"]
                    - previous_point["elevation"]
                )
            )

        return {
            "timestamp": target_timestamp,
            "latitude": latitude,
            "longitude": longitude,
            "elevation": elevation
        }