import cv2
from pathlib import Path

from cv_pipeline.tracker import TrafficTracker
from cv_pipeline.trajectory import TrajectoryAnalyzer



INPUT_VIDEO = Path(
    # "data/raw/highway/highway_1.mp4"
    "data/raw/normal/normal_1.mp4"
    # "data/raw/city/city_1.mp4"
)

OUTPUT_VIDEO = Path(
    # "outputs/videos/highway_1_trajectory.mp4"
    "outputs/videos/normal_1_trajectory.mp4"
    # "outputs/videos/city_1_trajectory.mp4"
)



def process_video():

    tracker = TrafficTracker()

    analyzer = TrajectoryAnalyzer(
        min_movement=50
    )

    cap = cv2.VideoCapture(
        str(INPUT_VIDEO)
    )

    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open video: {INPUT_VIDEO}"
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

    print(f"FPS: {fps}")
    print(
        f"Resolution: {width}x{height}"
    )

    OUTPUT_VIDEO.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )

    writer = cv2.VideoWriter(
        str(OUTPUT_VIDEO),
        fourcc,
        fps,
        (width, height)
    )

    frame_count = 0

    while True:

        success, frame = cap.read()

        if not success:
            break

        # Step 1: YOLO + ByteTrack
        tracked_objects = tracker.track(
            frame
        )

        # Step 2: Update trajectories
        movement_events = analyzer.update(
            tracked_objects
        )

        # Step 3: Draw tracked objects
        for obj in tracked_objects:

            track_id = obj["track_id"]

            x1, y1, x2, y2 = obj["bbox"]

            direction = analyzer.directions.get(
                track_id,
                "UNKNOWN"
            )

            label = (
                f'{obj["class_name"]} '
                f'ID:{track_id} '
                f'{direction}'
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

            # Draw trajectory
            trajectory = analyzer.get_trajectory(
                track_id
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

        counts = analyzer.get_counts()

        y_position = 40

        for direction, vehicles in counts.items():

            cv2.putText(
                frame,
                direction,
                (20, y_position),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2
            )

            y_position += 30

            for vehicle_type, count in vehicles.items():

                text = f"  {vehicle_type}: {count}"

                cv2.putText(
                    frame,
                    text,
                    (20, y_position),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2
                )

                y_position += 25

            y_position += 10

        # Print movement events
        for event in movement_events:

            print(
                "MOVEMENT EVENT:",
                event
            )

        writer.write(frame)

        frame_count += 1

        if frame_count % 100 == 0:

            print(
                f"Processed {frame_count} frames"
            )

    cap.release()
    writer.release()

    print("\nTrajectory analysis completed!")

    print("\nFINAL TRAFFIC COUNTS")
    print("=" * 40)

    counts = analyzer.get_counts()

    for direction, vehicles in counts.items():

        print(f"\n{direction}")

        for vehicle_type, count in vehicles.items():

            print(
                f"  {vehicle_type}: {count}"
            )

if __name__ == "__main__":
    process_video()