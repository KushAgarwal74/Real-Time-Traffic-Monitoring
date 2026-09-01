import cv2
import json
from datetime import datetime, timezone
from pathlib import Path

from cv_pipeline.tracker import TrafficTracker
from cv_pipeline.trajectory import TrajectoryAnalyzer
from cv_pipeline.vehicle_state import VehicleStateManager

from gps.video_gps_sync import VideoGPSSynchronizer

from events.event_store import EventStore


INPUT_VIDEO = Path(
    "data/raw/city/traffic_1.mp4"
)

GPX_FILE = Path(
    "data/raw/gps/traffic_1.gpx"
)

OUTPUT_DIR = Path(
    "data/processed/traffic_1"
)

OUTPUT_VIDEO = Path(
    "outputs/videos/traffic_1_processed.mp4"
)

def process_video():

    # ----------------------------------------
    # Create components
    # ----------------------------------------

    tracker = TrafficTracker()

    trajectory_analyzer = TrajectoryAnalyzer()

    vehicle_manager = VehicleStateManager(
        exit_after_frames=90,
        update_interval_frames=30
    )

    # ----------------------------------------
    # Video
    # ----------------------------------------

    cap = cv2.VideoCapture(
        str(INPUT_VIDEO)
    )

    if not cap.isOpened():

        raise RuntimeError(
            f"Could not open: {INPUT_VIDEO}"
        )

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    width = int(
        cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    )

    height = int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    )

    frame_total = int(
        cap.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    print("\nVIDEO INFORMATION")

    print(f"FPS: {fps}")

    print(f"Resolution: {width}x{height}")

    print(f"Total Frames: {frame_total}")

    # ----------------------------------------
    # Output directories
    # ----------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_VIDEO.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # ----------------------------------------
    # Video writer
    # ----------------------------------------

    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )

    writer = cv2.VideoWriter(
        str(OUTPUT_VIDEO),
        fourcc,
        fps,
        (width, height)
    )

    # ----------------------------------------
    # Event storage
    # ----------------------------------------

    event_store = EventStore(
        OUTPUT_DIR / "events.jsonl"
    )

    # ----------------------------------------
    # GPS Synchronizer
    # ----------------------------------------

    gps_sync = None

    try:

        gps_sync = VideoGPSSynchronizer(
            video_path=str(INPUT_VIDEO),
            gpx_path=str(GPX_FILE),
            metadata_represents="end"
        )

        print("\nGPS synchronization enabled")

    except Exception as e:

        print(
            f"\nGPS synchronization disabled: {e}"
        )

    # ----------------------------------------
    # Statistics
    # ----------------------------------------

    vehicle_counts = {

        "car": set(),

        "motorcycle": set(),

        "bus": set(),

        "truck": set()
    }

    event_counts = {

        "vehicle_detected": 0,

        "vehicle_updated": 0,

        "vehicle_exited": 0
    }

    frame_number = 0

    # ----------------------------------------
    # Main processing loop
    # ----------------------------------------

    while True:

        success, frame = cap.read()

        if not success:
            break

        # ------------------------------------
        # YOLO + ByteTrack
        # ------------------------------------

        tracked_objects = tracker.track(
            frame
        )

        # ------------------------------------
        # GPS
        # ------------------------------------

        timestamp = None
        camera_gps = None

        if gps_sync:

            telemetry = (
                gps_sync.get_frame_telemetry(
                    frame_number
                )
            )

            timestamp = telemetry["timestamp"]

            camera_gps = telemetry["gps"]

        # ------------------------------------
        # Fallback timestamp
        # ------------------------------------

        # if timestamp is None:

        #     timestamp = datetime.now(
        #         timezone.utc
        #     )

        # ------------------------------------
        # Update trajectories
        # ------------------------------------

        trajectory_analyzer.update(
            tracked_objects
        )

        # ------------------------------------
        # Vehicle lifecycle events
        # ------------------------------------

        # ------------------------------------
        # Vehicle lifecycle events
        # ------------------------------------

        lifecycle_events = vehicle_manager.update(
            tracked_objects=tracked_objects,
            frame_number=frame_number,
            timestamp=timestamp,
            camera_gps=camera_gps
        )

        for event in lifecycle_events:

            event_store.write_event(event)

            event_type = event["event_type"]

            if event_type in event_counts:

                event_counts[event_type] += 1

        # ------------------------------------
        # Track unique vehicles
        # ------------------------------------

        for obj in tracked_objects:

            vehicle_type = obj["class_name"]

            track_id = obj["track_id"]

            if vehicle_type in vehicle_counts:

                vehicle_counts[
                    vehicle_type
                ].add(track_id)

        # ------------------------------------
        # Draw objects
        # ------------------------------------

        for obj in tracked_objects:

            track_id = obj["track_id"]

            vehicle_type = obj["class_name"]

            x1, y1, x2, y2 = obj["bbox"]

            label = (
                f"{vehicle_type} "
                f"ID:{track_id}"
            )

            cv2.rectangle(

                frame,

                (x1, y1),

                (x2, y2),

                (0, 255, 0),

                2
            )

            cv2.putText(

                frame,

                label,

                (x1, y1 - 10),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.6,

                (0, 255, 0),

                2
            )

            # ------------------------------
            # Draw trajectory
            # ------------------------------

            trajectory = (
                trajectory_analyzer.get_trajectory(
                    track_id
                )
            )

            if len(trajectory) > 1:

                for i in range(
                    1,
                    len(trajectory)
                ):

                    cv2.line(

                        frame,

                        trajectory[i - 1],

                        trajectory[i],

                        (255, 0, 0),

                        2
                    )

        # ------------------------------------
        # Display counts
        # ------------------------------------

        y_position = 40

        cv2.putText(

            frame,

            "VEHICLES",

            (20, y_position),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (0, 255, 255),

            2
        )

        y_position += 35

        for vehicle_type, ids in vehicle_counts.items():

            text = (
                f"{vehicle_type}: "
                f"{len(ids)}"
            )

            cv2.putText(

                frame,

                text,

                (20, y_position),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.6,

                (255, 255, 255),

                2
            )

            y_position += 30

        # ------------------------------------
        # Write frame
        # ------------------------------------

        writer.write(frame)

        frame_number += 1

        if frame_number % 100 == 0:

            print(

                f"Processed {frame_number}/"
                f"{frame_total} frames"
            )

    # ----------------------------------------
    # Cleanup
    # ----------------------------------------

    cap.release()

    writer.release()

    event_store.close()

    # ----------------------------------------
    # Summary
    # ----------------------------------------

    summary = {

        "video": str(INPUT_VIDEO),

        "total_frames": frame_total,

        "fps": fps,

        "unique_vehicles": {

            vehicle_type: len(ids)

            for vehicle_type, ids

            in vehicle_counts.items()
        },

        "event_counts": event_counts
    }

    summary_path = (
        OUTPUT_DIR / "summary.json"
    )

    with open(
        summary_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(

            summary,

            file,

            indent=4
        )

    # ----------------------------------------
    # Terminal output
    # ----------------------------------------

    print("\nPROCESSING COMPLETE")

    print("=" * 50)

    print("\nUNIQUE VEHICLES")

    for vehicle_type, ids in vehicle_counts.items():

        print(
            f"{vehicle_type}: {len(ids)}"
        )

    print("\nEVENTS")

    for event_type, count in event_counts.items():

        print(
            f"{event_type}: {count}"
        )

    print("\nOUTPUTS")

    print(f"Video: {OUTPUT_VIDEO}")

    print(
        f"Events: "
        f"{OUTPUT_DIR / 'events.jsonl'}"
    )

    print(
        f"Summary: "
        f"{summary_path}"
    )


if __name__ == "__main__":

    process_video()