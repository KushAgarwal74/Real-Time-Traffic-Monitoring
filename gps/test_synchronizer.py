from datetime import timedelta

from gps.gpx_parser import GPXParser
from gps.synchronizer import GPSSynchronizer


GPX_FILE = "data/raw/gps/traffic_1.gpx"


def main():

    # Parse GPX
    parser = GPXParser(GPX_FILE)

    gps_points = parser.parse()

    # Create synchronizer
    synchronizer = GPSSynchronizer(gps_points)

    first_point = gps_points[0]

    print("\nFIRST GPS POINT")
    print(first_point)

    # Ask for location half a second later
    target_time = (
        first_point["timestamp"]
        + timedelta(seconds=0.5)
    )

    location = synchronizer.get_location(target_time)

    print("\nINTERPOLATED LOCATION")
    print(location)


if __name__ == "__main__":
    main()