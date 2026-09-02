from datetime import datetime

from cv_pipeline.vehicle_state_manager import (
    VehicleStateManager
)


def create_plate(
    text,
    final_score
):

    return {

        "ocr": {
            "text": text
        },

        "best_ocr": {

            "text": text,

            "ocr_confidence": 0.80,

            "plate_confidence": 0.85,

            "format_score": 1.0,

            "is_valid": True,

            "observations": 1,

            "total_observations": 1,

            "final_score": final_score
        }
    }


def main():

    print()

    print("=" * 70)

    print("VEHICLE STATE MANAGER TEST")

    print("=" * 70)

    state_manager = VehicleStateManager(

        exit_after_frames=10,

        update_interval_frames=3
    )


    timestamp = datetime.now()


    # ==================================================
    # FRAME 1
    # Vehicle appears
    # ==================================================

    print("\nFRAME 1")

    tracked_objects = [

        {

            "track_id": 1,

            "class_name": "car",

            "bbox": [
                100,
                100,
                300,
                250
            ],

            "confidence": 0.90,

            "license_plate": create_plate(

                "MH12AB1234",

                0.70
            )
        }
    ]


    events = state_manager.update(

        tracked_objects=tracked_objects,

        frame_number=1,

        timestamp=timestamp
    )

    for event in events:

        print(event)


    # ==================================================
    # FRAME 2
    # Better plate result
    # ==================================================

    print("\nFRAME 2 - BETTER PLATE")

    tracked_objects = [

        {

            "track_id": 1,

            "class_name": "car",

            "bbox": [
                105,
                100,
                305,
                250
            ],

            "confidence": 0.91,

            "license_plate": create_plate(

                "MH12AB6858",

                0.95
            )
        }
    ]


    events = state_manager.update(

        tracked_objects=tracked_objects,

        frame_number=2,

        timestamp=datetime.now()
    )

    for event in events:

        print(event)


    # ==================================================
    # FRAME 3
    # Worse plate result
    # Should NOT replace best plate
    # ==================================================

    print("\nFRAME 3 - WORSE PLATE")

    tracked_objects = [

        {

            "track_id": 1,

            "class_name": "car",

            "bbox": [
                110,
                100,
                310,
                250
            ],

            "confidence": 0.88,

            "license_plate": create_plate(

                "MH12AB123",

                0.40
            )
        }
    ]


    events = state_manager.update(

        tracked_objects=tracked_objects,

        frame_number=3,

        timestamp=datetime.now()
    )

    for event in events:

        print(event)


    # ==================================================
    # FRAME 4
    # Should generate update event
    # ==================================================

    print("\nFRAME 4 - UPDATE EVENT")

    tracked_objects = [

        {

            "track_id": 1,

            "class_name": "car",

            "bbox": [
                115,
                100,
                315,
                250
            ],

            "confidence": 0.92,

            "license_plate": None
        }
    ]


    events = state_manager.update(

        tracked_objects=tracked_objects,

        frame_number=4,

        timestamp=datetime.now()
    )

    for event in events:

        print(event)


    # ==================================================
    # FRAMES 5-14
    # Vehicle disappears
    # ==================================================

    print("\nVEHICLE DISAPPEARS")


    for frame_number in range(

        5,

        15
    ):

        events = state_manager.update(

            tracked_objects=[],

            frame_number=frame_number,

            timestamp=datetime.now()
        )


        for event in events:

            print()

            print(

                f"FRAME {frame_number}"
            )

            print(event)


    # ==================================================
    # FINAL STATE
    # ==================================================

    print()

    print("=" * 70)

    print("FINAL VEHICLE STATE")

    print("=" * 70)

    print(

        state_manager.vehicles[1]
    )


if __name__ == "__main__":

    main()