import json
from collections import Counter, defaultdict
from pathlib import Path


EVENTS_FILE = Path(
    "data/processed/traffic_1/events.jsonl"
)


def load_events(file_path):

    events = []

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        for line_number, line in enumerate(
            file,
            start=1
        ):

            line = line.strip()

            if not line:
                continue

            try:

                event = json.loads(line)

                events.append(event)

            except json.JSONDecodeError as error:

                print(
                    f"INVALID JSON at line "
                    f"{line_number}: {error}"
                )

    return events


def validate_events(events):

    event_counts = Counter()

    vehicle_type_counts = Counter()

    track_events = defaultdict(list)

    tracks_by_event_type = defaultdict(set)

    gps_missing_count = 0

    timestamp_missing_count = 0

    inconsistent_vehicle_types = []

    # -----------------------------------------
    # PROCESS ALL EVENTS
    # -----------------------------------------

    for event in events:

        event_type = event.get(
            "event_type"
        )

        track_id = event.get(
            "track_id"
        )

        vehicle_type = event.get(
            "vehicle_type"
        )

        timestamp = event.get(
            "timestamp"
        )

        camera_gps = event.get(
            "camera_gps"
        )

        # Count event types
        event_counts[event_type] += 1

        # Count vehicle types
        if vehicle_type:
            vehicle_type_counts[
                vehicle_type
            ] += 1

        # Store track lifecycle
        if track_id is not None:

            track_events[
                track_id
            ].append(event)

            tracks_by_event_type[
                event_type
            ].add(track_id)

        # Validate timestamp
        if not timestamp:
            timestamp_missing_count += 1

        # Validate GPS
        if camera_gps is None:
            gps_missing_count += 1

    # -----------------------------------------
    # TRACK SETS
    # -----------------------------------------

    detected_tracks = tracks_by_event_type[
        "vehicle_detected"
    ]

    updated_tracks = tracks_by_event_type[
        "vehicle_updated"
    ]

    exited_tracks = tracks_by_event_type[
        "vehicle_exited"
    ]

    all_tracks = set(
        track_events.keys()
    )

    # -----------------------------------------
    # LIFECYCLE VALIDATION
    # -----------------------------------------

    exited_without_detected = (
        exited_tracks -
        detected_tracks
    )

    updated_without_detected = (
        updated_tracks -
        detected_tracks
    )

    detected_without_exit = (
        detected_tracks -
        exited_tracks
    )

    # -----------------------------------------
    # DUPLICATE DETECTION EVENTS
    # -----------------------------------------

    duplicate_detected_tracks = []

    for track_id, events_for_track in (
        track_events.items()
    ):

        detected_count = sum(
            1
            for event in events_for_track
            if event.get("event_type")
            == "vehicle_detected"
        )

        if detected_count > 1:

            duplicate_detected_tracks.append(
                {
                    "track_id": track_id,
                    "detected_events": detected_count
                }
            )

    # -----------------------------------------
    # VEHICLE TYPE CONSISTENCY
    # -----------------------------------------

    for track_id, events_for_track in (
        track_events.items()
    ):

        vehicle_types = set()

        for event in events_for_track:

            vehicle_type = event.get(
                "vehicle_type"
            )

            if vehicle_type:
                vehicle_types.add(
                    vehicle_type
                )

        if len(vehicle_types) > 1:

            inconsistent_vehicle_types.append(
                {
                    "track_id": track_id,
                    "vehicle_types": list(
                        vehicle_types
                    )
                }
            )

    # -----------------------------------------
    # RETURN RESULTS
    # -----------------------------------------

    return {

        "total_events": len(events),

        "event_counts": event_counts,

        "vehicle_type_counts": vehicle_type_counts,

        "total_unique_tracks": len(
            all_tracks
        ),

        "unique_detected_tracks": len(
            detected_tracks
        ),

        "unique_updated_tracks": len(
            updated_tracks
        ),

        "unique_exited_tracks": len(
            exited_tracks
        ),

        "exited_without_detected": (
            exited_without_detected
        ),

        "updated_without_detected": (
            updated_without_detected
        ),

        "detected_without_exit": (
            detected_without_exit
        ),

        "duplicate_detected_tracks": (
            duplicate_detected_tracks
        ),

        "inconsistent_vehicle_types": (
            inconsistent_vehicle_types
        ),

        "gps_missing_count": (
            gps_missing_count
        ),

        "timestamp_missing_count": (
            timestamp_missing_count
        )
    }


def print_report(results):

    print()

    print("=" * 60)

    print("EVENT VALIDATION REPORT")

    print("=" * 60)

    # -----------------------------------------
    # GENERAL
    # -----------------------------------------

    print("\nGENERAL")

    print(
        f"Total Events: "
        f"{results['total_events']}"
    )

    print(
        f"Total Unique Tracks: "
        f"{results['total_unique_tracks']}"
    )

    # -----------------------------------------
    # EVENT TYPES
    # -----------------------------------------

    print("\nEVENT TYPES")

    for event_type, count in (
        results["event_counts"].items()
    ):

        print(
            f"{event_type}: {count}"
        )

    # -----------------------------------------
    # UNIQUE TRACKS
    # -----------------------------------------

    print("\nUNIQUE TRACKS")

    print(
        f"Detected: "
        f"{results['unique_detected_tracks']}"
    )

    print(
        f"Updated: "
        f"{results['unique_updated_tracks']}"
    )

    print(
        f"Exited: "
        f"{results['unique_exited_tracks']}"
    )

    # -----------------------------------------
    # LIFECYCLE VALIDATION
    # -----------------------------------------

    print("\nLIFECYCLE VALIDATION")

    print(
        "Exited without Detected: "
        f"{len(results['exited_without_detected'])}"
    )

    print(
        "Updated without Detected: "
        f"{len(results['updated_without_detected'])}"
    )

    print(
        "Detected without Exit: "
        f"{len(results['detected_without_exit'])}"
    )

    # -----------------------------------------
    # DUPLICATES
    # -----------------------------------------

    print("\nDUPLICATE DETECTION EVENTS")

    print(
        f"Tracks with duplicate DETECTED events: "
        f"{len(results['duplicate_detected_tracks'])}"
    )

    # -----------------------------------------
    # VEHICLE TYPE VALIDATION
    # -----------------------------------------

    print("\nVEHICLE TYPE CONSISTENCY")

    print(
        f"Tracks with inconsistent vehicle types: "
        f"{len(results['inconsistent_vehicle_types'])}"
    )

    # -----------------------------------------
    # DATA QUALITY
    # -----------------------------------------

    print("\nDATA QUALITY")

    print(
        f"Events missing timestamp: "
        f"{results['timestamp_missing_count']}"
    )

    print(
        f"Events missing GPS: "
        f"{results['gps_missing_count']}"
    )

    # -----------------------------------------
    # VEHICLE DISTRIBUTION
    # -----------------------------------------

    print("\nVEHICLE TYPE DISTRIBUTION")

    for vehicle_type, count in (
        results["vehicle_type_counts"].most_common()
    ):

        print(
            f"{vehicle_type}: {count}"
        )

    # -----------------------------------------
    # WARNINGS
    # -----------------------------------------

    print("\n" + "=" * 60)

    print("VALIDATION STATUS")

    print("=" * 60)

    problems = []

    if results["exited_without_detected"]:

        problems.append(
            "Some tracks EXITED without DETECTED"
        )

    if results["updated_without_detected"]:

        problems.append(
            "Some tracks UPDATED without DETECTED"
        )

    if results["duplicate_detected_tracks"]:

        problems.append(
            "Some tracks have duplicate DETECTED events"
        )

    if results["inconsistent_vehicle_types"]:

        problems.append(
            "Some tracks changed vehicle type"
        )

    if problems:

        print("\nWARNINGS FOUND:\n")

        for problem in problems:

            print(f"⚠️  {problem}")

    else:

        print(
            "\n✅ EVENT DATA LOOKS CONSISTENT"
        )


def main():

    print(
        f"\nReading events from:\n"
        f"{EVENTS_FILE}\n"
    )

    if not EVENTS_FILE.exists():

        raise FileNotFoundError(
            f"Events file not found: "
            f"{EVENTS_FILE}"
        )

    events = load_events(
        EVENTS_FILE
    )

    results = validate_events(
        events
    )

    print_report(
        results
    )


if __name__ == "__main__":
    main()