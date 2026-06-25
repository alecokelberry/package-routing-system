"""Behavior of the hash table, the clock, and one full delivery day."""

from __future__ import annotations

import unittest

from routing.depot import CORRECTION_TIME, DELAYED_ARRIVAL, run_day
from routing.hash_table import ChainingHashTable
from routing.timeutil import format_time, parse_time


class HashTableTests(unittest.TestCase):
    def test_insert_lookup_replace_and_remove(self) -> None:
        table = ChainingHashTable(initial_capacity=1)
        table.insert(1, "a")
        table.insert(1, "b")
        table.insert(2, "c")
        self.assertEqual(len(table), 2)
        self.assertEqual(table.lookup(1), "b")
        self.assertEqual(table.lookup(2), "c")
        self.assertIsNone(table.lookup(3))
        self.assertTrue(table.remove(1))
        self.assertFalse(table.remove(1))
        self.assertEqual(table.lookup(2), "c")
        self.assertEqual(len(table), 1)

    def test_grows_and_keeps_every_key(self) -> None:
        table = ChainingHashTable(initial_capacity=2)
        for key in range(40):
            table.insert(key, key * 10)
        self.assertGreater(len(table._buckets), 2)
        for key in range(40):
            self.assertEqual(table.lookup(key), key * 10)


class TimeTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        self.assertEqual(format_time(8), "8:00 AM")
        self.assertEqual(format_time(DELAYED_ARRIVAL), "9:05 AM")
        self.assertEqual(format_time(12), "12:00 PM")
        self.assertEqual(format_time(13.5), "1:30 PM")
        self.assertEqual(parse_time("9:05 AM"), DELAYED_ARRIVAL)
        self.assertEqual(parse_time("13:05"), 13 + 5 / 60)
        self.assertIsNone(parse_time("nope"))
        self.assertIsNone(parse_time("9:60 AM"))


class DayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.day = run_day()

    def test_mileage_and_deadlines(self) -> None:
        miles = [round(truck.mileage, 1) for truck in self.day.trucks]
        self.assertEqual(miles, [34.0, 40.0, 33.4])
        self.assertEqual(round(self.day.total_mileage, 1), 107.4)
        self.assertTrue(all(package.on_time() for package in self.day.packages.values()))
        for truck in self.day.trucks:
            self.assertEqual(len(truck.stops), len(truck.package_ids))
            times = [
                self.day.packages.lookup(package_id).delivery_time
                for package_id in truck.stops
            ]
            self.assertEqual(times, sorted(times))

    def test_package_nine_address_changes_at_ten_twenty(self) -> None:
        package = self.day.packages.lookup(9)
        assert package is not None
        self.assertEqual(package.address_at(CORRECTION_TIME - 0.01), "300 State St")
        self.assertEqual(package.address_at(CORRECTION_TIME), "410 S State St")
        self.assertEqual(package.zip_at(CORRECTION_TIME), "84111")
        self.assertIn("Delivered", package.status_at(11))

    def test_delayed_flight_is_not_at_the_hub_at_nine(self) -> None:
        package = self.day.packages.lookup(6)
        assert package is not None
        self.assertIn("Delayed", package.status_at(9))
        self.assertIn("En route", package.status_at(DELAYED_ARRIVAL))

    def test_early_deadline_leaves_at_eight(self) -> None:
        package = self.day.packages.lookup(15)
        assert package is not None
        self.assertEqual(package.truck_id, 1)
        self.assertLessEqual(package.delivery_time or 99, 9.0)
        self.assertIn("At the hub", package.status_at(7.9))


if __name__ == "__main__":
    unittest.main()
