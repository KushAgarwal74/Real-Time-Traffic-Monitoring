from cv_pipeline.license_plate_ocr import LicensePlateOCR
import cv2

ocr = LicensePlateOCR(
    aspect_ratio_threshold=2.0,
    debug=True
)

image = cv2.imread("path/to/plate.jpg")

result = ocr.read_plate(image)

print("\nFINAL RESULT")
print(result)