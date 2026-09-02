import json
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(
    "data/processed/traffic_1"
)

MODELS = [
    "v1s",
    "v1m",
    "v1l",
    "v1x"
]


# ============================================================
# LOAD EVENTS
# ============================================================

def load_events(events_path):

    events = []

    if not events_path.exists():

        print(
            f"⚠️ File not found: "
            f"{events_path}"
        )

        return events

    with open(
        events_path,
        "r"
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            try:

                event = json.loads(
                    line
                )

                events.append(
                    event
                )

            except json.JSONDecodeError:

                print(
                    f"⚠️ Invalid JSON line "
                    f"in {events_path}"
                )

    return events


# ============================================================
# ANALYZE ONE MODEL
# ============================================================

def analyze_model(
    model_name,
    events
):

    all_tracks = set()

    tracks_with_plate = set()

    exited_tracks = set()

    exited_tracks_with_plate = set()

    plate_confidences = []

    event_type_plate_counts = {}

    vehicle_type_tracks = {}

    vehicle_type_tracks_with_plate = {}

    best_plate_per_track = {}


    # --------------------------------------------------------
    # Process events
    # --------------------------------------------------------

    for event in events:

        track_id = event.get(
            "track_id"
        )

        vehicle_type = event.get(
            "vehicle_type"
        )

        event_type = event.get(
            "event_type"
        )

        license_plate = event.get(
            "license_plate"
        )


        # ----------------------------------------------------
        # Track information
        # ----------------------------------------------------

        if track_id is not None:

            all_tracks.add(
                track_id
            )


        # ----------------------------------------------------
        # Vehicle type totals
        # ----------------------------------------------------

        if (
            track_id is not None
            and
            vehicle_type is not None
        ):

            if vehicle_type not in (
                vehicle_type_tracks
            ):

                vehicle_type_tracks[
                    vehicle_type
                ] = set()

                vehicle_type_tracks_with_plate[
                    vehicle_type
                ] = set()


            vehicle_type_tracks[
                vehicle_type
            ].add(
                track_id
            )


        # ----------------------------------------------------
        # Exit tracks
        # ----------------------------------------------------

        if event_type == "vehicle_exited":

            exited_tracks.add(
                track_id
            )


        # ----------------------------------------------------
        # Plate detection
        # ----------------------------------------------------

        if license_plate is not None:

            confidence = license_plate.get(
                "confidence"
            )

            tracks_with_plate.add(
                track_id
            )


            # ------------------------------------------------
            # Confidence statistics
            # ------------------------------------------------

            if confidence is not None:

                plate_confidences.append(
                    confidence
                )


                # --------------------------------------------
                # Best confidence per track
                # --------------------------------------------

                if (
                    track_id
                    not in
                    best_plate_per_track
                ):

                    best_plate_per_track[
                        track_id
                    ] = confidence

                else:

                    best_plate_per_track[
                        track_id
                    ] = max(

                        best_plate_per_track[
                            track_id
                        ],

                        confidence
                    )


            # ------------------------------------------------
            # Event type count
            # ------------------------------------------------

            event_type_plate_counts[
                event_type
            ] = (

                event_type_plate_counts.get(
                    event_type,
                    0
                )

                + 1
            )


            # ------------------------------------------------
            # Vehicle type plate coverage
            # ------------------------------------------------

            if vehicle_type is not None:

                vehicle_type_tracks_with_plate[
                    vehicle_type
                ].add(
                    track_id
                )


            # ------------------------------------------------
            # Exit plate coverage
            # ------------------------------------------------

            if event_type == "vehicle_exited":

                exited_tracks_with_plate.add(
                    track_id
                )


    # ========================================================
    # CALCULATE RESULTS
    # ========================================================

    total_tracks = len(
        all_tracks
    )

    total_tracks_with_plate = len(
        tracks_with_plate
    )


    plate_coverage = (

        (
            total_tracks_with_plate
            /
            total_tracks
        )
        *
        100

        if total_tracks > 0

        else 0
    )


    exit_coverage = (

        (
            len(
                exited_tracks_with_plate
            )
            /
            len(
                exited_tracks
            )
        )
        *
        100

        if exited_tracks

        else 0
    )


    average_confidence = (

        sum(
            plate_confidences
        )
        /
        len(
            plate_confidences
        )

        if plate_confidences

        else 0
    )


    best_confidences = list(

        best_plate_per_track.values()

    )


    average_best_confidence = (

        sum(
            best_confidences
        )
        /
        len(
            best_confidences
        )

        if best_confidences

        else 0
    )


    highest_best_confidence = (

        max(
            best_confidences
        )

        if best_confidences

        else 0
    )


    # ========================================================
    # VEHICLE TYPE RESULTS
    # ========================================================

    vehicle_type_results = {}


    for vehicle_type in (
        vehicle_type_tracks
    ):

        total = len(

            vehicle_type_tracks[
                vehicle_type
            ]
        )

        detected = len(

            vehicle_type_tracks_with_plate[
                vehicle_type
            ]
        )


        coverage = (

            (
                detected
                /
                total
            )
            *
            100

            if total > 0

            else 0
        )


        vehicle_type_results[
            vehicle_type
        ] = {

            "total": total,

            "detected": detected,

            "coverage": coverage
        }


    # ========================================================
    # RETURN RESULTS
    # ========================================================

    return {

        "model": model_name,

        "total_tracks": total_tracks,

        "tracks_with_plate": (
            total_tracks_with_plate
        ),

        "plate_coverage": (
            plate_coverage
        ),

        "total_plate_events": len(
            plate_confidences
        ),

        "min_confidence": (

            min(
                plate_confidences
            )

            if plate_confidences

            else 0
        ),

        "max_confidence": (

            max(
                plate_confidences
            )

            if plate_confidences

            else 0
        ),

        "avg_confidence": (
            average_confidence
        ),

        "exited_tracks": len(
            exited_tracks
        ),

        "exited_with_plate": len(
            exited_tracks_with_plate
        ),

        "exit_coverage": (
            exit_coverage
        ),

        "avg_best_confidence": (
            average_best_confidence
        ),

        "highest_best_confidence": (
            highest_best_confidence
        ),

        "event_type_plate_counts": (
            event_type_plate_counts
        ),

        "vehicle_type_results": (
            vehicle_type_results
        )
    }


# ============================================================
# PRINT COMPARISON
# ============================================================

def print_comparison(
    results
):

    print()

    print(
        "=" * 100
    )

    print(
        "LICENSE PLATE MODEL COMPARISON"
    )

    print(
        "=" * 100
    )


    # --------------------------------------------------------
    # Main comparison
    # --------------------------------------------------------

    print()

    print(
        f"{'Model':<10}"
        f"{'Tracks':>10}"
        f"{'Detected':>12}"
        f"{'Coverage':>12}"
        f"{'Avg Conf':>12}"
        f"{'Exit Cov':>12}"
    )

    print(
        "-" * 68
    )


    for result in results:

        print(

            f"{result['model']:<10}"

            f"{result['total_tracks']:>10}"

            f"{result['tracks_with_plate']:>12}"

            f"{result['plate_coverage']:>11.2f}%"

            f"{result['avg_confidence']:>12.3f}"

            f"{result['exit_coverage']:>11.2f}%"
        )


    # --------------------------------------------------------
    # Best model by coverage
    # --------------------------------------------------------

    best_model = max(

        results,

        key=lambda x:
        x["plate_coverage"]
    )


    print()

    print(
        "=" * 100
    )

    print(
        "BEST MODEL BY PLATE COVERAGE"
    )

    print(
        "=" * 100
    )

    print()

    print(
        f"🏆 {best_model['model']}"
    )

    print(
        f"Plate Coverage: "
        f"{best_model['plate_coverage']:.2f}%"
    )


    # --------------------------------------------------------
    # Vehicle type comparison
    # --------------------------------------------------------

    print()

    print(
        "=" * 100
    )

    print(
        "VEHICLE TYPE COVERAGE"
    )

    print(
        "=" * 100
    )


    vehicle_types = [

        "car",

        "motorcycle",

        "bus",

        "truck"
    ]


    for vehicle_type in vehicle_types:

        print()

        print(
            vehicle_type.upper()
        )

        for result in results:

            data = (

                result[
                    "vehicle_type_results"
                ].get(
                    vehicle_type,
                    {}
                )
            )


            coverage = data.get(
                "coverage",
                0
            )


            detected = data.get(
                "detected",
                0
            )


            total = data.get(
                "total",
                0
            )


            print(

                f"  {result['model']:<8}"

                f"{detected}/{total}"

                f" ({coverage:.2f}%)"
            )


    print()

    print(
        "=" * 100
    )

    print(
        "COMPARISON COMPLETE"
    )

    print(
        "=" * 100
    )


# ============================================================
# MAIN
# ============================================================

def main():

    results = []


    for model_name in MODELS:

        events_path = (

            BASE_DIR
            /
            model_name
            /
            "events.jsonl"
        )


        print()

        print(
            f"Reading {model_name}: "
            f"{events_path}"
        )


        events = load_events(
            events_path
        )


        if not events:

            continue


        result = analyze_model(

            model_name,

            events
        )


        results.append(
            result
        )


    if not results:

        print(
            "❌ No event files found."
        )

        return


    print_comparison(
        results
    )


if __name__ == "__main__":

    main()