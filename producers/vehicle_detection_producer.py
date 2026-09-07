# type: ignore
import json
from confluent_kafka import Producer


BOOTSTRAP_SERVERS = "localhost:9092"

VEHICLE_TOPIC = "vehicle-events"
REGISTRATION_TOPIC = "registration-events"


def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(
            f"Message delivered to "
            f"{msg.topic()} [{msg.partition()}] @ {msg.offset()}"
        )


def create_vehicle_event(event):
    gps = event.get("camera_gps", {})

    return {
        "event_type": event["event_type"],
        "track_id": event["track_id"],
        "vehicle_type": event.get("vehicle_type"),
        "timestamp": event["timestamp"],
        "latitude": gps.get("latitude"),
        "longitude": gps.get("longitude")
    }


def create_registration_event(event):
    plate = event.get("license_plate")

    if not plate:
        return None

    return {
        "track_id": event["track_id"],
        "timestamp": event["timestamp"],
        "plate_confidence": plate.get("confidence"),
        "plate_bbox": plate.get("bbox")
    }


def publish_events(filename):

    producer = Producer({
        "bootstrap.servers": BOOTSTRAP_SERVERS
    })

    with open(filename, "r") as f:

        for line in f:

            if not line.strip():
                continue

            event = json.loads(line)

            # --------------------------------
            # Vehicle event
            # --------------------------------

            if event["event_type"] in (
                "vehicle_detected",
                "vehicle_updated",
                "vehicle_exited"
            ):

                vehicle_event = create_vehicle_event(event)

                producer.produce(
                    VEHICLE_TOPIC,
                    key=str(event["track_id"]),
                    value=json.dumps(vehicle_event),
                    callback=delivery_report
                )

            # --------------------------------
            # Registration plate event
            # --------------------------------

            registration_event = create_registration_event(event)

            if registration_event:

                producer.produce(
                    REGISTRATION_TOPIC,
                    key=str(event["track_id"]),
                    value=json.dumps(registration_event),
                    callback=delivery_report
                )

            # Serve delivery callbacks
            producer.poll(0)

    # Wait for all messages to be delivered
    producer.flush()


if __name__ == "__main__":
    publish_events("/home/ska/BITSPilani/AY2026-27_Semester1/StreamProcessingAndAnalytics/assignment1/Real-Time-Traffic-Monitoring/data/processed/traffic_1/v1s/events.jsonl")