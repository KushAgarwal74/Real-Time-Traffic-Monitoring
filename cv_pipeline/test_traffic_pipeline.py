import cv2

from datetime import datetime

from cv_pipeline.traffic_pipeline import (
    TrafficPipeline
)


def main():

    # ==========================================
    # LOAD TEST IMAGE
    # ==========================================

    image_path = "test_image.jpg"

    frame = cv2.imread(
        image_path
    )

    if frame is None:

        print(
            f"Could not load image: "
            f"{image_path}"
        )

        return


    # ==========================================
    # CREATE PIPELINE
    # ==========================================

    pipeline = TrafficPipeline()


    # ==========================================
    # PROCESS FRAME
    # ==========================================

    result = pipeline.process_frame(

        frame=frame,

        frame_number=1,

        timestamp=datetime.now(),

        camera_gps=None
    )


    # ==========================================
    # PRINT RESULTS
    # ==========================================

    print()

    print(
        "=" * 70
    )

    print(
        "TRAFFIC PIPELINE RESULT"
    )

    print(
        "=" * 70
    )


    print()

    print(
        "TRACKED OBJECTS"
    )

    print(
        "-" * 70
    )

    for vehicle in result[
        "tracked_objects"
    ]:

        print(vehicle)


    print()

    print(
        "PLATES"
    )

    print(
        "-" * 70
    )

    for track_id, plate in result[
        "plates_by_track"
    ].items():

        print(
            f"Track ID: {track_id}"
        )

        print(plate)


    print()

    print(
        "EVENTS"
    )

    print(
        "-" * 70
    )

    for event in result[
        "events"
    ]:

        print(event)


if __name__ == "__main__":

    main()