class PlateValidator:

    def __init__(
        self,
        min_confidence=0.30,
        min_aspect_ratio=1.2,
        max_aspect_ratio=10.0,
        min_width_ratio=0.02,
        max_width_ratio=0.80,
        min_height_ratio=0.01,
        max_height_ratio=0.40
    ):

        self.min_confidence = min_confidence

        self.min_aspect_ratio = min_aspect_ratio

        self.max_aspect_ratio = max_aspect_ratio

        self.min_width_ratio = min_width_ratio

        self.max_width_ratio = max_width_ratio

        self.min_height_ratio = min_height_ratio

        self.max_height_ratio = max_height_ratio


    def is_valid(
        self,
        plate,
        vehicle_width,
        vehicle_height
    ):

        confidence = plate["confidence"]

        if confidence < self.min_confidence:
            return False


        x1, y1, x2, y2 = plate["bbox"]

        plate_width = x2 - x1
        plate_height = y2 - y1


        if plate_width <= 0 or plate_height <= 0:
            return False


        aspect_ratio = (
            plate_width / plate_height
        )


        if (
            aspect_ratio < self.min_aspect_ratio
            or aspect_ratio > self.max_aspect_ratio
        ):
            return False


        width_ratio = (
            plate_width / vehicle_width
        )

        height_ratio = (
            plate_height / vehicle_height
        )


        if (
            width_ratio < self.min_width_ratio
            or width_ratio > self.max_width_ratio
        ):
            return False


        if (
            height_ratio < self.min_height_ratio
            or height_ratio > self.max_height_ratio
        ):
            return False


        return True


    def filter_plates(
        self,
        plates,
        vehicle_width,
        vehicle_height
    ):

        valid_plates = []

        for plate in plates:

            if self.is_valid(
                plate,
                vehicle_width,
                vehicle_height
            ):
                valid_plates.append(
                    plate
                )

        return valid_plates


    def get_best_plate(
        self,
        plates,
        vehicle_width,
        vehicle_height
    ):

        valid_plates = self.filter_plates(

            plates=plates,

            vehicle_width=vehicle_width,

            vehicle_height=vehicle_height
        )

        if not valid_plates:
            return None


        return max(
            valid_plates,
            key=lambda plate: plate["confidence"]
        )