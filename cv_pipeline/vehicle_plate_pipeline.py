from cv_pipeline.license_plate_detector import (
    LicensePlateDetector
)

from cv_pipeline.plate_validator import (
    PlateValidator
)

from cv_pipeline.license_plate_ocr import (
    LicensePlateOCR
)

from cv_pipeline.plate_ocr_validator import (
    PlateOCRValidator
)

from cv_pipeline.plate_ocr_aggregator import (
    PlateOCRAggregator
)

class VehiclePlatePipeline:

    def __init__(self, model_path = "models/license-plate-finetune-v1s.pt"):

        self.plate_detector = (
            LicensePlateDetector(model_path=model_path)
        )

        self.plate_validator = (
            PlateValidator()
        )

        self.plate_ocr = (
            LicensePlateOCR()
        )

        self.ocr_validator = (
            PlateOCRValidator()
        )

        self.ocr_aggregator = (
            PlateOCRAggregator()
        )

    def process_vehicle(
        self,
        frame,
        vehicle
    ):

        """
        Process one tracked vehicle.

        Steps:

        1. Crop vehicle
        2. Detect plate candidates
        3. Validate candidates
        4. Select best plate
        5. Convert coordinates to full frame
        """

        x1, y1, x2, y2 = (
            vehicle["bbox"]
        )

        frame_height, frame_width = (
            frame.shape[:2]
        )

        # ----------------------------------
        # Clamp coordinates
        # ----------------------------------

        x1 = max(0, x1)

        y1 = max(0, y1)

        x2 = min(frame_width, x2)

        y2 = min(frame_height, y2)

        # ----------------------------------
        # Validate vehicle bounding box
        # ----------------------------------

        if x2 <= x1 or y2 <= y1:

            return None

        # ----------------------------------
        # Crop vehicle
        # ----------------------------------

        vehicle_crop = frame[
            y1:y2,
            x1:x2
        ]

        if vehicle_crop is None:

            return None

        if vehicle_crop.size == 0:

            return None

        vehicle_height, vehicle_width = (
            vehicle_crop.shape[:2]
        )

        # ----------------------------------
        # Detect plate candidates
        # ----------------------------------

        detected_plates = self.plate_detector.detect(
            vehicle_crop
        )

        # print("\nDEBUG")
        # print("Vehicle bbox:", vehicle["bbox"])
        # print("Vehicle crop shape:", vehicle_crop.shape)
        # print("Raw detected plates:", detected_plates)

        # ----------------------------------
        # Validate and select best plate
        # ----------------------------------

        best_plate = (
            self.plate_validator.get_best_plate(

                plates=detected_plates,

                vehicle_width=vehicle_width,

                vehicle_height=vehicle_height
            )
        )

        # valid_plates = self.plate_validator.filter_plates(
        #     plates=detected_plates,
        #     vehicle_width=vehicle_width,
        #     vehicle_height=vehicle_height
        # )

        # print("Raw plates:", detected_plates)
        # print("Valid plates:", valid_plates)

        # if not valid_plates:
        #     return None

        # best_plate = max(
        #     valid_plates,
        #     key=lambda plate: plate["confidence"]
        # )

        # ----------------------------------
        # No valid plate
        # ----------------------------------

        if best_plate is None:

            return None

        # ----------------------------------
        # Convert coordinates to full frame
        # ----------------------------------

        px1, py1, px2, py2 = (
            best_plate["bbox"]
        )

        full_x1 = int(x1 + px1)

        full_y1 = int(y1 + py1)

        full_x2 = int(x1 + px2)

        full_y2 = int(y1 + py2)

        # ----------------------------------
        # Crop detected plate
        # ----------------------------------

        plate_crop = frame[
            full_y1:full_y2,
            full_x1:full_x2
        ]

        # ----------------------------------
        # Run OCR
        # ----------------------------------

        ocr_result = None

        ocr_validation = None

        ocr_usable = False

        if plate_crop is not None and plate_crop.size > 0:

            ocr_result = self.plate_ocr.read_plate(
                plate_crop
            )

            # ----------------------------------
            # Validate OCR text
            # ----------------------------------

            if ocr_result is not None:

                ocr_validation = (
                    self.ocr_validator.validate(
                        ocr_result.get("text")
                    )
                )

                # ----------------------------------
                # OCR quality gate
                # ----------------------------------

                ocr_usable = (
                    self.ocr_validator.is_usable(
                        ocr_result=ocr_result,
                        validation_result=ocr_validation
                    )
                )

                # ----------------------------------
                # Add only usable OCR observations
                # to temporal aggregator
                # ----------------------------------

                if ocr_usable:

                    self.ocr_aggregator.add_observation(

                        track_id=vehicle[
                            "track_id"
                        ],

                        ocr_result=ocr_result,

                        format_result=ocr_validation,

                        plate_confidence=best_plate[
                            "confidence"
                        ]
                    )

        # ----------------------------------
        # Return event-ready plate data
        # ----------------------------------

        return {

            "track_id": int(
                vehicle["track_id"]
            ),

            "bbox": [
                full_x1,
                full_y1,
                full_x2,
                full_y2
            ],

            "confidence": float(
                best_plate["confidence"]
            ),

            # ----------------------------------
            # Current frame OCR result
            # ----------------------------------

            "ocr": ocr_result,

            # ----------------------------------
            # OCR validation
            # ----------------------------------

            "ocr_validation": ocr_validation,

            "ocr_usable": ocr_usable,

            # ----------------------------------
            # Best OCR result accumulated
            # across this vehicle track
            # ----------------------------------

            "best_ocr": (
                self.ocr_aggregator.get_best_plate(
                    vehicle["track_id"]
                )
            )
        }


    def process_frame(
        self,
        frame,
        tracked_objects
    ):

        """
        Process all tracked vehicles.

        Returns a dictionary:

        {
            track_id: plate_data
        }
        """

        plates_by_track = {}

        for vehicle in tracked_objects:

            plate = self.process_vehicle(

                frame,

                vehicle
            )

            if plate is not None:

                track_id = plate["track_id"]

                plates_by_track[
                    track_id
                ] = plate

        return plates_by_track

    def clear_track(
        self,
        track_id
    ):

        """
        Clear OCR observations for a vehicle
        after the vehicle exits.
        """

        self.ocr_aggregator.clear_track(
            track_id
        )