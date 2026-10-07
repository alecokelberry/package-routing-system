"""Nearest-neighbor routing on a small, hand-checkable map."""

from __future__ import annotations

import unittest

from routing.package import Package, PackageTable
from routing.truck import AVERAGE_SPEED_MPH, Truck

# Four stops on a straight road: hub at mile 0, then A at 1, B at 3, C at 6.
ADDRESSES = ["HUB", "A St", "B St", "C St"]
MILE_MARKERS = [0.0, 1.0, 3.0, 6.0]
DISTANCES = [[abs(a - b) for b in MILE_MARKERS] for a in MILE_MARKERS]


def index_of(address: str) -> int:
    return ADDRESSES.index(address)


def make_packages(*addresses: str) -> PackageTable:
    table = PackageTable()
    for package_id, address in enumerate(addresses, start=1):
        table.insert(
            package_id,
            Package(package_id, address, "City", "UT", "84000", "EOD", 1, ""),
        )
    return table


class TruckTests(unittest.TestCase):
    def test_visits_the_closest_stop_first_and_drives_home(self) -> None:
        packages = make_packages("C St", "A St", "B St")
        truck = Truck(1, [1, 2, 3], departure_time=8.0)

        back = truck.deliver(packages, DISTANCES, index_of)

        self.assertEqual(truck.stops, [2, 3, 1])
        self.assertEqual(truck.mileage, 12.0)  # 1 + 2 + 3 out, 6 back
        self.assertAlmostEqual(back, 8.0 + 12.0 / AVERAGE_SPEED_MPH)
        self.assertEqual(truck.return_time, back)
        delivered = packages.lookup(1)
        assert delivered is not None
        self.assertAlmostEqual(delivered.delivery_time or 0, 8.0 + 6.0 / 18.0)
        self.assertEqual(delivered.truck_id, 1)
        self.assertEqual(delivered.departure_time, 8.0)

    def test_packages_at_the_same_address_are_delivered_together(self) -> None:
        packages = make_packages("B St", "B St")
        truck = Truck(1, [1, 2], departure_time=8.0)
        truck.deliver(packages, DISTANCES, index_of)
        first, second = packages.lookup(1), packages.lookup(2)
        assert first is not None and second is not None
        self.assertEqual(first.delivery_time, second.delivery_time)
        self.assertEqual(truck.mileage, 6.0)

    def test_ties_go_to_manifest_order(self) -> None:
        packages = make_packages("A St", "A St")
        truck = Truck(1, [2, 1], departure_time=8.0)
        truck.deliver(packages, DISTANCES, index_of)
        self.assertEqual(truck.stops, [2, 1])

    def test_a_corrected_address_is_used_once_it_is_known(self) -> None:
        packages = make_packages("A St", "C St")
        corrected = packages.lookup(2)
        assert corrected is not None
        corrected.corrected_address = "B St"
        corrected.correction_time = 8.0

        truck = Truck(1, [1, 2], departure_time=8.0)
        truck.deliver(packages, DISTANCES, index_of)

        self.assertEqual(truck.mileage, 6.0)  # hub -> A -> B -> hub

    def test_an_empty_truck_drives_nowhere(self) -> None:
        truck = Truck(1, [], departure_time=9.0)
        self.assertEqual(truck.deliver(make_packages(), DISTANCES, index_of), 9.0)
        self.assertEqual(truck.mileage, 0.0)

    def test_needs_a_departure_time(self) -> None:
        with self.assertRaises(RuntimeError):
            Truck(1, [1], departure_time=None).deliver(
                make_packages("A St"), DISTANCES, index_of
            )

    def test_unknown_package_id_is_an_error(self) -> None:
        with self.assertRaises(KeyError):
            Truck(1, [99], departure_time=8.0).deliver(
                make_packages("A St"), DISTANCES, index_of
            )


if __name__ == "__main__":
    unittest.main()
