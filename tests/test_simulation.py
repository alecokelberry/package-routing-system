"""One full delivery day: mileage, deadlines, and the day's special cases."""

from __future__ import annotations

import unittest

from routing.depot import (
    CORRECTION_TIME,
    DAY_START,
    DELAYED_ARRIVAL,
    TRUCK_CAPACITY,
    Day,
    run_day,
)
from routing.package import Package


class DayTests(unittest.TestCase):
    day: Day

    @classmethod
    def setUpClass(cls) -> None:
        cls.day = run_day()

    def package(self, package_id: int) -> Package:
        package = self.day.packages.lookup(package_id)
        assert package is not None
        return package

    def test_mileage_matches_the_published_result(self) -> None:
        miles = [round(truck.mileage, 1) for truck in self.day.trucks]
        self.assertEqual(miles, [34.0, 40.0, 33.4])
        self.assertEqual(round(self.day.total_mileage, 1), 107.4)

    def test_every_package_is_delivered_once_and_on_time(self) -> None:
        stops = [stop for truck in self.day.trucks for stop in truck.stops]
        self.assertEqual(sorted(stops), list(range(1, 41)))
        late = [p.package_id for p in self.day.packages.values() if not p.on_time()]
        self.assertEqual(late, [])

    def test_each_truck_runs_forward_in_time_within_capacity(self) -> None:
        for truck in self.day.trucks:
            with self.subTest(truck=truck.truck_id):
                self.assertLessEqual(len(truck.package_ids), TRUCK_CAPACITY)
                times = [self.package(i).delivery_time or 0 for i in truck.stops]
                self.assertEqual(times, sorted(times))
                self.assertGreaterEqual(times[0], truck.departure_time or 0)
                self.assertGreaterEqual(truck.return_time or 0, times[-1])

    def test_truck_three_waits_for_a_driver_and_the_corrected_address(self) -> None:
        truck1, truck2, truck3 = self.day.trucks
        self.assertEqual(truck1.departure_time, DAY_START)
        self.assertEqual(truck2.departure_time, DELAYED_ARRIVAL)
        first_back = min(truck1.return_time or 0, truck2.return_time or 0)
        self.assertEqual(truck3.departure_time, max(first_back, CORRECTION_TIME))

    def test_package_nine_address_changes_at_ten_twenty(self) -> None:
        package = self.package(9)
        self.assertEqual(package.address_at(CORRECTION_TIME - 0.01), "300 State St")
        self.assertEqual(package.address_at(CORRECTION_TIME), "410 S State St")
        self.assertEqual(package.zip_at(CORRECTION_TIME), "84111")
        self.assertEqual(package.truck_id, 3)
        self.assertGreaterEqual(package.delivery_time or 0, CORRECTION_TIME)

    def test_status_moves_from_hub_to_truck_to_delivered(self) -> None:
        package = self.package(15)
        delivered = package.delivery_time or 0
        self.assertEqual(package.truck_id, 1)
        self.assertLessEqual(delivered, 9.0)
        self.assertEqual(package.status_at(7.9), "At the hub")
        self.assertIn("En route on truck 1", package.status_at(DAY_START))
        self.assertIn("Delivered", package.status_at(delivered))

    def test_delayed_package_reports_its_flight(self) -> None:
        package = self.package(6)
        self.assertIn("Delayed", package.status_at(9.0))
        self.assertIn("En route on truck 2", package.status_at(DELAYED_ARRIVAL))


if __name__ == "__main__":
    unittest.main()
