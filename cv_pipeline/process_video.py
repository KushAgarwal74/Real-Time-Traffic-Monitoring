import cv2
from pathlib import Path

from cv_pipeline.detector import TrafficDetector


INPUT_VIDEO = Path(
    "data/raw/highway/highway_1.mp4"
)

OUTPUT_VIDEO = Path(
    "outputs/videos/highway_1_detected.mp4"
)


def process_video():

    detector = TrafficDetector()

    cap = cv2.VideoCapture(str(INPUT_VIDEO))

    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open video: {INPUT_VIDEO}"
        )

    fps = cap.get(cv2.CAP_PROP_FPS)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"FPS: {fps}")
    print(f"Resolution: {width}x{height}")

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

        detections = detector.detect(frame)

        for detection in detections:

            x1, y1, x2, y2 = detection["bbox"]

            label = (
                f'{detection["class_name"]} '
                f'{detection["confidence"]:.2f}'
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

        writer.write(frame)

        frame_count += 1

        if frame_count % 30 == 0:
            print(
                f"Processed {frame_count} frames | "
                f"Detected {len(detections)} vehicles"
            )

    cap.release()
    writer.release()

    print("\nProcessing completed!")
    print(f"Output: {OUTPUT_VIDEO}")


if __name__ == "__main__":
    process_video()