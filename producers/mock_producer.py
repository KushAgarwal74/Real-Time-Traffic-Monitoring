import json
import time
import sys
from confluent_kafka import Producer

def delivery_report(err, msg):
    if err is not None:
        print(f"[-] Message delivery failed: {err}")
    else:
        print(f"[+] YOLO Frame data sent to topic: {msg.topic()} [Partition: {msg.partition()}]")

def run_yolo_producer():
    # Configure producer to talk to local cluster via mapped localhost port
    conf = {'bootstrap.servers': 'localhost:9092'}
    producer = Producer(conf)
    topic_name = 'traffic-raw-data'
    
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
