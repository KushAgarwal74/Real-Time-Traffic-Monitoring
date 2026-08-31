import unittest
from datetime import datetime, timezone

from config.db_config import classify_congestion, floor_to_minute


class TrafficSummaryTests(unittest.TestCase):
    def test_floor_to_minute_rounds_down_to_minute(self):
        dt = datetime(2026, 8, 31, 18, 5, 11, 250000, tzinfo=timezone.utc)
        self.assertEqual(
            floor_to_minute(dt),
            datetime(2026, 8, 31, 18, 5, 0, 0, tzinfo=timezone.utc),
        )

    def test_congestion_level_thresholds(self):
        self.assertEqual(classify_congestion(8), "low")
        self.assertEqual(classify_congestion(18), "medium")
        self.assertEqual(classify_congestion(35), "high")


if __name__ == "__main__":
    unittest.main()
