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

        normalized_text = self.normalize(
            text
        )

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

            if pattern.match(
                normalized_text
            ):

                return {

                    "text": normalized_text,

                    "is_valid": True,

                    "format_score": 1.0
                }


        # ----------------------------------
        # Partial / plausible result scoring
        # ----------------------------------

        score = 0.0

        length = len(
            normalized_text
        )

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

            "format_score": float(
                score
            )
        }