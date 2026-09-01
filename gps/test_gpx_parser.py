from gps.gpx_parser import GPXParser


GPX_FILE = "data/raw/gps/traffic_1.gpx"


def main():

    parser = GPXParser(GPX_FILE)

    gps_points = parser.parse()

    print("\nGPS PARSING COMPLETED")
    print("=" * 50)

    print(f"Total GPS points: {len(gps_points)}")

    if gps_points:

        print("\nFIRST POINT:")
        print(gps_points[0])

        print("\nLAST POINT:")
        print(gps_points[-1])

        print("\nFIRST 5 POINTS:")

        for point in gps_points[:5]:
            print(point)


if __name__ == "__main__":
    main()