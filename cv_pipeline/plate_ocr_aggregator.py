from collections import defaultdict


class PlateOCRAggregator:

    def __init__(self):

        # ----------------------------------
        # OCR observations grouped by track
        # ----------------------------------

        self.observations = defaultdict(list)


    # ==================================================
    # ADD OBSERVATION
    # ==================================================

    def add_observation(
        self,
        track_id,
        ocr_result,
        format_result,
        plate_confidence
    ):

        if ocr_result is None:
            return

        if format_result is None:
            return


        text = ocr_result.get(
            "text"
        )

        if not text:
            return


        normalized_text = format_result.get(
            "text"
        )

        if not normalized_text:
            return


        observation = {

            "text": normalized_text,

            "ocr_confidence": float(
                ocr_result.get(
                    "confidence",
                    0.0
                )
            ),

            "format_score": float(
                format_result.get(
                    "format_score",
                    0.0
                )
            ),

            "is_valid": bool(
                format_result.get(
                    "is_valid",
                    False
                )
            ),

            "plate_confidence": float(
                plate_confidence
            )
        }


        self.observations[
            track_id
        ].append(
            observation
        )


    # ==================================================
    # GET BEST PLATE
    # ==================================================

    def get_best_plate(
        self,
        track_id
    ):

        track_observations = (
            self.observations.get(
                track_id,
                []
            )
        )


        if not track_observations:
            return None


        # ----------------------------------
        # Group identical OCR texts
        # ----------------------------------

        candidates = {}


        for observation in track_observations:

            text = observation[
                "text"
            ]


            if text not in candidates:

                candidates[text] = {

                    "text": text,

                    "count": 0,

                    "ocr_scores": [],

                    "plate_scores": [],

                    "format_scores": [],

                    "valid_count": 0
                }


            candidate = candidates[text]

            candidate["count"] += 1

            candidate[
                "ocr_scores"
            ].append(
                observation[
                    "ocr_confidence"
                ]
            )

            candidate[
                "plate_scores"
            ].append(
                observation[
                    "plate_confidence"
                ]
            )

            candidate[
                "format_scores"
            ].append(
                observation[
                    "format_score"
                ]
            )


            if observation[
                "is_valid"
            ]:

                candidate[
                    "valid_count"
                ] += 1


        # ==================================================
        # CALCULATE SCORES
        # ==================================================

        for candidate in candidates.values():

            # ----------------------------------
            # Average OCR confidence
            # ----------------------------------

            avg_ocr_confidence = (

                sum(
                    candidate[
                        "ocr_scores"
                    ]
                )

                /

                len(
                    candidate[
                        "ocr_scores"
                    ]
                )
            )


            # ----------------------------------
            # Average plate confidence
            # ----------------------------------

            avg_plate_confidence = (

                sum(
                    candidate[
                        "plate_scores"
                    ]
                )

                /

                len(
                    candidate[
                        "plate_scores"
                    ]
                )
            )


            # ----------------------------------
            # Average format score
            # ----------------------------------

            avg_format_score = (

                sum(
                    candidate[
                        "format_scores"
                    ]
                )

                /

                len(
                    candidate[
                        "format_scores"
                    ]
                )
            )


            # ----------------------------------
            # Candidate validity
            # ----------------------------------

            is_valid = (

                candidate[
                    "valid_count"
                ]
                >
                0
            )


            # ----------------------------------
            # Base quality score
            # ----------------------------------

            base_score = (

                0.40
                *
                avg_ocr_confidence

                +

                0.30
                *
                avg_plate_confidence

                +

                0.30
                *
                avg_format_score
            )


            # ----------------------------------
            # Consistency bonus
            #
            # More repeated observations
            # increase confidence.
            #
            # Capped at 0.20.
            # ----------------------------------

            consistency_bonus = min(

                (
                    candidate[
                        "count"
                    ]
                    -
                    1
                )
                *
                0.05,

                0.20
            )


            # ----------------------------------
            # Final score
            # ----------------------------------

            final_score = (

                base_score

                +

                consistency_bonus
            )


            # ----------------------------------
            # Penalize invalid OCR
            # ----------------------------------

            if not is_valid:

                final_score *= 0.50


            # Store calculated values

            candidate[
                "avg_ocr_confidence"
            ] = avg_ocr_confidence


            candidate[
                "avg_plate_confidence"
            ] = avg_plate_confidence


            candidate[
                "avg_format_score"
            ] = avg_format_score


            candidate[
                "is_valid"
            ] = is_valid


            candidate[
                "final_score"
            ] = final_score


        # ==================================================
        # PRIORITIZE VALID PLATES
        # ==================================================

        valid_candidates = [

            candidate

            for candidate in candidates.values()

            if candidate[
                "is_valid"
            ]
        ]


        # ----------------------------------
        # If we have at least one valid plate,
        # INVALID plates cannot win.
        # ----------------------------------

        if valid_candidates:

            best_candidate = max(

                valid_candidates,

                key=lambda candidate: (

                    candidate[
                        "final_score"
                    ],

                    candidate[
                        "count"
                    ]
                )
            )


        # ----------------------------------
        # Otherwise select best available OCR
        # ----------------------------------

        else:

            best_candidate = max(

                candidates.values(),

                key=lambda candidate: (

                    candidate[
                        "final_score"
                    ],

                    candidate[
                        "count"
                    ]
                )
            )


        # ==================================================
        # RETURN RESULT
        # ==================================================

        return {

            "text": best_candidate[
                "text"
            ],

            "ocr_confidence": float(

                best_candidate[
                    "avg_ocr_confidence"
                ]
            ),

            "plate_confidence": float(

                best_candidate[
                    "avg_plate_confidence"
                ]
            ),

            "format_score": float(

                best_candidate[
                    "avg_format_score"
                ]
            ),

            "is_valid": bool(

                best_candidate[
                    "is_valid"
                ]
            ),

            "observations": int(

                best_candidate[
                    "count"
                ]
            ),

            "total_observations": len(
                track_observations
            ),

            "final_score": float(

                best_candidate[
                    "final_score"
                ]
            )
        }


    # ==================================================
    # CLEAR TRACK
    # ==================================================

    def clear_track(
        self,
        track_id
    ):

        """
        Remove observations
        after vehicle exit.
        """

        if track_id in self.observations:

            del self.observations[
                track_id
            ]