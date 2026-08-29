from ultralytics import YOLO

class TrafficDetector:

    def __init__(self):
        # Small and fast model for initial testing
        self.model = YOLO("yolo11n.pt")

        self.vehicle_classes = {
            "car",
            "motorcycle",
            "bus",
            "truck"
        }

    def detect(self, frame):

        results = self.model(frame, verbose=False)

        detections = []

        for result in results:

            for box in result.boxes:

                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                class_name = self.model.names[class_id]

                if class_name not in self.vehicle_classes:
                    continue

                x1, y1, x2, y2 = box.xyxy[0].tolist()

                detections.append({
                    "class_name": class_name,
                    "confidence": confidence,
                    "bbox": [
                        int(x1),
                        int(y1),
                        int(x2),
                        int(y2)
                    ]
                })

        return detections