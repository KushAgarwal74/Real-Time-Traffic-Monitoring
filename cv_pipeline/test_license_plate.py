import cv2

from cv_pipeline.license_plate_detector import (
    LicensePlateDetector
)


VIDEO_PATH = (
    "data/raw/city/traffic_1.mp4"
)


def main():

    detector = LicensePlateDetector()

    cap = cv2.VideoCapture(
        VIDEO_PATH
    )

    if not cap.isOpened():

        raise RuntimeError(
            "Could not open video"
        )

    frame_number = 0

    while True:

        success, frame = cap.read()

        if not success:
            break

        # Only test one frame every 30 frames
        if frame_number % 30 == 0:

            plates = detector.detect(
                frame
            )

            print(
                f"Frame {frame_number}: "
                f"{len(plates)} plates detected"
            )

            # Draw detected plates
            for plate in plates:

                x1, y1, x2, y2 = (
                    plate["bbox"]
                )

                confidence = (
                    plate["confidence"]
                )

                cv2.rectangle(

                    frame,

                    (x1, y1),

                    (x2, y2),

                    (0, 255, 0),

                    2

                )

                label = (
                    f"Plate {confidence:.2f}"
                )

                cv2.putText(

                    frame,

                    label,

                    (x1, y1 - 10),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    (0, 255, 0),

                    2

                )

            cv2.imshow(
                "License Plate Detection",
                frame
            )

            key = cv2.waitKey(1)

            if key == ord("q"):

                break

        frame_number += 1

    cap.release()

    cv2.destroyAllWindows()


if __name__ == "__main__":

    main()