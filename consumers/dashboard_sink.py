import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from confluent_kafka import Consumer, KafkaError

from config.kafka_config import ensure_kafka_topic
from config.settings import KAFKA_BOOTSTRAP_SERVERS, KAFKA_CONSUMER_GROUP, KAFKA_RAW_TOPIC
from config.db_config import get_db_connection, init_database, upsert_traffic_summary


def persist_traffic_event(payload: dict):
    if not payload:
        return

    timestamp_raw = payload.get("timestamp")
    if isinstance(timestamp_raw, (int, float)):
        event_time = datetime.fromtimestamp(timestamp_raw, tz=timezone.utc)
    else:
        event_time = datetime.now(timezone.utc)

    camera_location = payload.get("camera_location", "unknown")
    frame_id = payload.get("frame_id", 0)
    detections = payload.get("detections", {})
    total_count = sum(int(value) for value in detections.values() if isinstance(value, (int, float)))
    raw_payload = json.dumps(payload)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO traffic_event (
                    event_time,
                    camera_location,
                    frame_id,
                    total_vehicles,
                    detection_summary,
                    raw_payload
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    event_time,
                    camera_location,
                    frame_id,
                    total_count,
                    json.dumps(detections),
                    raw_payload,
                ),
            )
        conn.commit()

    upsert_traffic_summary(camera_location, event_time, total_count)

    print(
        f"[DB Sink] saved frame {frame_id} from {camera_location} | "
        f"total={total_count} | breakdown={detections}"
    )


def run_stream_consumer():
    init_database()
    ensure_kafka_topic(KAFKA_RAW_TOPIC, KAFKA_BOOTSTRAP_SERVERS)

    conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': KAFKA_CONSUMER_GROUP,
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(conf)
    consumer.subscribe([KAFKA_RAW_TOPIC])

    print("[*] Kafka DB Sink active. Awaiting traffic events from Kafka...")

    try:
        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"[-] Consumer encountered an error: {msg.error()}")
                    break

            try:
                raw_payload = msg.value().decode('utf-8')
                traffic_json = json.loads(raw_payload)
                persist_traffic_event(traffic_json)
            except Exception as exc:
                print(f"[-] Error decoding or storing Kafka payload: {exc}")

    except KeyboardInterrupt:
        print("\n[*] Stopping Kafka DB sink gracefully...")
    finally:
        consumer.close()


if __name__ == "__main__":
    run_stream_consumer()

