from ultralytics import YOLO

from cv_pipeline.device import get_device


class LicensePlateDetector:

    def __init__(
        self,
        model_path="license-plate-finetune-v1s.pt",
        confidence_threshold=0.25
    ):

        self.device = get_device()

        # print(
        #     f"Loading license plate model: "
        #     f"{model_path}"
        # )

        self.model = YOLO(
            model_path
        )

        self.confidence_threshold = (
            confidence_threshold
        )


    def detect(
        self,
        vehicle_crop
    ):

        if vehicle_crop is None:

            return []

        if vehicle_crop.size == 0:

            return []

        results = self.model.predict(

            source=vehicle_crop,

            conf=self.confidence_threshold,

            device=self.device,

            verbose=False
        )

        detected_plates = []

        for result in results:

            if result.boxes is None:

                continue

            for box in result.boxes:

                confidence = float(
                    box.conf[0]
                )

                x1, y1, x2, y2 = (
                    box.xyxy[0].tolist()
                )

                detected_plates.append({

                    "bbox": [

                        int(x1),

                        int(y1),

                        int(x2),

                        int(y2)
                    ],

                    "confidence": confidence
                })

        return detected_plates