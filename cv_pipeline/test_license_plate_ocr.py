import cv2

from cv_pipeline.license_plate_detector import (
    LicensePlateDetector
)

from cv_pipeline.license_plate_ocr import (
    LicensePlateOCR
)


# ==========================================================
# TEST IMAGES
# ==========================================================

image_paths = [
    "./image_plate1.png",
    "./image_plate2.png",
    "./image_plate3.png",
    "./image_plate4.png",
    "./image_plate5.png"
]


# ==========================================================
# MAIN
# ==========================================================

def main():

    # ------------------------------------------------------
    # Create license plate detector
    # ------------------------------------------------------

    plate_detector = LicensePlateDetector(
        model_path="models/license-plate-finetune-v1s.pt",
        confidence_threshold=0.25
    )

    # ------------------------------------------------------
    # Create OCR engine
    # ------------------------------------------------------

    ocr = LicensePlateOCR(
        debug=True
    )

    # ------------------------------------------------------
    # Process images
    # ------------------------------------------------------

    for img_path in image_paths:

        print("\n")
        print("=" * 80)
        print(
            f"PROCESSING: {img_path}"
        )
        print("=" * 80)

        # --------------------------------------------------
        # Load image
        # --------------------------------------------------

        image = cv2.imread(
            img_path
        )

        if image is None:

            print(
                f"Could not load image: "
                f"{img_path}"
            )

            continue

        # --------------------------------------------------
        # Detect license plates
        # --------------------------------------------------

        plates = plate_detector.detect(
            image
        )

        print(
            f"Detected plates: "
            f"{len(plates)}"
        )

        if not plates:

            print(
                "No license plate detected."
            )

            continue

        # --------------------------------------------------
        # Print all detections
        # --------------------------------------------------

        for index, plate in enumerate(
            plates
        ):

            print(
                f"Plate {index + 1}: "
                f"bbox={plate['bbox']}, "
                f"confidence="
                f"{plate['confidence']:.3f}"
            )

        # --------------------------------------------------
        # Select highest-confidence plate
        # --------------------------------------------------

        best_plate = max(
            plates,
            key=lambda plate:
            plate["confidence"]
        )

        x1, y1, x2, y2 = (
            best_plate["bbox"]
        )

        # --------------------------------------------------
        # Clamp coordinates
        # --------------------------------------------------

        image_height, image_width = (
            image.shape[:2]
        )

        x1 = max(
            0,
            min(
                int(x1),
                image_width - 1
            )
        )

        y1 = max(
            0,
            min(
                int(y1),
                image_height - 1
            )
        )

        x2 = max(
            0,
            min(
                int(x2),
                image_width
            )
        )

        y2 = max(
            0,
            min(
                int(y2),
                image_height
            )
        )

        # --------------------------------------------------
        # Crop license plate
        # --------------------------------------------------

        plate_crop = image[
            y1:y2,
            x1:x2
        ]

        if plate_crop.size == 0:

            print(
                "Invalid plate crop."
            )

            continue

        # ==================================================
        # SAVE DETECTOR CROP
        # ==================================================

        filename = img_path.split("/")[-1]

        name, extension = (
            filename.rsplit(".", 1)
        )

        debug_filename = (
            f"debug_plate_{name}."
            f"{extension}"
        )

        cv2.imwrite(
            debug_filename,
            plate_crop
        )

        print(
            f"Saved plate crop: "
            f"{debug_filename}"
        )

        # ==================================================
        # CROP GEOMETRY
        # ==================================================

        crop_height, crop_width = (
            plate_crop.shape[:2]
        )

        aspect_ratio = (
            crop_width /
            float(crop_height)
            if crop_height > 0
            else 0.0
        )

        print(
            f"Plate crop size: "
            f"{crop_width}x{crop_height}"
        )

        print(
            f"Plate aspect ratio: "
            f"{aspect_ratio:.2f}"
        )

        # ==================================================
        # OCR
        # ==================================================

        result = ocr.read_plate(
            plate_crop
        )

        # ==================================================
        # RESULT
        # ==================================================

        print("\nOCR RESULT")
        print("=" * 50)

        print(
            result
        )


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    main()