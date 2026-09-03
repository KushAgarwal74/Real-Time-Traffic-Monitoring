import cv2
import easyocr
import torch
import re
import numpy as np

from cv_pipeline.plate_ocr_validator import (
    PlateOCRValidator
)


class LicensePlateOCR:

    def __init__(
        self,
        aspect_ratio_threshold=2.0,
        debug=False,
        target_height=96,
        padding_ratio=0.05,
        early_stop_score=1.10,
        early_stop_confidence=0.90
    ):
        """
        License Plate OCR Engine - Version 4.

        Pipeline:

            detector crop
                ↓
            padding
                ↓
            geometry normalization
                ↓
            fixed-height resize
                ↓
            preprocessing
                ↓
            single/two-line OCR
                ↓
            candidate scoring

        Parameters
        ----------
        aspect_ratio_threshold : float
            Used only as a layout hint.

        debug : bool
            Print OCR candidates.

        target_height : int
            Target height used when resizing plate crops.

        padding_ratio : float
            Padding added around detector crop.

        early_stop_score : float
            Minimum score for early termination.

        early_stop_confidence : float
            Minimum OCR confidence for early termination.
        """

        self.aspect_ratio_threshold = (
            aspect_ratio_threshold
        )

        self.debug = debug

        self.target_height = (
            target_height
        )

        self.padding_ratio = (
            padding_ratio
        )

        self.early_stop_score = (
            early_stop_score
        )

        self.early_stop_confidence = (
            early_stop_confidence
        )

        # ==================================================
        # EASY OCR
        # ==================================================

        use_gpu = torch.cuda.is_available()

        print(
            f"Loading EasyOCR "
            f"(GPU={use_gpu})..."
        )

        self.reader = easyocr.Reader(
            ["en"],
            gpu=use_gpu
        )

        self.validator = (
            PlateOCRValidator()
        )

    # ======================================================
    # IMAGE GEOMETRY
    # ======================================================

    def get_aspect_ratio(
        self,
        image
    ):
        """
        Return width / height.
        """

        if (
            image is None
            or
            image.size == 0
        ):
            return 0.0

        height, width = (
            image.shape[:2]
        )

        if height <= 0:
            return 0.0

        return (
            width /
            float(height)
        )

    # ======================================================
    # LAYOUT HINT
    # ======================================================

    def classify_crop_layout(
        self,
        plate_image
    ):
        """
        Classify crop geometry.

        IMPORTANT:
        This is only a hint.

        We still test both single-line and two-line
        interpretations where appropriate.
        """

        aspect_ratio = (
            self.get_aspect_ratio(
                plate_image
            )
        )

        if aspect_ratio <= 0:
            return "unknown"

        if (
            aspect_ratio
            >=
            self.aspect_ratio_threshold
        ):
            return "single_line"

        return "two_line"

    # ======================================================
    # ADD PADDING
    # ======================================================

    def add_padding(
        self,
        image
    ):
        """
        Add a small amount of border around the detector crop.

        Detector bounding boxes can occasionally cut very
        close to the characters.
        """

        if (
            image is None
            or
            image.size == 0
        ):
            return image

        height, width = (
            image.shape[:2]
        )

        pad_x = max(
            int(
                width *
                self.padding_ratio
            ),
            2
        )

        pad_y = max(
            int(
                height *
                self.padding_ratio
            ),
            2
        )

        padded = cv2.copyMakeBorder(
            image,
            pad_y,
            pad_y,
            pad_x,
            pad_x,
            cv2.BORDER_REPLICATE
        )

        return padded

    # ======================================================
    # FOUR POINT ORDERING
    # ======================================================

    def order_points(
        self,
        points
    ):
        """
        Order quadrilateral points as:

            top-left
            top-right
            bottom-right
            bottom-left
        """

        points = np.asarray(
            points,
            dtype=np.float32
        )

        ordered = np.zeros(
            (4, 2),
            dtype=np.float32
        )

        sums = (
            points[:, 0]
            +
            points[:, 1]
        )

        differences = (
            points[:, 0]
            -
            points[:, 1]
        )

        ordered[0] = points[
            np.argmin(sums)
        ]

        ordered[2] = points[
            np.argmax(sums)
        ]

        ordered[1] = points[
            np.argmax(differences)
        ]

        ordered[3] = points[
            np.argmin(differences)
        ]

        return ordered

    # ======================================================
    # PERSPECTIVE NORMALIZATION
    # ======================================================

    def perspective_normalize(
        self,
        image
    ):
        """
        Attempt to correct moderate perspective distortion.

        This uses the outer plate boundary only when a clear
        quadrilateral can be detected.

        If no reliable boundary is found, the original image
        is returned.

        This is deliberately conservative.
        """

        if (
            image is None
            or
            image.size == 0
        ):
            return image

        height, width = (
            image.shape[:2]
        )

        if (
            width < 30
            or
            height < 15
        ):
            return image

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

        # --------------------------------------------------
        # Slight blur to suppress noise
        # --------------------------------------------------

        blurred = cv2.GaussianBlur(
            gray,
            (3, 3),
            0
        )

        # --------------------------------------------------
        # Edge detection
        # --------------------------------------------------

        edges = cv2.Canny(
            blurred,
            50,
            150
        )

        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_LIST,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return image

        image_area = (
            width *
            height
        )

        best_quad = None
        best_area = 0.0

        # --------------------------------------------------
        # Search for a plausible large quadrilateral
        # --------------------------------------------------

        for contour in contours:

            contour_area = abs(
                cv2.contourArea(
                    contour
                )
            )

            if contour_area <= 0:
                continue

            area_ratio = (
                contour_area /
                float(image_area)
            )

            if area_ratio < 0.35:
                continue

            perimeter = cv2.arcLength(
                contour,
                True
            )

            if perimeter <= 0:
                continue

            approximation = (
                cv2.approxPolyDP(
                    contour,
                    0.03 * perimeter,
                    True
                )
            )

            if len(approximation) != 4:
                continue

            points = (
                approximation.reshape(
                    4,
                    2
                )
            )

            ordered = (
                self.order_points(
                    points
                )
            )

            # ------------------------------------------------
            # Check resulting geometry
            # ------------------------------------------------

            tl, tr, br, bl = ordered

            top_width = np.linalg.norm(
                tr - tl
            )

            bottom_width = np.linalg.norm(
                br - bl
            )

            left_height = np.linalg.norm(
                bl - tl
            )

            right_height = np.linalg.norm(
                br - tr
            )

            max_width = max(
                top_width,
                bottom_width
            )

            max_height = max(
                left_height,
                right_height
            )

            if (
                max_width < 20
                or
                max_height < 10
            ):
                continue

            candidate_ratio = (
                max_width /
                max_height
            )

            # ------------------------------------------------
            # License plates should not be extremely tall.
            # ------------------------------------------------

            if candidate_ratio < 1.2:
                continue

            if candidate_ratio > 10.0:
                continue

            if contour_area > best_area:

                best_area = (
                    contour_area
                )

                best_quad = ordered

        if best_quad is None:
            return image

        # ==================================================
        # DESTINATION SIZE
        # ==================================================

        tl, tr, br, bl = (
            best_quad
        )

        width_top = np.linalg.norm(
            tr - tl
        )

        width_bottom = np.linalg.norm(
            br - bl
        )

        height_left = np.linalg.norm(
            bl - tl
        )

        height_right = np.linalg.norm(
            br - tr
        )

        output_width = max(
            int(width_top),
            int(width_bottom),
            30
        )

        output_height = max(
            int(height_left),
            int(height_right),
            15
        )

        destination = np.array(
            [
                [0, 0],
                [output_width - 1, 0],
                [
                    output_width - 1,
                    output_height - 1
                ],
                [
                    0,
                    output_height - 1
                ]
            ],
            dtype=np.float32
        )

        matrix = cv2.getPerspectiveTransform(
            best_quad,
            destination
        )

        normalized = cv2.warpPerspective(
            image,
            matrix,
            (
                output_width,
                output_height
            ),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )

        return normalized

    # ======================================================
    # FIXED HEIGHT RESIZE
    # ======================================================

    def resize_to_target_height(
        self,
        image
    ):
        """
        Resize the plate to a consistent character height.

        This is particularly useful for very small detections
        such as the 94x32 crop from image 5.
        """

        if (
            image is None
            or
            image.size == 0
        ):
            return image

        height, width = (
            image.shape[:2]
        )

        if height <= 0:
            return image

        scale = (
            self.target_height /
            float(height)
        )

        new_width = max(
            int(width * scale),
            1
        )

        resized = cv2.resize(
            image,
            (
                new_width,
                self.target_height
            ),
            interpolation=cv2.INTER_CUBIC
        )

        return resized

    # ======================================================
    # GEOMETRY NORMALIZATION
    # ======================================================

    def normalize_plate_image(
        self,
        plate_image
    ):
        """
        Complete image normalization.
        """

        if (
            plate_image is None
            or
            plate_image.size == 0
        ):
            return None

        # --------------------------------------------------
        # Padding
        # --------------------------------------------------

        padded = self.add_padding(
            plate_image
        )

        # --------------------------------------------------
        # Perspective normalization
        # --------------------------------------------------

        normalized = (
            self.perspective_normalize(
                padded
            )
        )

        # --------------------------------------------------
        # Fixed-height resize
        # --------------------------------------------------

        normalized = (
            self.resize_to_target_height(
                normalized
            )
        )

        return normalized

    # ======================================================
    # PREPROCESSING VARIANTS
    # ======================================================

    def preprocess_variants(
        self,
        plate_image
    ):
        """
        Generate OCR preprocessing variants.

        The normalized image is used as the main source.
        """

        variants = {}

        # --------------------------------------------------
        # Original detector crop
        # --------------------------------------------------

        variants[
            "original"
        ] = plate_image

        # --------------------------------------------------
        # Geometry-normalized crop
        # --------------------------------------------------

        normalized = (
            self.normalize_plate_image(
                plate_image
            )
        )

        if normalized is not None:

            variants[
                "normalized"
            ] = normalized

        # --------------------------------------------------
        # Upscaled original
        # --------------------------------------------------

        upscaled = cv2.resize(
            plate_image,
            None,
            fx=3,
            fy=3,
            interpolation=cv2.INTER_CUBIC
        )

        variants[
            "upscaled"
        ] = upscaled

        # --------------------------------------------------
        # Grayscale normalized
        # --------------------------------------------------

        source = (
            normalized
            if normalized is not None
            else upscaled
        )

        gray = cv2.cvtColor(
            source,
            cv2.COLOR_BGR2GRAY
        )

        # --------------------------------------------------
        # CLAHE
        # --------------------------------------------------

        clahe = cv2.createCLAHE(
            clipLimit=2.0,
            tileGridSize=(8, 8)
        )

        clahe_image = clahe.apply(
            gray
        )

        variants[
            "clahe"
        ] = clahe_image

        # --------------------------------------------------
        # Sharpened
        # --------------------------------------------------

        blurred = cv2.GaussianBlur(
            gray,
            (0, 0),
            2
        )

        sharpened = cv2.addWeighted(
            gray,
            1.6,
            blurred,
            -0.6,
            0
        )

        variants[
            "sharpened"
        ] = sharpened

        # --------------------------------------------------
        # Otsu
        # --------------------------------------------------

        _, otsu = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY
            +
            cv2.THRESH_OTSU
        )

        variants[
            "otsu"
        ] = otsu

        # --------------------------------------------------
        # Adaptive threshold
        # --------------------------------------------------

        adaptive = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            5
        )

        variants[
            "adaptive"
        ] = adaptive

        return variants

    # ======================================================
    # CLEAN OCR TEXT
    # ======================================================

    def clean_text(
        self,
        text
    ):
        """
        Normalize OCR text.
        """

        if not text:
            return ""

        text = text.upper()

        text = re.sub(
            r"[^A-Z0-9]",
            "",
            text
        )

        return text

    # ======================================================
    # OCR SEGMENTS
    # ======================================================

    def get_ocr_segments(
        self,
        image
    ):
        """
        Run EasyOCR and preserve bounding-box geometry.
        """

        results = self.reader.readtext(
            image,
            detail=1,
            paragraph=False,
            allowlist=(
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                "0123456789"
            )
        )

        segments = []

        for result in results:

            bbox, text, confidence = (
                result
            )

            cleaned_text = (
                self.clean_text(
                    text
                )
            )

            if not cleaned_text:
                continue

            xs = [
                point[0]
                for point in bbox
            ]

            ys = [
                point[1]
                for point in bbox
            ]

            x_min = min(xs)
            x_max = max(xs)

            y_min = min(ys)
            y_max = max(ys)

            width = (
                x_max -
                x_min
            )

            height = (
                y_max -
                y_min
            )

            center_x = (
                x_min +
                x_max
            ) / 2.0

            center_y = (
                y_min +
                y_max
            ) / 2.0

            segments.append({

                "text":
                    cleaned_text,

                "confidence":
                    float(
                        confidence
                    ),

                "x":
                    float(x_min),

                "y":
                    float(y_min),

                "width":
                    float(width),

                "height":
                    float(height),

                "center_x":
                    float(center_x),

                "center_y":
                    float(center_y)
            })

        return segments

    # ======================================================
    # FILTER SMALL / AUXILIARY TEXT
    # ======================================================

    def filter_auxiliary_segments(
        self,
        segments
    ):
        """
        Remove very small OCR detections.

        This is useful for auxiliary markings such as the
        small "IND" printed on many Indian plates.

        No text itself is hardcoded.
        """

        if len(segments) <= 1:
            return segments

        heights = [
            segment["height"]
            for segment in segments
            if segment["height"] > 0
        ]

        if not heights:
            return segments

        median_height = float(
            np.median(
                heights
            )
        )

        filtered = []

        for segment in segments:

            height = (
                segment["height"]
            )

            text = (
                segment["text"]
            )

            # ------------------------------------------------
            # Tiny relative to normal characters
            # ------------------------------------------------

            if (
                height
                <
                median_height * 0.55
            ):
                continue

            # ------------------------------------------------
            # Very short and relatively small
            # ------------------------------------------------

            if (
                len(text) <= 3
                and
                height
                <
                median_height * 0.70
            ):
                continue

            filtered.append(
                segment
            )

        # --------------------------------------------------
        # Safety fallback
        # --------------------------------------------------

        if not filtered:
            return segments

        return filtered

    # ======================================================
    # GROUP OCR SEGMENTS INTO ROWS
    # ======================================================

    def group_segments_into_rows(
        self,
        segments
    ):
        """
        Group OCR detections by vertical position.
        """

        if not segments:
            return []

        sorted_segments = sorted(
            segments,
            key=lambda item:
            item["center_y"]
        )

        heights = [
            segment["height"]
            for segment in sorted_segments
            if segment["height"] > 0
        ]

        if not heights:
            return [
                sorted_segments
            ]

        median_height = float(
            np.median(
                heights
            )
        )

        tolerance = max(
            median_height * 0.65,
            4.0
        )

        rows = []

        for segment in sorted_segments:

            best_row = None
            best_distance = (
                float("inf")
            )

            for row in rows:

                row_center = (
                    sum(
                        item[
                            "center_y"
                        ]
                        for item in row
                    )
                    /
                    len(row)
                )

                distance = abs(
                    segment[
                        "center_y"
                    ]
                    -
                    row_center
                )

                if (
                    distance
                    <= tolerance
                    and
                    distance
                    <
                    best_distance
                ):

                    best_row = row
                    best_distance = (
                        distance
                    )

            if best_row is not None:

                best_row.append(
                    segment
                )

            else:

                rows.append([
                    segment
                ])

        # --------------------------------------------------
        # Sort rows top -> bottom
        # --------------------------------------------------

        rows.sort(
            key=lambda row:
            sum(
                item[
                    "center_y"
                ]
                for item in row
            )
            /
            len(row)
        )

        # --------------------------------------------------
        # Sort characters left -> right
        # --------------------------------------------------

        for row in rows:

            row.sort(
                key=lambda item:
                item["center_x"]
            )

        return rows

    # ======================================================
    # COMBINE SINGLE-LINE SEGMENTS
    # ======================================================

    def combine_single_line_segments(
        self,
        segments
    ):
        """
        Combine all OCR segments left -> right.
        """

        if not segments:
            return None

        ordered = sorted(
            segments,
            key=lambda item:
            item["center_x"]
        )

        text = "".join(
            item["text"]
            for item in ordered
        )

        if not text:
            return None

        confidence = (
            sum(
                item["confidence"]
                for item in ordered
            )
            /
            len(ordered)
        )

        return {

            "text":
                text,

            "confidence":
                float(
                    confidence
                )
        }

    # ======================================================
    # COMBINE ROWS
    # ======================================================

    def combine_rows(
        self,
        rows
    ):
        """
        Combine rows top -> bottom.
        """

        if not rows:
            return None

        row_texts = []
        row_confidences = []

        for row in rows:

            if not row:
                continue

            row.sort(
                key=lambda item:
                item["center_x"]
            )

            text = "".join(
                item["text"]
                for item in row
            )

            if not text:
                continue

            confidence = (
                sum(
                    item["confidence"]
                    for item in row
                )
                /
                len(row)
            )

            row_texts.append(
                text
            )

            row_confidences.append(
                confidence
            )

        if not row_texts:
            return None

        combined_text = "".join(
            row_texts
        )

        confidence = (
            sum(row_confidences)
            /
            len(row_confidences)
        )

        return {

            "text":
                combined_text,

            "confidence":
                float(
                    confidence
                )
        }

    # ======================================================
    # SINGLE-LINE CANDIDATES
    # ======================================================

    def generate_single_line_candidates(
        self,
        segments
    ):
        """
        Generate candidates assuming one row.
        """

        candidates = []

        if not segments:
            return candidates

        segments = (
            self.filter_auxiliary_segments(
                segments
            )
        )

        # --------------------------------------------------
        # Individual OCR segments
        # --------------------------------------------------

        for segment in segments:

            candidates.append({

                "text":
                    segment["text"],

                "confidence":
                    segment[
                        "confidence"
                    ],

                "method_suffix":
                    "single_segment"
            })

        # --------------------------------------------------
        # Combined candidate
        # --------------------------------------------------

        combined = (
            self.combine_single_line_segments(
                segments
            )
        )

        if combined:

            candidates.append({

                "text":
                    combined["text"],

                "confidence":
                    combined[
                        "confidence"
                    ],

                "method_suffix":
                    "single_line_combined"
            })

        return candidates

    # ======================================================
    # TWO-LINE CANDIDATES
    # ======================================================

    def generate_two_line_candidates(
        self,
        segments
    ):
        """
        Generate candidates using OCR bounding-box rows.
        """

        candidates = []

        if not segments:
            return candidates

        segments = (
            self.filter_auxiliary_segments(
                segments
            )
        )

        rows = (
            self.group_segments_into_rows(
                segments
            )
        )

        if len(rows) < 2:
            return candidates

        combined = (
            self.combine_rows(
                rows
            )
        )

        if combined:

            candidates.append({

                "text":
                    combined["text"],

                "confidence":
                    combined[
                        "confidence"
                    ],

                "method_suffix":
                    "row_grouping"
            })

        return candidates

    # ======================================================
    # HORIZONTAL SPLIT OCR
    # ======================================================

    def generate_horizontal_split_candidate(
        self,
        image
    ):
        """
        Explicitly split a two-line plate into top and
        bottom regions.

        A small overlap prevents characters near the
        center boundary from being cut.
        """

        if (
            image is None
            or
            image.size == 0
        ):
            return []

        height = image.shape[0]

        if height < 20:
            return []

        middle = height // 2

        overlap = max(
            int(
                height * 0.08
            ),
            2
        )

        top_end = min(
            height,
            middle + overlap
        )

        bottom_start = max(
            0,
            middle - overlap
        )

        top_image = image[
            0:top_end,
            :
        ]

        bottom_image = image[
            bottom_start:height,
            :
        ]

        # --------------------------------------------------
        # OCR top
        # --------------------------------------------------

        top_segments = (
            self.get_ocr_segments(
                top_image
            )
        )

        # --------------------------------------------------
        # OCR bottom
        # --------------------------------------------------

        bottom_segments = (
            self.get_ocr_segments(
                bottom_image
            )
        )

        if (
            not top_segments
            or
            not bottom_segments
        ):
            return []

        top_segments = (
            self.filter_auxiliary_segments(
                top_segments
            )
        )

        bottom_segments = (
            self.filter_auxiliary_segments(
                bottom_segments
            )
        )

        top_segments.sort(
            key=lambda item:
            item["center_x"]
        )

        bottom_segments.sort(
            key=lambda item:
            item["center_x"]
        )

        top_text = "".join(
            item["text"]
            for item in top_segments
        )

        bottom_text = "".join(
            item["text"]
            for item in bottom_segments
        )

        if (
            not top_text
            or
            not bottom_text
        ):
            return []

        top_confidence = (
            sum(
                item["confidence"]
                for item in top_segments
            )
            /
            len(top_segments)
        )

        bottom_confidence = (
            sum(
                item["confidence"]
                for item in bottom_segments
            )
            /
            len(bottom_segments)
        )

        confidence = (
            top_confidence
            +
            bottom_confidence
        ) / 2.0

        return [{

            "text":
                top_text
                +
                bottom_text,

            "confidence":
                float(confidence),

            "method_suffix":
                "horizontal_split"
        }]

    # ======================================================
    # STRUCTURAL SCORE
    # ======================================================

    def structural_score(
        self,
        text
    ):
        """
        Score resemblance to a normal Indian registration.

        General pattern:

            LL DD L... DDDD

        Examples:

            MH12S05035
            MH12SL6163
            MH12ZM6131
            MH12YH5289

        No character correction is performed.
        """

        if not text:
            return 0.0

        text = self.clean_text(
            text
        )

        if not text:
            return 0.0

        # --------------------------------------------------
        # Exact common Indian structure
        # --------------------------------------------------

        exact_pattern = re.compile(
            r"^[A-Z]{2}"
            r"[0-9]{1,2}"
            r"[A-Z]{1,3}"
            r"[0-9]{4}$"
        )

        if exact_pattern.fullmatch(
            text
        ):

            return 1.0

        # --------------------------------------------------
        # Partial structure
        # --------------------------------------------------

        length = len(text)

        if (
            length < 6
            or
            length > 14
        ):
            return 0.0

        score = 0.0

        # --------------------------------------------------
        # State code
        # --------------------------------------------------

        if (
            len(text) >= 2
            and
            text[:2].isalpha()
        ):

            score += 0.30

        # --------------------------------------------------
        # Digits after state code
        # --------------------------------------------------

        if (
            len(text) >= 3
            and
            re.search(
                r"[0-9]",
                text[2:]
            )
        ):

            score += 0.20

        # --------------------------------------------------
        # Letters after numeric section
        # --------------------------------------------------

        if (
            len(text) >= 5
            and
            re.search(
                r"[A-Z]",
                text[3:]
            )
        ):

            score += 0.20

        # --------------------------------------------------
        # Four-digit suffix
        # --------------------------------------------------

        if re.search(
            r"[0-9]{4}$",
            text
        ):

            score += 0.25

        # --------------------------------------------------
        # Reasonable total length
        # --------------------------------------------------

        if 9 <= length <= 11:

            score += 0.15

        return min(
            score,
            0.95
        )

    # ======================================================
    # OCR SCORE
    # ======================================================

    def score_result(
        self,
        text,
        confidence
    ):
        """
        Score OCR candidate.

        Confidence is deliberately significant.

        Strong exact-format candidates receive a bonus.
        Low-confidence candidates are penalized.
        """

        if not text:
            return (
                0.0,
                None
            )

        text = self.clean_text(
            text
        )

        if not text:
            return (
                0.0,
                None
            )

        validation = (
            self.validator.validate(
                text
            )
        )

        validator_score = float(
            validation.get(
                "format_score",
                0.0
            )
        )

        is_valid = bool(
            validation.get(
                "is_valid",
                False
            )
        )

        structure_score = (
            self.structural_score(
                text
            )
        )

        # ==================================================
        # BASE SCORE
        # ==================================================

        score = (

            0.55 * float(
                confidence
            )

            +

            0.25 * validator_score

            +

            0.20 * structure_score
        )

        # ==================================================
        # VALID FORMAT BONUS
        # ==================================================

        if is_valid:

            score += 0.20

        # ==================================================
        # INVALID CANDIDATE PENALTY
        # ==================================================

        else:

            if structure_score < 0.50:

                score *= 0.45

            else:

                score *= 0.70

        # ==================================================
        # LENGTH PENALTY
        # ==================================================

        length = len(text)

        if length < 5:

            score *= 0.20

        elif length < 6:

            score *= 0.35

        elif length < 8:

            score *= 0.70

        # ==================================================
        # LOW CONFIDENCE PENALTY
        # ==================================================

        if confidence < 0.15:

            score *= 0.35

        elif confidence < 0.20:

            score *= 0.50

        elif confidence < 0.30:

            score *= 0.75

        # ==================================================
        # ADD STRUCTURAL SCORE TO VALIDATION
        # ==================================================

        validation = dict(
            validation
        )

        validation[
            "structural_score"
        ] = float(
            structure_score
        )

        return (
            float(score),
            validation
        )

    # ======================================================
    # DEBUG
    # ======================================================

    def debug_candidate(
        self,
        method,
        candidate,
        score,
        validation
    ):
        """
        Print candidate information.
        """

        if not self.debug:
            return

        text = candidate.get(
            "text",
            ""
        )

        confidence = float(
            candidate.get(
                "confidence",
                0.0
            )
        )

        format_score = (
            validation.get(
                "format_score",
                0.0
            )
            if validation
            else 0.0
        )

        structural_score = (
            validation.get(
                "structural_score",
                0.0
            )
            if validation
            else 0.0
        )

        is_valid = (
            validation.get(
                "is_valid",
                False
            )
            if validation
            else False
        )

        # print(
        #     f"OCR [{method}] "
        #     f"-> {text} "
        #     f"(conf={confidence:.3f}, "
        #     f"format={format_score:.3f}, "
        #     f"structure={structural_score:.3f}, "
        #     f"valid={is_valid}, "
        #     f"score={score:.3f})"
        # )

    # ======================================================
    # READ PLATE
    # ======================================================

    def read_plate(
        self,
        plate_image
    ):
        """
        Main OCR entry point.

        Returns:

        {
            "text": ...,
            "confidence": ...,
            "method": ...,
            "score": ...,
            "validation": ...,
            "layout": ...
        }
        """

        if (
            plate_image is None
            or
            plate_image.size == 0
        ):
            return None

        # ==================================================
        # LAYOUT HINT
        # ==================================================

        crop_layout_hint = (
            self.classify_crop_layout(
                plate_image
            )
        )

        # if self.debug:

        #     print(
        #         "\nPlate geometry: "
        #         f"aspect="
        #         f"{self.get_aspect_ratio(plate_image):.2f}, "
        #         f"hint="
        #         f"{crop_layout_hint}"
        #     )

        # ==================================================
        # PREPROCESSING
        # ==================================================

        variants = (
            self.preprocess_variants(
                plate_image
            )
        )

        # ==================================================
        # BEST RESULT
        # ==================================================

        best_result = None
        best_score = -1.0

        # ==================================================
        # PROCESSING ORDER
        # ==================================================

        processing_order = [

            "normalized",

            "original",

            "upscaled",

            "clahe",

            "sharpened",

            "otsu",

            "adaptive"
        ]

        # ==================================================
        # PROCESS VARIANTS
        # ==================================================

        for method in processing_order:

            image = variants.get(
                method
            )

            if image is None:
                continue

            # ------------------------------------------------
            # Run EasyOCR once
            # ------------------------------------------------

            segments = (
                self.get_ocr_segments(
                    image
                )
            )

            if not segments:
                continue

            # ==================================================
            # SINGLE-LINE HYPOTHESIS
            # ==================================================

            single_candidates = (
                self.generate_single_line_candidates(
                    segments
                )
            )

            for candidate in (
                single_candidates
            ):

                candidate[
                    "layout"
                ] = "single_line"

            # ==================================================
            # TWO-LINE HYPOTHESIS
            # ==================================================

            two_line_candidates = (
                self.generate_two_line_candidates(
                    segments
                )
            )

            for candidate in (
                two_line_candidates
            ):

                candidate[
                    "layout"
                ] = "two_line"

            candidates = (
                single_candidates
                +
                two_line_candidates
            )

            # ==================================================
            # HORIZONTAL SPLIT
            # ==================================================

            rows = (
                self.group_segments_into_rows(
                    segments
                )
            )

            should_try_split = (

                crop_layout_hint
                ==
                "two_line"

                or

                len(rows) >= 2
            )

            if should_try_split:

                split_candidates = (
                    self.generate_horizontal_split_candidate(
                        image
                    )
                )

                for candidate in (
                    split_candidates
                ):

                    candidate[
                        "layout"
                    ] = "two_line"

                candidates.extend(
                    split_candidates
                )

            # ==================================================
            # SCORE
            # ==================================================

            for candidate in candidates:

                text = self.clean_text(
                    candidate.get(
                        "text",
                        ""
                    )
                )

                if not text:
                    continue

                confidence = float(
                    candidate.get(
                        "confidence",
                        0.0
                    )
                )

                score, validation = (
                    self.score_result(
                        text,
                        confidence
                    )
                )

                method_suffix = (
                    candidate.get(
                        "method_suffix",
                        "ocr"
                    )
                )

                result_method = (
                    f"{method}_"
                    f"{method_suffix}"
                )

                self.debug_candidate(
                    result_method,
                    candidate,
                    score,
                    validation
                )

                # ------------------------------------------------
                # Keep best
                # ------------------------------------------------

                if score > best_score:

                    best_score = score

                    best_result = {

                        "text":
                            text,

                        "confidence":
                            confidence,

                        "method":
                            result_method,

                        "score":
                            float(
                                best_score
                            ),

                        "validation":
                            validation,

                        "layout":
                            candidate.get(
                                "layout",
                                crop_layout_hint
                            )
                    }

            # ==================================================
            # EARLY STOP
            # ==================================================

            if best_result is not None:

                validation = (
                    best_result[
                        "validation"
                    ]
                )

                if (
                    validation.get(
                        "is_valid",
                        False
                    )
                    and
                    best_result[
                        "confidence"
                    ]
                    >=
                    self.early_stop_confidence
                    and
                    best_result[
                        "score"
                    ]
                    >=
                    self.early_stop_score
                ):

                    # if self.debug:

                    #     print(
                    #         "\nStrong OCR result "
                    #         "found. "
                    #         "Stopping additional "
                    #         "preprocessing."
                    #     )

                    break

        # ==================================================
        # FINAL RESULT
        # ==================================================

        # if self.debug:

        #     print(
        #         "\nFINAL OCR RESULT"
        #     )

        #     print(
        #         best_result
        #     )

        return best_result