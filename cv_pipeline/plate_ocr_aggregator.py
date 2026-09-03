from collections import defaultdict


class PlateOCRAggregator:
    """
    Version 2:
    Position-aware temporal OCR aggregation for Indian license plates.

    The aggregator combines multiple OCR observations belonging to the
    same vehicle track.

    Instead of relying only on complete-string similarity, it performs
    character-level voting according to Indian plate structure.

    Typical private vehicle format:

        MH12ZM6131
        LLDDLLDDDD

    where:
        L = letter
        D = digit

    Supported patterns:

        LLDDLLDDDD
        LLDDLLDDD
        LLDBHDDDDLL
        LLDDLLDDDD  (generic fallback)

    The aggregator DOES NOT blindly perform substitutions such as:

        O -> 0
        I -> 1
        Z -> 2

    because those substitutions are position-dependent.
    """

    def __init__(self):
        self.observations = defaultdict(list)

    # ============================================================
    # PUBLIC API
    # ============================================================

    def add_observation(
        self,
        track_id,
        ocr_result,
        format_result,
        plate_confidence
    ):
        """
        Add one OCR observation for a vehicle track.
        """

        if ocr_result is None:
            return

        if format_result is None:
            return

        text = format_result.get("text", "")

        if not text:
            return

        text = str(text).strip().upper()

        if not text:
            return

        observation = {
            "text": text,

            "ocr_confidence": float(
                ocr_result.get("confidence", 0.0)
            ),

            "format_score": float(
                format_result.get("format_score", 0.0)
            ),

            "is_valid": bool(
                format_result.get("is_valid", False)
            ),

            "plate_confidence": float(
                plate_confidence
            )
        }

        self.observations[track_id].append(
            observation
        )

    # ============================================================
    # BASIC HELPERS
    # ============================================================

    @staticmethod
    def _is_letter(char):
        return char.isalpha()

    @staticmethod
    def _is_digit(char):
        return char.isdigit()

    # ============================================================
    # EXPECTED PLATE PATTERNS
    # ============================================================

    def _get_patterns(self, text):
        """
        Return possible structural patterns for an OCR string.

        The patterns are intentionally conservative.

        LLDDLLDDDD
            Example:
            MH12ZM6131

        LLDDLLDDD
            Example:
            MH12ZM613

        LLDBHDDDDLL
            Bharat series:
            22BH1234AB
        """

        patterns = []

        length = len(text)

        # Standard Indian plate:
        # State (2 letters)
        # District/RTO (1-2 digits)
        # Series (1-3 letters)
        # Number (3-4 digits)
        #
        # For the common 10-character case:
        if length == 10:
            patterns.append(
                "LLDDLLDDDD"
            )

        # Common 9-character case
        if length == 9:
            patterns.append(
                "LLDDLLDDD"
            )

        # Bharat Series:
        # 22BH1234AB
        if length == 10:
            patterns.append(
                "DDBHDDDDLL"
            )

        return patterns

    def _structural_score(self, text, pattern):
        """
        Measure how well a string matches a structural pattern.

        Returns value in [0, 1].
        """

        if len(text) != len(pattern):
            return 0.0

        score = 0.0

        for char, expected in zip(text, pattern):

            if expected == "L":
                if self._is_letter(char):
                    score += 1.0

            elif expected == "D":
                if self._is_digit(char):
                    score += 1.0

            else:
                # Literal character, e.g. B or H
                if char == expected:
                    score += 1.0

        return score / len(pattern)

    def _best_pattern(self, text):
        """
        Find the structural pattern that best describes a string.
        """

        patterns = self._get_patterns(text)

        if not patterns:
            return None, 0.0

        best_pattern = None
        best_score = 0.0

        for pattern in patterns:

            score = self._structural_score(
                text,
                pattern
            )

            if score > best_score:
                best_score = score
                best_pattern = pattern

        return best_pattern, best_score

    # ============================================================
    # NORMALIZE OBSERVATION LENGTH
    # ============================================================

    def _select_target_length(self, cluster):
        """
        Select the most likely plate length.

        Longer, high-confidence observations receive more weight.
        """

        length_scores = defaultdict(float)

        for observation in cluster:

            text = observation["text"]

            weight = (
                0.40
                * observation["ocr_confidence"]
                + 0.30
                * observation["format_score"]
                + 0.30
                * observation["plate_confidence"]
            )

            # Valid observations get additional support.
            if observation["is_valid"]:
                weight *= 1.20

            length_scores[len(text)] += weight

        if not length_scores:
            return None

        return max(
            length_scores,
            key=length_scores.get
        )

    # ============================================================
    # CHARACTER COMPATIBILITY
    # ============================================================

    def _character_vote_weight(
        self,
        observation
    ):
        """
        Calculate the weight of an OCR observation.
        """

        weight = (
            0.40
            * observation["ocr_confidence"]
            + 0.30
            * observation["format_score"]
            + 0.30
            * observation["plate_confidence"]
        )

        if observation["is_valid"]:
            weight *= 1.20

        return weight

    def _compatible_character(
        self,
        char,
        expected
    ):
        """
        Check whether a character is compatible with
        the expected plate position.
        """

        if expected == "L":
            return char.isalpha()

        if expected == "D":
            return char.isdigit()

        return char == expected

    # ============================================================
    # POSITIONAL CHARACTER VOTING
    # ============================================================

    def _character_vote(
        self,
        cluster,
        target_length,
        pattern
    ):
        """
        Vote independently for every character position.

        This is the main improvement over Version 1.
        """

        if not cluster:
            return ""

        result = []

        for position in range(target_length):

            votes = defaultdict(float)

            expected_type = pattern[position]

            for observation in cluster:

                text = observation["text"]

                if position >= len(text):
                    continue

                char = text[position]

                weight = self._character_vote_weight(
                    observation
                )

                # ------------------------------------------------
                # Structural compatibility
                # ------------------------------------------------

                if self._compatible_character(
                    char,
                    expected_type
                ):
                    votes[char] += weight

                else:
                    # OCR character does not match the expected
                    # type. We don't completely discard it because
                    # OCR can confuse letters and digits.
                    votes[char] += (
                        weight * 0.10
                    )

            if not votes:
                continue

            best_char = max(
                votes,
                key=votes.get
            )

            result.append(best_char)

        return "".join(result)

    # ============================================================
    # STRUCTURE-AWARE CHARACTER CORRECTION
    # ============================================================

    def _correct_character_for_position(
        self,
        char,
        expected
    ):
        """
        Apply ONLY position-aware OCR corrections.

        These are deliberately conservative.

        Letter positions:
            0 -> O
            1 -> I
            5 -> S

        Digit positions:
            O -> 0
            I -> 1
            Z -> 2
            S -> 5
            B -> 8
            G -> 6

        This function is NOT used blindly across the plate.
        """

        if expected == "D":

            replacements = {
                "O": "0",
                "I": "1",
                "Z": "2",
                "S": "5",
                "B": "8",
                "G": "6",
                "Q": "0"
            }

            return replacements.get(
                char,
                char
            )

        if expected == "L":

            replacements = {
                "0": "O",
                "1": "I",
                "2": "Z",
                "5": "S",
                "8": "B",
                "6": "G"
            }

            return replacements.get(
                char,
                char
            )

        return char

    def _apply_position_correction(
        self,
        text,
        pattern
    ):
        """
        Apply positional OCR correction.
        """

        if not text:
            return ""

        corrected = []

        for index, char in enumerate(text):

            if index >= len(pattern):
                corrected.append(char)
                continue

            expected = pattern[index]

            corrected.append(
                self._correct_character_for_position(
                    char,
                    expected
                )
            )

        return "".join(corrected)

    # ============================================================
    # CLUSTER OBSERVATIONS
    # ============================================================

    def _cluster_observations(self, observations):
        """
        Group observations using plate-aware compatibility.

        Unlike Version 1, this does not require the complete
        strings to have high Levenshtein similarity.

        Observations are compared position-by-position.
        """

        clusters = []

        for observation in observations:

            text = observation["text"]

            best_cluster = None
            best_score = 0.0

            for cluster in clusters:

                score = self._observation_cluster_similarity(
                    observation,
                    cluster
                )

                if score > best_score:
                    best_score = score
                    best_cluster = cluster

            # ----------------------------------------------------
            # Accept reasonably compatible observations
            # ----------------------------------------------------

            if (
                best_cluster is not None
                and best_score >= 0.50
            ):
                best_cluster.append(
                    observation
                )

            else:
                clusters.append(
                    [observation]
                )

        return clusters

    def _observation_cluster_similarity(
        self,
        observation,
        cluster
    ):
        """
        Position-aware similarity between an observation
        and an existing cluster.

        Instead of asking:

            "Are the strings globally similar?"

        we ask:

            "Do the characters mostly agree at their positions?"
        """

        text = observation["text"]

        if not cluster:
            return 0.0

        # Compare with the strongest observation in the cluster.
        best_score = 0.0

        for existing in cluster:

            other = existing["text"]

            max_length = max(
                len(text),
                len(other)
            )

            if max_length == 0:
                continue

            matches = 0
            comparisons = 0

            for index in range(
                min(len(text), len(other))
            ):

                a = text[index]
                b = other[index]

                comparisons += 1

                if a == b:
                    matches += 1

                else:
                    # Allow common OCR confusion.
                    if self._characters_compatible(
                        a,
                        b
                    ):
                        matches += 0.5

            if comparisons == 0:
                continue

            positional_score = (
                matches / comparisons
            )

            length_score = (
                min(len(text), len(other))
                / max_length
            )

            score = (
                0.80 * positional_score
                + 0.20 * length_score
            )

            best_score = max(
                best_score,
                score
            )

        return best_score

    @staticmethod
    def _characters_compatible(a, b):
        """
        Common OCR confusion pairs.
        """

        confusion_pairs = {
            frozenset(("0", "O")),
            frozenset(("1", "I")),
            frozenset(("2", "Z")),
            frozenset(("5", "S")),
            frozenset(("8", "B")),
            frozenset(("6", "G")),
            frozenset(("7", "T")),
            frozenset(("4", "A")),
            frozenset(("3", "B")),
            frozenset(("9", "G"))
        }

        return frozenset((a, b)) in confusion_pairs

    # ============================================================
    # CLUSTER SCORING
    # ============================================================

    def _score_cluster(self, cluster):
        """
        Score one plate candidate cluster.
        """

        if not cluster:
            return None

        target_length = self._select_target_length(
            cluster
        )

        if target_length is None:
            return None

        # --------------------------------------------------------
        # Determine structural pattern
        # --------------------------------------------------------

        pattern_candidates = []

        for observation in cluster:

            text = observation["text"]

            if len(text) != target_length:
                continue

            pattern, score = self._best_pattern(
                text
            )

            if pattern is not None:

                weight = (
                    self._character_vote_weight(
                        observation
                    )
                )

                pattern_candidates.append(
                    (
                        pattern,
                        score * weight
                    )
                )

        # --------------------------------------------------------
        # Select strongest pattern
        # --------------------------------------------------------

        if pattern_candidates:

            pattern_scores = defaultdict(float)

            for pattern, score in pattern_candidates:
                pattern_scores[pattern] += score

            pattern = max(
                pattern_scores,
                key=pattern_scores.get
            )

        else:

            # Generic fallback.
            if target_length == 10:
                pattern = "LLDDLLDDDD"

            elif target_length == 9:
                pattern = "LLDDLLDDD"

            else:
                # Cannot safely infer structure.
                return None

        # --------------------------------------------------------
        # Character voting
        # --------------------------------------------------------

        voted_text = self._character_vote(
            cluster,
            target_length,
            pattern
        )

        if not voted_text:
            return None

        # --------------------------------------------------------
        # Position-aware correction
        # --------------------------------------------------------

        corrected_text = self._apply_position_correction(
            voted_text,
            pattern
        )

        # --------------------------------------------------------
        # Recalculate structural quality
        # --------------------------------------------------------

        structural_score = self._structural_score(
            corrected_text,
            pattern
        )

        # --------------------------------------------------------
        # Weighted averages
        # --------------------------------------------------------

        total_weight = 0.0

        weighted_ocr = 0.0
        weighted_plate = 0.0
        weighted_format = 0.0

        valid_count = 0

        for observation in cluster:

            weight = self._character_vote_weight(
                observation
            )

            total_weight += weight

            weighted_ocr += (
                observation["ocr_confidence"]
                * weight
            )

            weighted_plate += (
                observation["plate_confidence"]
                * weight
            )

            weighted_format += (
                observation["format_score"]
                * weight
            )

            if observation["is_valid"]:
                valid_count += 1

        if total_weight > 0:

            avg_ocr = (
                weighted_ocr
                / total_weight
            )

            avg_plate = (
                weighted_plate
                / total_weight
            )

            avg_format = (
                weighted_format
                / total_weight
            )

        else:

            avg_ocr = 0.0
            avg_plate = 0.0
            avg_format = 0.0

        # --------------------------------------------------------
        # Base score
        # --------------------------------------------------------

        score = (
            0.35 * avg_ocr
            + 0.25 * avg_plate
            + 0.20 * avg_format
            + 0.20 * structural_score
        )

        # --------------------------------------------------------
        # Temporal consistency
        # --------------------------------------------------------

        observation_count = len(cluster)

        consistency_bonus = min(
            (observation_count - 1) * 0.05,
            0.25
        )

        score += consistency_bonus

        # --------------------------------------------------------
        # Validity
        # --------------------------------------------------------

        is_valid = (
            valid_count > 0
            and structural_score >= 0.80
        )

        if is_valid:
            score += 0.15

        else:
            score *= 0.60

        # --------------------------------------------------------
        # Length penalty
        # --------------------------------------------------------

        if len(corrected_text) < 6:
            score *= 0.50

        elif len(corrected_text) < 8:
            score *= 0.80

        # --------------------------------------------------------
        # Clamp
        # --------------------------------------------------------

        score = max(
            0.0,
            min(score, 1.0)
        )

        return {
            "text": corrected_text,
            "ocr_confidence": float(avg_ocr),
            "plate_confidence": float(avg_plate),
            "format_score": float(avg_format),
            "is_valid": bool(is_valid),
            "observations": observation_count,
            "structural_score": float(
                structural_score
            ),
            "final_score": float(score)
        }

    # ============================================================
    # BEST PLATE
    # ============================================================

    def get_best_plate(self, track_id):
        """
        Return the best aggregated plate for a vehicle track.
        """

        observations = self.observations.get(
            track_id,
            []
        )

        if not observations:
            return None

        # --------------------------------------------------------
        # Cluster
        # --------------------------------------------------------

        clusters = self._cluster_observations(
            observations
        )

        if not clusters:
            return None

        # --------------------------------------------------------
        # Score clusters
        # --------------------------------------------------------

        candidates = []

        for cluster in clusters:

            candidate = self._score_cluster(
                cluster
            )

            if candidate is not None:

                candidates.append(
                    candidate
                )

        if not candidates:
            return None

        # --------------------------------------------------------
        # Prefer valid candidates
        # --------------------------------------------------------

        valid_candidates = [
            candidate
            for candidate in candidates
            if candidate["is_valid"]
        ]

        if valid_candidates:

            candidates = valid_candidates

        # --------------------------------------------------------
        # Select best candidate
        # --------------------------------------------------------

        best = max(
            candidates,
            key=lambda candidate: (
                candidate["final_score"],
                candidate["observations"]
            )
        )

        # --------------------------------------------------------
        # Total observations
        # --------------------------------------------------------

        best["total_observations"] = len(
            observations
        )

        return best

    # ============================================================
    # CLEAR TRACK
    # ============================================================

    def clear_track(self, track_id):
        """
        Remove all OCR observations for a vehicle.
        """

        if track_id in self.observations:
            del self.observations[track_id]