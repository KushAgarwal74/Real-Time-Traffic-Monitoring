import cv2

from datetime import datetime

from cv_pipeline.traffic_pipeline import (
    TrafficPipeline
)


# ==========================================================
# CONFIGURATION
# ==========================================================

VIDEO_PATH = "data/raw/city/traffic_1.mp4"
GPX_PATH = "data/raw/city/traffic_1.gpx"

MAX_FRAMES = 300

PRINT_EVERY = 10


# ==========================================================
# MAIN
# ==========================================================

def main():

    # ======================================================
    # OPEN VIDEO
    # ======================================================

    print(
        f"Opening video: {VIDEO_PATH}"
    )

    cap = cv2.VideoCapture(
        VIDEO_PATH
    )

    if not cap.isOpened():

        print(
            f"Could not open video: "
            f"{VIDEO_PATH}"
        )

        return

    total_video_frames = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    print(
        f"Video frames: "
        f"{total_video_frames}"
    )

    print(
        f"FPS: "
        f"{fps:.2f}"
    )

    print(
        f"Processing first "
        f"{MAX_FRAMES} frames..."
    )

    # ======================================================
    # CREATE PIPELINE
    # ======================================================

    pipeline = TrafficPipeline(
        video_path=VIDEO_PATH,
        gpx_path=GPX_PATH
    )

    # ======================================================
    # PROCESS VIDEO
    # ======================================================

    frame_number = 0

    all_events = []

    last_result = None

    try:

        while frame_number < MAX_FRAMES:

            ret, frame = cap.read()

            if not ret:

                print(
                    "\nEnd of video."
                )

                break

            frame_number += 1

            # --------------------------------------------------
            # Timestamp
            # --------------------------------------------------

            timestamp = datetime.now()

            # --------------------------------------------------
            # Process frame
            # --------------------------------------------------

            result = pipeline.process_frame(
                frame=frame,
                frame_number=frame_number,
            )

            last_result = result

            # --------------------------------------------------
            # Store events
            # --------------------------------------------------

            events = result.get(
                "events",
                []
            )

            if events:

                all_events.extend(
                    events
                )

            # --------------------------------------------------
            # Progress
            # --------------------------------------------------

            if (
                frame_number == 1
                or
                frame_number % PRINT_EVERY == 0
            ):

                print(
                    f"Frame "
                    f"{frame_number}/"
                    f"{MAX_FRAMES} "
                    f"| Vehicles: "
                    f"{len(result['tracked_objects'])} "
                    f"| Plates: "
                    f"{len(result['plates_by_track'])}"
                )

                # ----------------------------------------------
                # Print current plate observations
                # ----------------------------------------------

                for (
                    track_id,
                    plate
                ) in result[
                    "plates_by_track"
                ].items():

                    if plate is None:
                        continue

                    best_ocr = plate.get(
                        "best_ocr"
                    )

                    if best_ocr is None:
                        continue

                    print(
                        f"  Track {track_id}: "
                        f"{best_ocr['text']} "
                        f"| observations="
                        f"{best_ocr['observations']} "
                        f"| total="
                        f"{best_ocr['total_observations']} "
                        f"| score="
                        f"{best_ocr['final_score']:.3f}"
                    )

    finally:

        cap.release()

    # ======================================================
    # FINAL RESULT
    # ======================================================

    print()
    print(
        "=" * 80
    )

    print(
        "MULTI-FRAME TRAFFIC PIPELINE RESULT"
    )

    print(
        "=" * 80
    )

    print()

    print(
        f"Frames processed: "
        f"{frame_number}"
    )

    print(
        f"Events generated: "
        f"{len(all_events)}"
    )

    # ======================================================
    # FINAL TRACK STATE
    # ======================================================

    print()

    print(
        "FINAL TRACK RESULTS"
    )

    print(
        "-" * 80
    )

    if (
        last_result is None
        or
        not last_result[
            "tracked_objects"
        ]
    ):

        print(
            "No tracked vehicles."
        )

    else:

        for vehicle in last_result[
            "tracked_objects"
        ]:

            track_id = vehicle[
                "track_id"
            ]

            plate = vehicle.get(
                "license_plate"
            )

            print()

            print(
                f"Track ID: "
                f"{track_id}"
            )

            print(
                f"Vehicle: "
                f"{vehicle['class_name']}"
            )

            if plate is None:

                print(
                    "Plate: None"
                )

                continue

            best_ocr = plate.get(
                "best_ocr"
            )

            if best_ocr is None:

                print(
                    "Plate OCR: None"
                )

                continue

            print(
                f"Best plate: "
                f"{best_ocr['text']}"
            )

            print(
                f"OCR confidence: "
                f"{best_ocr['ocr_confidence']:.3f}"
            )

            print(
                f"Plate confidence: "
                f"{best_ocr['plate_confidence']:.3f}"
            )

            print(
                f"Format score: "
                f"{best_ocr['format_score']:.3f}"
            )

            print(
                f"Valid: "
                f"{best_ocr['is_valid']}"
            )

            print(
                f"Observations: "
                f"{best_ocr['observations']}"
            )

            print(
                f"Total observations: "
                f"{best_ocr['total_observations']}"
            )

            print(
                f"Final score: "
                f"{best_ocr['final_score']:.3f}"
            )

    # ======================================================
    # EVENTS
    # ======================================================

    print()

    print(
        "EVENTS"
    )

    print(
        "-" * 80
    )

    for event in all_events:

        print(
            event
        )


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    main()