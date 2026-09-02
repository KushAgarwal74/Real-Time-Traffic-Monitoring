import cv2
import json
import os

from datetime import datetime

from producers.kafka_producer import (
    TrafficEventProducer
)


class VideoRunner:

    def __init__(
        self,
        pipeline
    ):

        self.pipeline = pipeline

        # Kafka producer for real-time event streaming
        self.kafka_producer = (
            TrafficEventProducer()
        )


    # ==================================================
    # DRAW RESULTS
    # ==================================================

    def draw_results(
        self,
        frame,
        result
    ):

        for vehicle in result["tracked_objects"]:

            # ==========================================
            # VEHICLE DATA
            # ==========================================

            x1, y1, x2, y2 = (
                vehicle["bbox"]
            )

            track_id = vehicle[
                "track_id"
            ]

            class_name = vehicle[
                "class_name"
            ]

            confidence = vehicle[
                "confidence"
            ]


            # ==========================================
            # DRAW VEHICLE BOUNDING BOX
            # ==========================================

            cv2.rectangle(

                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )


            label = (
                f"{class_name} "
                f"ID:{track_id} "
                f"{confidence:.2f}"
            )


            cv2.putText(
                frame,
                label,
                (
                    x1,
                    max(30, y1 - 10)
                ),

                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )


            # ==========================================
            # LICENSE PLATE
            # ==========================================

            plate = vehicle.get(
                "license_plate"
            )

            if plate is None:
                continue


            px1, py1, px2, py2 = (
                plate["bbox"]
            )

            # ==========================================
            # DRAW PLATE BOUNDING BOX
            # ==========================================

            cv2.rectangle(
                frame,
                (px1, py1),
                (px2, py2),
                (255, 0, 0),
                2
            )


            # ==========================================
            # DRAW BEST OCR RESULT
            # ==========================================

            best_ocr = plate.get(
                "best_ocr"
            )

            if best_ocr is None:
                continue

            plate_text = best_ocr.get(
                "text",
                ""
            )

            if plate_text:
                cv2.putText(
                    frame,
                    plate_text,
                    (
                        px1,
                        max(30, py1 - 10)
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 0, 0),
                    2
                )

        return frame

    # ==================================================
    # RUN VIDEO
    # ==================================================

    def run(
        self,
        input_path,
        output_path,
        events_path,
        summary_path,
        camera_gps=None
    ):

        # ==============================================
        # CREATE OUTPUT DIRECTORIES
        # ==============================================

        for path in [
            output_path,
            events_path,
            summary_path
        ]:

            directory = os.path.dirname(
                path
            )

            if directory:
                os.makedirs(
                    directory,
                    exist_ok=True
                )

        # ==============================================
        # OPEN VIDEO
        # ==============================================

        cap = cv2.VideoCapture(
            input_path
        )


        if not cap.isOpened():
            raise RuntimeError(
                f"Could not open video: "
                f"{input_path}"
            )


        # ==============================================
        # VIDEO PROPERTIES
        # ==============================================

        fps = cap.get(
            cv2.CAP_PROP_FPS
        )

        width = int(
            cap.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )


        height = int(
            cap.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )


        total_frames = int(
            cap.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
        )


        print("=" * 70)
        print("VIDEO INFORMATION")
        print("=" * 70)
        print(
            f"Input: {input_path}"
        )
        print(
            f"FPS: {fps}"
        )
        print(
            f"Resolution: "
            f"{width}x{height}"
        )
        print(
            f"Total Frames: "
            f"{total_frames}"
        )
        print("=" * 70)

        # ==============================================
        # OUTPUT VIDEO WRITER
        # ==============================================

        fourcc = cv2.VideoWriter_fourcc(
            *"mp4v"
        )

        writer = cv2.VideoWriter(
            output_path,
            fourcc,
            fps,
            (
                width,
                height
            )
        )


        if not writer.isOpened():
            cap.release()
            raise RuntimeError(
                f"Could not create output video: "
                f"{output_path}"
            )

        # ==============================================
        # EVENT STATISTICS
        # ==============================================

        event_counts = {
            "vehicle_detected": 0,
            "vehicle_updated": 0,
            "vehicle_exited": 0
        }

        frame_number = 0

        # ==============================================
        # PROCESS VIDEO SAFELY
        # ==============================================

        try:
            # ==========================================
            # OPEN EVENTS FILE
            # ==========================================
            with open(
                events_path,
                "w",
                encoding="utf-8"
            ) as events_file:

                # ======================================
                # FRAME LOOP
                # ======================================

                while True:
                    success, frame = cap.read()
                    if not success:
                        break

                    frame_number += 1

                    # ==================================
                    # TIMESTAMP
                    # ==================================

                    timestamp = datetime.now()

                    # ==================================
                    # RUN TRAFFIC PIPELINE
                    # ==================================

                    result = (
                        self.pipeline.process_frame(
                            frame=frame,
                            frame_number=frame_number,
                            timestamp=timestamp,
                            camera_gps=camera_gps
                        )
                    )

                    # ==================================
                    # PROCESS EVENTS
                    # ==================================

                    for event in result["events"]:

                        # ------------------------------
                        # 1. SEND EVENT TO KAFKA
                        # ------------------------------
                        self.kafka_producer.send_event(
                            event
                        )

                        # ------------------------------
                        # 2. SAVE EVENT TO JSONL
                        # ------------------------------
                        events_file.write(
                            json.dumps(
                                event
                            )
                            +
                            "\n"
                        )

                        # ------------------------------
                        # 3. UPDATE EVENT COUNTS
                        # ------------------------------
                        event_type = event.get(
                            "event_type"
                        )

                        if event_type in event_counts:
                            event_counts[
                                event_type
                            ] += 1

                    # ==================================
                    # FLUSH EVENTS FILE
                    #
                    # Allows events.jsonl to be updated
                    # while video is still processing.
                    # ==================================

                    events_file.flush()


                    # ==================================
                    # DRAW RESULTS
                    # ==================================

                    output_frame = (
                        self.draw_results(
                            frame,
                            result
                        )
                    )


                    # ==================================
                    # WRITE OUTPUT FRAME
                    # ==================================

                    writer.write(
                        output_frame
                    )

                    # ==================================
                    # PROGRESS
                    # ==================================

                    if frame_number % 100 == 0:
                        progress = (
                            frame_number
                            /
                            total_frames
                            *
                            100
                        )

                        print(
                            f"Processed "
                            f"{frame_number}/"
                            f"{total_frames} "
                            f"({progress:.1f}%)"
                        )

        finally:


            # ==========================================
            # FLUSH KAFKA
            # ==========================================

            try:
                self.kafka_producer.flush()

            except Exception as error:
                print(
                    f"Kafka flush error: "
                    f"{error}"
                )

            # ==========================================
            # RELEASE VIDEO RESOURCES
            # ==========================================

            cap.release()
            writer.release()


        # ==============================================
        # CREATE SUMMARY
        # ==============================================

        summary = {
            "input_video": input_path,
            "output_video": output_path,
            "fps": fps,
            "resolution": {
                "width": width,
                "height": height
            },
            "total_frames": total_frames,
            "processed_frames": frame_number,
            "events": event_counts,
            "camera_gps": camera_gps,
            "completed_at": (
                datetime.now().isoformat()
            )
        }


        with open(
            summary_path,
            "w",
            encoding="utf-8"

        ) as summary_file:
            json.dump(
                summary,
                summary_file,
                indent=4
            )


        # ==============================================
        # COMPLETION MESSAGE
        # ==============================================

        print("=" * 70)
        print(
            "VIDEO PROCESSING COMPLETE"
        )

        print("=" * 70)
        print(
            f"Output saved to: "
            f"{output_path}"
        )
        print(
            f"Events saved to: "
            f"{events_path}"
        )
        print(
            f"Summary saved to: "
            f"{summary_path}"
        )

        return {

            "output_path": output_path,
            "events_path": events_path,
            "summary_path": summary_path
        }