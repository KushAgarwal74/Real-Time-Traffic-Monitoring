import json
import sys
from confluent_kafka import Consumer, KafkaError

def run_stream_consumer():
    conf = {
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'traffic-monitoring-analytics-group',
        'auto.offset.reset': 'earliest'
    }
    
    consumer = Consumer(conf)
    topic_name = 'traffic-raw-data'
    consumer.subscribe([topic_name])
    
    print("[*] Kafka Stream Engine active. Awaiting logs from YOLO node...")
    
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
            
            # Safely process incoming text frame payload 
            try:
                raw_payload = msg.value().decode('utf-8')
                traffic_json = json.loads(raw_payload)
                
                # Perform mock stream extraction / metrics evaluation
                detections = traffic_json["detections"]
                total_count = sum(detections.values())
                frame_number = traffic_json["frame_id"]
                loc = traffic_json["camera_location"]
                
                print(f"[Engine Output] Loc: {loc} | Frame: {frame_number} | Counted Vehicles: {total_count} -> Breakdown: {detections}")
                
            except Exception as e:
                print(f"[-] Error decoding dynamic text string payload: {e}")
                
    except KeyboardInterrupt:
        print("\n[*] Stopping engine stream consumer...")
    finally:
        consumer.close()

if __name__ == "__main__":
    run_stream_consumer()
