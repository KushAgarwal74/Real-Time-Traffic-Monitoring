import json
import time

from producers.kafka_producer import (
    TrafficEventProducer
)


EVENTS_PATH = (
    "data/processed/traffic_1/events.jsonl"
)


def main():

    producer = TrafficEventProducer()

    print("=" * 60)

    print("STARTING EVENT REPLAY")

    print("=" * 60)


    with open(
        EVENTS_PATH,
        "r"
    ) as file:

        for line_number, line in enumerate(
            file,
            start=1
        ):

            line = line.strip()

            if not line:

                continue


            # --------------------------------------
            # Parse JSON event safely
            # --------------------------------------

            try:

                event = json.loads(
                    line
                )

            except json.JSONDecodeError:

                print(

                    f"Skipping invalid JSON "
                    f"at line {line_number}: "
                    f"{repr(line[:100])}"

                )

                continue


            # --------------------------------------
            # Send to Kafka
            # --------------------------------------

            producer.send_event(
                event
            )


            print(

                f"Sent event {line_number}: "

                f"{event.get('event_type')} "

                f"Track={event.get('track_id')}"
            )


            time.sleep(0.1)


    # ==========================================
    # Ensure all messages are delivered
    # ==========================================

    producer.flush()


    print("=" * 60)

    print("EVENT REPLAY COMPLETE")

    print("=" * 60)


if __name__ == "__main__":

    main()