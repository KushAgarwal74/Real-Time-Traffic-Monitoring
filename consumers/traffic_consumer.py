import json

import psycopg2

from confluent_kafka import Consumer


KAFKA_CONFIG = {

    "bootstrap.servers": "localhost:9092",

    "group.id": "traffic-db-consumer",

    "auto.offset.reset": "earliest"
}


DB_CONFIG = {

    "host": "localhost",

    "port": 5432,

    "database": "traffic_db",

    "user": "traffic_user",

    "password": "traffic_password"
}


TOPIC = "traffic-events"


def extract_plate_data(event):

    license_plate = None

    plate_confidence = None


    plate = event.get(
        "license_plate"
    )


    if plate:

        best_ocr = plate.get(
            "best_ocr"
        )


        if best_ocr:

            license_plate = best_ocr.get(
                "text"
            )


            plate_confidence = best_ocr.get(
                "plate_confidence"
            )


    return (

        license_plate,

        plate_confidence
    )


def main():

    # ==========================================
    # CONNECT TO DATABASE
    # ==========================================

    connection = psycopg2.connect(

        **DB_CONFIG
    )


    cursor = connection.cursor()


    print(
        "Connected to TimescaleDB"
    )


    # ==========================================
    # CONNECT TO KAFKA
    # ==========================================

    consumer = Consumer(

        KAFKA_CONFIG
    )


    consumer.subscribe(

        [TOPIC]
    )


    print(
        f"Listening to Kafka topic: {TOPIC}"
    )


    try:

        while True:

            message = consumer.poll(
                timeout=1.0
            )


            if message is None:

                continue


            if message.error():

                print(
                    f"Kafka error: "
                    f"{message.error()}"
                )

                continue


            # ======================================
            # PARSE EVENT
            # ======================================

            event = json.loads(

                message.value().decode(
                    "utf-8"
                )
            )


            # ======================================
            # EXTRACT LICENSE PLATE
            # ======================================

            (

                license_plate,

                plate_confidence

            ) = extract_plate_data(
                event
            )


            # ======================================
            # INSERT EVENT
            # ======================================

            cursor.execute(

                """
                INSERT INTO traffic_events (

                    event_time,

                    event_type,

                    track_id,

                    vehicle_type,

                    confidence,

                    bbox,

                    camera_gps,

                    license_plate,

                    plate_confidence,

                    raw_event

                )

                VALUES (

                    %s,

                    %s,

                    %s,

                    %s,

                    %s,

                    %s,

                    %s,

                    %s,

                    %s,

                    %s

                )
                """,

                (

                    event.get(
                        "timestamp"
                    ),

                    event.get(
                        "event_type"
                    ),

                    event.get(
                        "track_id"
                    ),

                    event.get(
                        "vehicle_type"
                    ),

                    event.get(
                        "confidence"
                    ),

                    json.dumps(
                        event.get(
                            "bbox"
                        )
                    ),

                    json.dumps(
                        event.get(
                            "camera_gps"
                        )
                    ),

                    license_plate,

                    plate_confidence,

                    json.dumps(
                        event
                    )
                )
            )


            connection.commit()


            print(

                f"Stored: "

                f"{event.get('event_type')} "

                f"Track={event.get('track_id')}"
            )


    except KeyboardInterrupt:

        print(
            "\nStopping consumer..."
        )


    finally:

        consumer.close()

        cursor.close()

        connection.close()


if __name__ == "__main__":

    main()