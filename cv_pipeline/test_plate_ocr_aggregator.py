from cv_pipeline.plate_ocr_validator import (
    PlateOCRValidator
)

from cv_pipeline.plate_ocr_aggregator import (
    PlateOCRAggregator
)


def main():

    validator = (
        PlateOCRValidator()
    )

    aggregator = (
        PlateOCRAggregator()
    )


    track_id = 1


    observations = [

        {
            "text": "MH12AB6858",
            "ocr_confidence": 0.72,
            "plate_confidence": 0.85
        },

        {
            "text": "MH12A86858",
            "ocr_confidence": 0.61,
            "plate_confidence": 0.82
        },

        {
            "text": "MH12AB6858",
            "ocr_confidence": 0.89,
            "plate_confidence": 0.91
        },

        {
            "text": "MH12AB6858",
            "ocr_confidence": 0.81,
            "plate_confidence": 0.88
        },

        {
            "text": "05502",
            "ocr_confidence": 0.92,
            "plate_confidence": 0.90
        }
    ]


    print()

    print(
        "=" * 70
    )

    print(
        "PLATE OCR AGGREGATOR TEST"
    )

    print(
        "=" * 70
    )


    for observation in observations:

        format_result = (
            validator.validate(
                observation[
                    "text"
                ]
            )
        )


        aggregator.add_observation(

            track_id=track_id,

            ocr_result={

                "text": observation[
                    "text"
                ],

                "confidence": observation[
                    "ocr_confidence"
                ]
            },

            format_result=format_result,

            plate_confidence=observation[
                "plate_confidence"
            ]
        )


    result = (
        aggregator.get_best_plate(
            track_id
        )
    )


    print()

    print(
        "FINAL AGGREGATED RESULT"
    )

    print(
        "=" * 70
    )

    print(
        result
    )


if __name__ == "__main__":

    main()