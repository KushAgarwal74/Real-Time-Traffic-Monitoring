import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from confluent_kafka import Producer

from config.kafka_config import ensure_kafka_topic
from config.settings import KAFKA_BOOTSTRAP_SERVERS, KAFKA_RAW_TOPIC


def delivery_report(err, msg):
    if err is not None:
        print(f"[-] Message delivery failed: {err}")
    else:
        print(f"[+] YOLO Frame data sent to topic: {msg.topic()} [Partition: {msg.partition()}]")

def run_yolo_producer():
    ensure_kafka_topic(KAFKA_RAW_TOPIC, KAFKA_BOOTSTRAP_SERVERS)

    # Configure producer to talk to local cluster via mapped localhost port
    conf = {'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS}
    producer = Producer(conf)
    topic_name = KAFKA_RAW_TOPIC

    print("[*] Starting mock YOLO camera stream... Press Ctrl+C to terminate.")
    
    frame_count = 0
    try:
        while True:
            frame_count += 1
            
            # This simulates what your actual YOLO pipeline metadata looks like
            traffic_payload = {
                "frame_id": frame_count,
                "timestamp": time.time(),
                "camera_location": "intersection_north_highway",
                "detections": {
                    "car": 8,
                    "truck": 2,
                    "bus": 1,
                    "motorcycle": 4
                }
            }
            
            # Send message data to the queue
            producer.produce(
                topic=topic_name, 
                value=json.dumps(traffic_payload).encode('utf-8'), 
                callback=delivery_report
            )
            
            # Poll to trigger background callbacks
            producer.poll(0)
            
            # Simulate processing speed delay (2 frames per second)
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n[*] Stopping producer feed gracefully...")
    finally:
        # Flush remaining buffers before close
        producer.flush()

if __name__ == "__main__":
    run_yolo_producer()
