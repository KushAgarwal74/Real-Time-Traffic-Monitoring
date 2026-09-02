import os
import glob
import cv2

from cv_pipeline.license_plate_ocr import (
    LicensePlateOCR
)

IMAGE_DIR = "."
image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.gif"]
image_path = []

def main():

    # ----------------------------------
    # Create OCR engine
    # ----------------------------------

    ocr = LicensePlateOCR()

    # ----------------------------------
    # Test image path
    # ----------------------------------

    for ext in image_extensions:

        image_path.extend(
            glob.glob(
                os.path.join(
                    IMAGE_DIR,
                    ext
                )
            )
        )

    for img_path in image_path:

        print(
            f"\nProcessing image: "
            f"{img_path}"
        )
        image = cv2.imread(img_path)

        if image is None:

            print(
                f"Could not load image: "
                f"{img_path}"
            )

            return

        # ----------------------------------
        # Run OCR
        # ----------------------------------

        result = ocr.read_plate(image)

        # ----------------------------------
        # Print result
        # ----------------------------------

        print("\nOCR RESULT")
        print("=" * 40)

        print(result)


if __name__ == "__main__":

    main()