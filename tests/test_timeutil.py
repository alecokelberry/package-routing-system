"""Clock formatting and parsing."""

from __future__ import annotations

import unittest

from routing.timeutil import format_time, parse_time


class FormatTimeTests(unittest.TestCase):
    def test_formats_morning_noon_afternoon_and_midnight(self) -> None:
        self.assertEqual(format_time(0), "12:00 AM")
        self.assertEqual(format_time(8), "8:00 AM")
        self.assertEqual(format_time(9 + 5 / 60), "9:05 AM")
        self.assertEqual(format_time(12), "12:00 PM")
        self.assertEqual(format_time(13.5), "1:30 PM")

    def test_rounds_to_the_nearest_minute(self) -> None:
        self.assertEqual(format_time(9 + 59.6 / 60), "10:00 AM")
        self.assertEqual(format_time(9 + 0.4 / 60), "9:00 AM")


class ParseTimeTests(unittest.TestCase):
    def test_accepts_12_and_24_hour_forms(self) -> None:
        cases = {
            "9:05 AM": 9 + 5 / 60,
            "9:05am": 9 + 5 / 60,
            " 10:20 AM ": 10 + 20 / 60,
            "13:05": 13 + 5 / 60,
            "9": 9.0,
            "0:30": 0.5,
            "12:00 AM": 0.0,
            "12:30 PM": 12.5,
            "1 PM": 13.0,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(parse_time(text), expected)

    def test_rejects_text_that_is_not_a_time_of_day(self) -> None:
        for text in ["", "nope", "9:60 AM", "24:00", "13 AM", "0 PM", "9:5", "-1"]:
            with self.subTest(text=text):
                self.assertIsNone(parse_time(text))


if __name__ == "__main__":
    unittest.main()
