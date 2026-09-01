
from gps.video_gps_sync import (
    VideoGPSSynchronizer
)


VIDEO_FILE = (
    "data/raw/city/traffic_1.mp4"
    # "data/raw/city/traffic_2.mp4"
)

GPX_FILE = (
    "data/raw/gps/traffic_1.gpx"
    # "data/raw/gps/traffic_2.gpx"
)


def main():

    sync = VideoGPSSynchronizer(
        video_path=VIDEO_FILE,
        gpx_path=GPX_FILE,
        metadata_represents="end"
    )

    print("\nVIDEO GPS SYNCHRONIZATION")
    print("=" * 60)

    print(f"FPS: {sync.fps}")

    print(
        f"Frame Count: "
        f"{sync.frame_count}"
    )

    print(
        f"Duration: "
        f"{sync.duration_seconds:.2f} seconds"
    )

    print()

    print(
        f"Video Start: "
        f"{sync.video_start_time}"
    )

    print(
        f"Video End:   "
        f"{sync.video_end_time}"
    )

    print()

    print(
        f"GPS Start: "
        f"{sync.gps_start_time}"
    )

    print(
        f"GPS End:   "
        f"{sync.gps_end_time}"
    )

    print("\n" + "=" * 60)
    print("FRAME GPS TEST")
    print("=" * 60)

    test_frames = [

        0,

        sync.frame_count // 4,

        sync.frame_count // 2,

        (sync.frame_count * 3) // 4,

        sync.frame_count - 1
    ]

    for frame_number in test_frames:

        telemetry = (
            sync.get_frame_telemetry(
                frame_number
            )
        )

        print()

        print(
            f"Frame: {frame_number}"
        )

        print(
            f"Time: "
            f"{telemetry['timestamp']}"
        )

        if telemetry["gps"]:

            print(
                f"Latitude: "
                f"{telemetry['gps']['latitude']}"
            )

            print(
                f"Longitude: "
                f"{telemetry['gps']['longitude']}"
            )

        else:

            print(
                "GPS: NOT AVAILABLE"
            )


if __name__ == "__main__":
    main()