import re


class PlateOCRValidator:

    def __init__(self):

        # ----------------------------------
        # Common Indian license plate patterns
        # ----------------------------------

        self.patterns = [

            # Standard:
            # MH12AB1234
            re.compile(
                r"^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$"
            ),

            # BH series:
            # 21BH1234AA
            re.compile(
                r"^[0-9]{2}BH[0-9]{4}[A-Z]{2}$"
            ),

            # Some OCR may capture:
            # MH12A1234
            re.compile(
                r"^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{3,4}$"
            )
        ]


    def normalize(self, text):

        """
        Normalize OCR output.

        Example:

        'MH 12 AB 6858'
            ↓
        'MH12AB6858'
        """

        if not text:
            return ""

        text = text.upper()

        # Keep only letters and numbers
        text = re.sub(
            r"[^A-Z0-9]",
            "",
            text
        )

        return text


    def validate(self, text):

        """
        Validate OCR text.

        Returns:

        {
            "text": normalized_text,
            "is_valid": bool,
            "format_score": float
        }
        """

        normalized_text = self.normalize(text)

        # ----------------------------------
        # Empty result
        # ----------------------------------

        if not normalized_text:

            return {
                "text": "",
                "is_valid": False,
                "format_score": 0.0
            }


        # ----------------------------------
        # Exact pattern match
        # ----------------------------------

        for pattern in self.patterns:

            if pattern.match(normalized_text):

                return {
                    "text": normalized_text,
                    "is_valid": True,
                    "format_score": 1.0
                }


        # ----------------------------------
        # Partial / plausible result scoring
        # ----------------------------------

        score = 0.0

        length = len(normalized_text)

        # Indian plates are generally
        # around 8–12 characters

        if 8 <= length <= 12:

            score += 0.30

        elif 6 <= length <= 14:

            score += 0.15


        # Starts with two letters

        if (
            len(normalized_text) >= 2
            and
            normalized_text[:2].isalpha()
        ):

            score += 0.25


        # Contains numbers

        if any(
            char.isdigit()
            for char in normalized_text
        ):

            score += 0.15


        # Contains letters

        if any(
            char.isalpha()
            for char in normalized_text
        ):

            score += 0.15


        # Ends with digits
        # Very common for Indian plates

        if (
            len(normalized_text) >= 3
            and
            normalized_text[-3:].isdigit()
        ):

            score += 0.15


        score = min(
            score,
            0.95
        )


        return {
            "text": normalized_text,
            "is_valid": False,
            "format_score": float(score)
        }


    def is_usable(
        self,
        ocr_result,
        validation_result
    ):

        """
        Decide whether an OCR observation is
        good enough to enter temporal aggregation.

        This is intentionally separate from
        validate().

        validate()
            -> plate format quality

        is_usable()
            -> OCR observation quality
        """

        if not ocr_result:
            return False

        if not validation_result:
            return False


        text = validation_result.get(
            "text",
            ""
        )

        if not text:
            return False


        # ----------------------------------
        # Basic length filter
        # ----------------------------------

        # Single characters such as:
        #
        # U
        # 6
        # 7
        # C
        #
        # are almost certainly OCR failures.

        if len(text) < 4:
            return False


        # ----------------------------------
        # OCR confidence
        # ----------------------------------

        ocr_confidence = float(
            ocr_result.get(
                "confidence",
                0.0
            )
        )

        # Extremely low-confidence OCR should
        # not pollute temporal aggregation.

        if ocr_confidence < 0.10:
            return False


        # ----------------------------------
        # Format score
        # ----------------------------------

        format_score = float(
            validation_result.get(
                "format_score",
                0.0
            )
        )


        # ----------------------------------
        # Strong valid plate
        # ----------------------------------

        if validation_result.get(
            "is_valid",
            False
        ):

            return True


        # ----------------------------------
        # Partial plate
        # ----------------------------------

        # For an incomplete/noisy reading we
        # require stronger evidence.

        if format_score < 0.40:
            return False


        # ----------------------------------
        # Character composition
        # ----------------------------------

        has_letters = any(
            char.isalpha()
            for char in text
        )

        has_digits = any(
            char.isdigit()
            for char in text
        )

        # A useful plate observation should
        # normally contain both letters and digits.

        if not has_letters or not has_digits:
            return False


        # ----------------------------------
        # Minimum length for partial reading
        # ----------------------------------

        if len(text) < 6:
            return False


        return True