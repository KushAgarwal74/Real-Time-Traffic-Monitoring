import json
from collections import deque
from datetime import datetime
from confluent_kafka import Consumer, KafkaError
import matplotlib.pyplot as plt


# Keep the last N data points visible
MAX_POINTS = 30


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

    # ---------------------------------------------------------
    # Data buffers
    # ---------------------------------------------------------

    timestamps = deque(maxlen=MAX_POINTS)
    cars = deque(maxlen=MAX_POINTS)
    motorbikes = deque(maxlen=MAX_POINTS)
    buses = deque(maxlen=MAX_POINTS)
    trucks = deque(maxlen=MAX_POINTS)

    # ---------------------------------------------------------
    # Setup live plot
    # ---------------------------------------------------------

    plt.ion()

    fig, ax = plt.subplots(figsize=(12, 6))

    try:

        while True:

            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():

                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue

                print(f"[-] Consumer encountered an error: {msg.error()}")
                break

            # -------------------------------------------------
            # Decode Kafka message
            # -------------------------------------------------

            try:

                raw_payload = msg.value().decode('utf-8')
                traffic_json = json.loads(raw_payload)

                detections = traffic_json["detections"]

                total_count = sum(detections.values())
                frame_number = traffic_json["frame_id"]
                loc = traffic_json["camera_location"]
                timestamp = traffic_json["timestamp"]

                datetime_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

                print(
                    f"[Engine Output] "
                    f"Loc: {loc} | "
                    f"Frame: {frame_number} | "
                    f"Counted Vehicles: {total_count} | "
                    f"Breakdown: {detections}"
                )

                # -------------------------------------------------
                # Add new data point
                # -------------------------------------------------

                # timestamps.append(timestamp)
                timestamps.append(datetime_str)
                cars.append(detections.get("car", 0))
                motorbikes.append(detections.get("motorcycle", 0))
                buses.append(detections.get("bus", 0))
                trucks.append(detections.get("truck", 0))

                # -------------------------------------------------
                # Update plot
                # -------------------------------------------------

                ax.clear()

                x = range(len(timestamps))

                # Cars - bottom layer
                ax.bar(
                    x,
                    cars,
                    label="Cars"
                )

                # Motorbikes - stacked on cars
                ax.bar(
                    x,
                    motorbikes,
                    bottom=cars,
                    label="Motorbikes"
                )

                # Calculate bottom for buses
                bottom_buses = [
                    c + m
                    for c, m in zip(cars, motorbikes)
                ]

                ax.bar(
                    x,
                    buses,
                    bottom=bottom_buses,
                    label="Buses"
                )

                # Calculate bottom for trucks
                bottom_trucks = [
                    c + m + b
                    for c, m, b in zip(
                        cars,
                        motorbikes,
                        buses
                    )
                ]

                ax.bar(
                    x,
                    trucks,
                    bottom=bottom_trucks,
                    label="Trucks"
                )

                # -------------------------------------------------
                # Labels / formatting
                # -------------------------------------------------

                ax.set_xlabel("Timestamp")
                ax.set_ylabel("Number of Vehicles")

                ax.set_title(
                    f"Traffic Analysis - {loc}"
                )

                ax.set_xticks(list(x))
                ax.set_xticklabels(
                    list(timestamps),
                    rotation=45,
                    ha="right"
                )

                ax.legend()

                fig.tight_layout()

                # Refresh GUI
                fig.canvas.draw()
                fig.canvas.flush_events()

                plt.pause(0.01)

            except Exception as e:

                print(
                    f"[-] Error decoding "
                    f"traffic payload: {e}"
                )

    except KeyboardInterrupt:

        print("\n[*] Stopping engine stream consumer...")

    finally:

        consumer.close()
        plt.close()


if __name__ == "__main__":
    run_stream_consumer()