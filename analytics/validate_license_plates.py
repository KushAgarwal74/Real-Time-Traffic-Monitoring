import json
from pathlib import Path
from collections import defaultdict


EVENT_FILE = Path(
    "data/processed/traffic_1/events.jsonl"
)


def analyze_license_plates():

    print("\nReading events from:")

    print(EVENT_FILE)

    if not EVENT_FILE.exists():

        raise FileNotFoundError(
            f"Event file not found: {EVENT_FILE}"
        )

    # ----------------------------------------
    # Track information
    # ----------------------------------------

    tracks = {}

    vehicle_type_tracks = defaultdict(set)

    # ----------------------------------------
    # Plate statistics
    # ----------------------------------------

    tracks_with_plate = set()

    plate_confidences = []

    plate_detections = 0

    event_types_with_plate = defaultdict(int)

    exited_tracks = set()

    exited_with_plate = set()

    # ----------------------------------------
    # Read events
    # ----------------------------------------

    with open(
        EVENT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            if not line:

                continue

            event = json.loads(line)

            track_id = event["track_id"]

            event_type = event["event_type"]

            vehicle_type = event[
                "vehicle_type"
            ]

            # --------------------------------
            # Store track
            # --------------------------------

            if track_id not in tracks:

                tracks[track_id] = {

                    "vehicle_type": vehicle_type,

                    "best_plate_confidence": None,

                    "plate_events": 0
                }

            vehicle_type_tracks[
                vehicle_type
            ].add(track_id)

            # --------------------------------
            # Plate information
            # --------------------------------

            license_plate = event.get(
                "license_plate"
            )

            if license_plate is not None:

                tracks_with_plate.add(
                    track_id
                )

                plate_detections += 1

                event_types_with_plate[
                    event_type
                ] += 1

                confidence = license_plate.get(
                    "confidence"
                )

                if confidence is not None:

                    confidence = float(
                        confidence
                    )

                    plate_confidences.append(
                        confidence
                    )

                    current_best = tracks[
                        track_id
                    ][
                        "best_plate_confidence"
                    ]

                    if (
                        current_best is None
                        or confidence > current_best
                    ):

                        tracks[
                            track_id
                        ][
                            "best_plate_confidence"
                        ] = confidence

                tracks[
                    track_id
                ][
                    "plate_events"
                ] += 1

            # --------------------------------
            # Exit information
            # --------------------------------

            if event_type == "vehicle_exited":

                exited_tracks.add(
                    track_id
                )

                if license_plate is not None:

                    exited_with_plate.add(
                        track_id
                    )

    # ========================================
    # GENERAL STATISTICS
    # ========================================

    total_tracks = len(tracks)

    total_tracks_with_plate = len(
        tracks_with_plate
    )

    if total_tracks > 0:

        plate_coverage = (
            total_tracks_with_plate
            / total_tracks
            * 100
        )

    else:

        plate_coverage = 0

    # ========================================
    # OUTPUT
    # ========================================

    print("\n")

    print("=" * 60)

    print("LICENSE PLATE ANALYTICS REPORT")

    print("=" * 60)

    # ----------------------------------------
    # Overall coverage
    # ----------------------------------------

    print("\nGENERAL")

    print(
        f"Total Unique Vehicle Tracks: "
        f"{total_tracks}"
    )

    print(
        f"Tracks With Plate Detection: "
        f"{total_tracks_with_plate}"
    )

    print(
        f"Plate Detection Coverage: "
        f"{plate_coverage:.2f}%"
    )

    print(
        f"Total Events Containing Plate Data: "
        f"{plate_detections}"
    )

    # ----------------------------------------
    # Confidence
    # ----------------------------------------

    print("\nPLATE CONFIDENCE")

    if plate_confidences:

        print(
            f"Minimum: "
            f"{min(plate_confidences):.3f}"
        )

        print(
            f"Maximum: "
            f"{max(plate_confidences):.3f}"
        )

        average_confidence = (

            sum(plate_confidences)
            / len(plate_confidences)

        )

        print(
            f"Average: "
            f"{average_confidence:.3f}"
        )

    else:

        print(
            "No plate detections found"
        )

    # ----------------------------------------
    # Event type distribution
    # ----------------------------------------

    print("\nPLATE DATA BY EVENT TYPE")

    for event_type, count in sorted(
        event_types_with_plate.items()
    ):

        print(
            f"{event_type}: {count}"
        )

    # ----------------------------------------
    # Vehicle type coverage
    # ----------------------------------------

    print("\nPLATE COVERAGE BY VEHICLE TYPE")

    for vehicle_type in sorted(
        vehicle_type_tracks.keys()
    ):

        all_tracks = vehicle_type_tracks[
            vehicle_type
        ]

        tracks_with_type_plate = {

            track_id

            for track_id in tracks_with_plate

            if tracks[track_id][
                "vehicle_type"
            ] == vehicle_type
        }

        total = len(all_tracks)

        detected = len(
            tracks_with_type_plate
        )

        percentage = (

            detected / total * 100

            if total > 0

            else 0
        )

        print(

            f"{vehicle_type}: "

            f"{detected}/{total} "

            f"({percentage:.2f}%)"

        )

    # ----------------------------------------
    # Exit coverage
    # ----------------------------------------

    print("\nEXIT EVENT ANALYSIS")

    print(
        f"Exited Tracks: "
        f"{len(exited_tracks)}"
    )

    print(
        f"Exited With Plate Data: "
        f"{len(exited_with_plate)}"
    )

    if exited_tracks:

        exit_plate_percentage = (

            len(exited_with_plate)
            / len(exited_tracks)
            * 100

        )

        print(

            f"Exit Plate Coverage: "

            f"{exit_plate_percentage:.2f}%"

        )

    # ----------------------------------------
    # Best plate confidence distribution
    # ----------------------------------------

    best_confidences = [

        track["best_plate_confidence"]

        for track in tracks.values()

        if track[
            "best_plate_confidence"
        ] is not None

    ]

    print("\nBEST PLATE PER TRACK")

    print(

        f"Tracks With Best Plate: "

        f"{len(best_confidences)}"

    )

    if best_confidences:

        print(

            f"Average Best Confidence: "

            f"{sum(best_confidences) / len(best_confidences):.3f}"

        )

        print(

            f"Highest Best Confidence: "

            f"{max(best_confidences):.3f}"

        )

    print("\n")

    print("=" * 60)

    print("LICENSE PLATE ANALYTICS COMPLETE")

    print("=" * 60)


if __name__ == "__main__":

    analyze_license_plates()