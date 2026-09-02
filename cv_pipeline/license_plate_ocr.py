import cv2
import easyocr
import torch
import re

from cv_pipeline.plate_ocr_validator import PlateOCRValidator

class LicensePlateOCR:

    def __init__(self):

        use_gpu = torch.cuda.is_available()

        print(
            f"Loading EasyOCR "
            f"(GPU={use_gpu})..."
        )

        self.reader = easyocr.Reader(
            ["en"],
            gpu=use_gpu
        )

        self.validator = PlateOCRValidator()

    # ==================================================
    # PREPROCESSING VARIANTS
    # ==================================================

    def preprocess_variants(self, plate_image):

        variants = {}

        # ----------------------------------------------
        # 1. Original
        # ----------------------------------------------

        variants["original"] = plate_image


        # ----------------------------------------------
        # 2. Upscaled
        # ----------------------------------------------

        upscaled = cv2.resize(
            plate_image,
            None,
            fx=3,
            fy=3,
            interpolation=cv2.INTER_CUBIC
        )

        variants["upscaled"] = upscaled


        # ----------------------------------------------
        # Convert to grayscale
        # ----------------------------------------------

        gray = cv2.cvtColor(
            upscaled,
            cv2.COLOR_BGR2GRAY
        )


        # ----------------------------------------------
        # 3. CLAHE contrast enhancement
        # ----------------------------------------------

        clahe = cv2.createCLAHE(
            clipLimit=2.0,
            tileGridSize=(8, 8)
        )

        clahe_image = clahe.apply(
            gray
        )

        variants["clahe"] = clahe_image


        # ----------------------------------------------
        # 4. Sharpened
        # ----------------------------------------------

        blurred = cv2.GaussianBlur(
            gray,
            (0, 0),
            3
        )

        sharpened = cv2.addWeighted(
            gray,
            1.8,
            blurred,
            -0.8,
            0
        )

        variants["sharpened"] = sharpened


        # ----------------------------------------------
        # 5. Otsu Threshold
        # ----------------------------------------------

        _, otsu = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY +
            cv2.THRESH_OTSU
        )

        variants["otsu"] = otsu


        # ----------------------------------------------
        # 6. Adaptive Threshold
        # ----------------------------------------------

        adaptive = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            5
        )

        variants["adaptive"] = adaptive


        return variants


    # ==================================================
    # CLEAN OCR TEXT
    # ==================================================

    def clean_text(self, text):

        text = text.upper()

        text = re.sub(
            r"[^A-Z0-9]",
            "",
            text
        )

        return text


    # ==================================================
    # SCORE OCR RESULT
    # ==================================================

    def score_result(
        self,
        text,
        confidence
    ):

        if not text:

            return 0.0, None

        validation = self.validator.validate(
            text
        )

        format_score = validation[
            "format_score"
        ]

        is_valid = validation[
            "is_valid"
        ]

        # ------------------------------------------
        # Main weighted score
        # ------------------------------------------

        score = (

            0.4 * confidence

            +

            0.6 * format_score
        )

        # ------------------------------------------
        # Strong penalty for invalid OCR
        # ------------------------------------------

        if not is_valid:

            score *= 0.5

        # ------------------------------------------
        # Extra penalty for very short OCR
        #
        # Prevents:
        # "MH"
        # "05502"
        #
        # from winning just because OCR confidence
        # is high.
        # ------------------------------------------

        if len(text) < 6:

            score *= 0.4

        return score, validation

    # ==================================================
    # OCR ONE IMAGE
    # ==================================================

    def run_ocr(
        self,
        image
    ):

        results = self.reader.readtext(
            image,
            detail=1,
            paragraph=False,
            allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        )

        candidates = []

        segments = []

        for result in results:

            bbox, text, confidence = result

            cleaned_text = self.clean_text(
                text
            )

            if not cleaned_text:
                continue

            # ------------------------------------------
            # Get approximate position of OCR text
            # ------------------------------------------

            x = min(
                point[0]
                for point in bbox
            )

            y = min(
                point[1]
                for point in bbox
            )

            segments.append({

                "text": cleaned_text,

                "confidence": float(
                    confidence
                ),

                "x": x,

                "y": y
            })

        # ------------------------------------------
        # Sort OCR segments
        #
        # Important for Indian two-line plates:
        #
        # MH12Z
        # H6131
        #
        # Result:
        # MH12ZH6131
        # ------------------------------------------

        segments.sort(
            key=lambda item: (
                item["y"],
                item["x"]
            )
        )

        # ------------------------------------------
        # Add individual candidates
        # ------------------------------------------

        for segment in segments:

            candidates.append({

                "text": segment["text"],

                "confidence": segment[
                    "confidence"
                ]
            })

        # ------------------------------------------
        # Add combined candidate
        # ------------------------------------------

        if len(segments) >= 2:

            combined_text = "".join(

                segment["text"]

                for segment in segments
            )

            average_confidence = (

                sum(

                    segment["confidence"]

                    for segment in segments
                )

                /

                len(segments)
            )

            candidates.append({

                "text": combined_text,

                "confidence": float(
                    average_confidence
                )
            })

        return candidates


    # ==================================================
    # READ LICENSE PLATE
    # ==================================================

    def read_plate(
        self,
        plate_image
    ):

        if (
            plate_image is None
            or
            plate_image.size == 0
        ):

            return None


        variants = self.preprocess_variants(
            plate_image
        )


        best_result = None

        best_score = -1


        # ----------------------------------------------
        # Try OCR on every preprocessing variant
        # ----------------------------------------------

        for method, image in variants.items():

            candidates = self.run_ocr(
                image
            )

            for candidate in candidates:

                text = candidate["text"]

                confidence = candidate[
                    "confidence"
                ]

                score, validation = self.score_result(
                    text,
                    confidence
                )

                # Debugging
                # print(

                #     f"OCR [{method}] "
                #     f"-> {text} "
                #     f"(conf={confidence:.3f}, "
                #     f"format={validation['format_score']:.3f}, "
                #     f"valid={validation['is_valid']}, "
                #     f"score={score:.3f})"

                # )

                if score > best_score:

                    best_score = score

                    best_result = {

                        "text": text,

                        "confidence": confidence,

                        "method": method,

                        "score": float(best_score),

                        "validation": validation
                    }


        return best_result