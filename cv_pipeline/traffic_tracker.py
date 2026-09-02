from ultralytics import YOLO

from cv_pipeline.device import get_device


class TrafficTracker:

    def __init__(self):

        self.device = get_device()

        self.model = YOLO(
            "yolo11n.pt"
        )

        self.vehicle_classes = {
            "car",
            "motorcycle",
            "bus",
            "truck"
        }


    def track(self, frame):

        results = self.model.track(

            frame,

            persist=True,

            tracker="bytetrack.yaml",

            verbose=False,

            device=self.device
        )

        tracked_objects = []

        for result in results:

            if result.boxes is None:

                continue

            for box in result.boxes:

                class_id = int(
                    box.cls[0]
                )

                confidence = float(
                    box.conf[0]
                )

                class_name = (
                    self.model.names[class_id]
                )

                # Ignore objects we don't care about

                if class_name not in self.vehicle_classes:

                    continue

                # Track ID may not exist initially

                if box.id is None:

                    continue

                track_id = int(
                    box.id[0]
                )

                x1, y1, x2, y2 = (
                    box.xyxy[0].tolist()
                )

                tracked_objects.append({

                    "track_id": track_id,

                    "class_name": class_name,

                    "confidence": confidence,

                    "bbox": [

                        int(x1),

                        int(y1),

                        int(x2),

                        int(y2)
                    ]
                })

        return tracked_objects