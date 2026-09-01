import xml.etree.ElementTree as ET
from datetime import datetime, timezone


GPX_NAMESPACE = {
    "gpx": "http://www.topografix.com/GPX/1/1"
}


class GPXParser:

    def __init__(self, gpx_path):
        self.gpx_path = gpx_path

    def parse(self):

        tree = ET.parse(self.gpx_path)
        root = tree.getroot()

        gps_points = []

        track_points = root.findall(
            ".//gpx:trkpt",
            GPX_NAMESPACE
        )

        for point in track_points:

            latitude = float(point.attrib["lat"])
            longitude = float(point.attrib["lon"])

            elevation_element = point.find(
                "gpx:ele",
                GPX_NAMESPACE
            )

            time_element = point.find(
                "gpx:time",
                GPX_NAMESPACE
            )

            elevation = None
            timestamp = None

            if elevation_element is not None:
                elevation = float(elevation_element.text)

            if time_element is not None:

                base_time = datetime.fromisoformat(
                    time_element.text.replace(
                        "Z",
                        "+00:00"
                    )
                )

                timestamp = base_time.astimezone(timezone.utc)

            gps_points.append({
                "timestamp": timestamp,
                "latitude": latitude,
                "longitude": longitude,
                "elevation": elevation
            })

        # Sort by timestamp just to be safe
        gps_points.sort(
            key=lambda point: point["timestamp"]
        )

        return gps_points