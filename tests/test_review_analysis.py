import copy
import json
import unittest
from unittest.mock import patch

import pandas as pd

from src.review_analysis import analyze_reviews


class ReviewAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.reviews = pd.DataFrame([
            {
                "review_id": "REV-001",
                "rating": 2,
                "review_text": "杯盖漏水。",
            },
            {
                "review_id": "REV-002",
                "rating": 4,
                "review_text": "使用方便，目前没有发现漏水。",
            },
        ])
        self.valid_result = {
            "items": [
                {"review_id": "REV-001", "sentiment": "负面"},
                {"review_id": "REV-002", "sentiment": "正面"},
            ],
            "observations": [
                {
                    "text": "两位用户的漏水体验不同，建议进一步核查。",
                    "review_ids": ["REV-001", "REV-002"],
                }
            ],
        }

    def analyze_mock_result(self, result):
        with patch(
            "src.review_analysis.ask_local_ai",
            return_value=json.dumps(result, ensure_ascii=False),
        ):
            return analyze_reviews(self.reviews)

    def test_valid_result(self):
        result = self.analyze_mock_result(self.valid_result)
        self.assertEqual(
            result["labels"],
            {"REV-001": "负面", "REV-002": "正面"},
        )
        self.assertEqual(
            result["observations"],
            self.valid_result["observations"],
        )

    def test_missing_or_duplicate_ids_are_rejected(self):
        for ids in [
            ["REV-001"],
            ["REV-001", "REV-001"],
            ["REV-001", "REV-999"],
        ]:
            with self.subTest(ids=ids):
                result = copy.deepcopy(self.valid_result)
                result["items"] = [
                    {"review_id": review_id, "sentiment": "负面"}
                    for review_id in ids
                ]
                with self.assertRaises(RuntimeError):
                    self.analyze_mock_result(result)

    def test_unknown_reference_is_rejected(self):
        result = copy.deepcopy(self.valid_result)
        result["observations"][0]["review_ids"] = ["REV-999"]
        with self.assertRaises(RuntimeError):
            self.analyze_mock_result(result)

    def test_invalid_json_is_rejected(self):
        with patch(
            "src.review_analysis.ask_local_ai",
            return_value="这不是 JSON",
        ):
            with self.assertRaises(RuntimeError):
                analyze_reviews(self.reviews)


if __name__ == "__main__":
    unittest.main()