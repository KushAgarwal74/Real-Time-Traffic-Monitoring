from cv_pipeline.plate_ocr_validator import (
    PlateOCRValidator
)


def main():

    validator = (
        PlateOCRValidator()
    )

    test_cases = [

        "MH12AB6858",

        "MH 12 AB 6858",

        "DL01CA1234",

        "21BH1234AA",

        "05502",

        "MHTZN",

        "MH1ZTH1062",

        "6MH12S05035",

        "6059",

        "",
    ]


    print()

    print(
        "=" * 65
    )

    print(
        "LICENSE PLATE OCR VALIDATOR TEST"
    )

    print(
        "=" * 65
    )


    for text in test_cases:

        result = validator.validate(
            text
        )

        print()

        print(
            f"Input: {text}"
        )

        print(
            f"Normalized: "
            f"{result['text']}"
        )

        print(
            f"Valid: "
            f"{result['is_valid']}"
        )

        print(
            f"Format Score: "
            f"{result['format_score']:.2f}"
        )


if __name__ == "__main__":

    main()