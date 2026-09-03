import json
from datetime import datetime

from confluent_kafka import Producer

def json_serializer(obj):

    if isinstance(obj, datetime):
        return obj.isoformat()

    raise TypeError(
        f"Object of type {type(obj).__name__} "
        f"is not JSON serializable"
    )

class TrafficEventProducer:

    def __init__(
        self,
        bootstrap_servers="localhost:9092",
        topic="traffic-events"
    ):

        self.topic = topic

        self.producer = Producer(
            {
                "bootstrap.servers": bootstrap_servers
            }
        )


    # ==========================================
    # DELIVERY CALLBACK
    # ==========================================

    def delivery_report(
        self,
        err,
        msg
    ):

        if err is not None:

            print(
                f"Message delivery failed: {err}"
            )

        else:

            print(
                f"Delivered event to "
                f"{msg.topic()} "
                f"[partition {msg.partition()}]"
            )


    # ==========================================
    # SEND EVENT
    # ==========================================

    def send_event(
        self,
        event
    ):

        track_id = event.get(
            "track_id"
        )


        self.producer.produce(

            topic=self.topic,

            key=str(track_id),

            value=json.dumps(event, default=json_serializer),

            callback=self.delivery_report
        )


        # Allow delivery callbacks to run
        self.producer.poll(
            0
        )


    # ==========================================
    # FLUSH
    # ==========================================

    def flush(self):

        self.producer.flush()