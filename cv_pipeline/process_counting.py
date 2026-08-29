import cv2
from pathlib import Path

from cv_pipeline.tracker import TrafficTracker
from cv_pipeline.counter import VehicleCounter


INPUT_VIDEO = Path(
    # "data/raw/highway/highway_1.mp4"
    # "data/raw/normal/normal_1.mp4"
    "data/raw/city/city_1.mp4"
)

OUTPUT_VIDEO = Path(
    # "outputs/videos/highway_1_counted.mp4"
    # "outputs/videos/normal_1_counted.mp4"
    "outputs/videos/city_1_counted.mp4"
)


def process_video():

    tracker = TrafficTracker()

    cap = cv2.VideoCapture(str(INPUT_VIDEO))

    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open video: {INPUT_VIDEO}"
        )

    fps = cap.get(cv2.CAP_PROP_FPS)

    width = int(cap.get(
        cv2.CAP_PROP_FRAME_WIDTH
    ))

    height = int(cap.get(
        cv2.CAP_PROP_FRAME_HEIGHT
    ))

    print(f"FPS: {fps}")
    print(f"Resolution: {width}x{height}")

    # Counting line
    line_y = int(height * 0.52)  # Middle of the frame

    counter = VehicleCounter(
        line_y=line_y
    )

    OUTPUT_VIDEO.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

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

        # Tracking
        tracked_objects = tracker.track(frame)

        # Update counter
        crossing_events = counter.update(
            tracked_objects
        )

        # Draw counting line
        cv2.line(
            frame,
            (0, line_y),
            (width, line_y),
            (0, 0, 255),
            3
        )

        # Draw tracked objects
        for obj in tracked_objects:

            x1, y1, x2, y2 = obj["bbox"]

            label = (
                f'{obj["class_name"]} '
                f'ID:{obj["track_id"]}'
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

        # Show counts
        counts = counter.get_counts()

        y_position = 40

        for vehicle_type, count in counts.items():

            text = (
                f"{vehicle_type}: {count}"
            )

            cv2.putText(
                frame,
                text,
                (20, y_position),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            y_position += 35

        # Print crossing events
        for event in crossing_events:

            print(
                f"CROSSING EVENT: "
                f"{event}"
            )

        writer.write(frame)

        frame_count += 1

        if frame_count % 100 == 0:

            print(
                f"Processed {frame_count} frames | "
                f"Counts: {counts}"
            )

    cap.release()
    writer.release()

    print("\nCounting completed!")

    print("\nFINAL COUNTS:")

    for vehicle_type, count in (
        counter.get_counts().items()
    ):

        print(
            f"{vehicle_type}: {count}"
        )

    print(f"\nOutput: {OUTPUT_VIDEO}")


if __name__ == "__main__":
    process_video()