import cv2

from cv_pipeline.vehicle_plate_pipeline import (
    VehiclePlatePipeline
)

# IMAGE_DIR = "."
# image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.gif"]
# image_path = []

def main():

    # ----------------------------------
    # Load test image
    # ----------------------------------

    image_path = "test_image.jpg"

    frame = cv2.imread(
        image_path
    )

    if frame is None:

        print(
            "Could not load image"
        )

        return


    # ----------------------------------
    # Create pipeline
    # ----------------------------------

    pipeline = (
        VehiclePlatePipeline()
    )


    # ----------------------------------
    # Temporary vehicle bounding box
    #
    # Replace these coordinates with
    # the vehicle location in your image
    # ----------------------------------

    vehicle = {

        "track_id": 1,

        "class_name": "car",

        "bbox": [

            0,
            0,
            frame.shape[1],
            frame.shape[0]

        ]
    }


    # ----------------------------------
    # Process vehicle
    # ----------------------------------

    result = (
        pipeline.process_vehicle(

            frame,

            vehicle
        )
    )


    # ----------------------------------
    # Print result
    # ----------------------------------

    print()

    print(
        "VEHICLE PLATE PIPELINE RESULT"
    )

    print(
        "=" * 50
    )

    print(
        result
    )


    # ----------------------------------
    # Draw plate detection
    # ----------------------------------

    if result is not None:

        x1, y1, x2, y2 = (
            result["bbox"]
        )

        cv2.rectangle(

            frame,

            (x1, y1),

            (x2, y2),

            (0, 255, 0),

            2
        )


        # ----------------------------------
        # OCR text
        # ----------------------------------

        ocr = result.get(
            "ocr"
        )

        if ocr:

            text = ocr.get(
                "text",
                ""
            )

            confidence = ocr.get(
                "confidence",
                0
            )

            label = (
                f"{text} "
                f"{confidence:.2f}"
            )

        else:

            label = (
                "OCR: None"
            )


        cv2.putText(

            frame,

            label,

            (x1, max(30, y1 - 10)),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.7,

            (0, 255, 0),

            2
        )


    # ----------------------------------
    # Save output
    # ----------------------------------

    output_path = (
        "vehicle_plate_ocr_test.jpg"
    )

    cv2.imwrite(

        output_path,

        frame
    )


    print()

    print(
        f"Output saved: "
        f"{output_path}"
    )


if __name__ == "__main__":

    main()