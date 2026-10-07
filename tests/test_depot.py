"""Loading the CSVs and checking hand-written truck loads against the notes."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from routing.depot import (
    CORRECTED_ADDRESS,
    MANIFESTS,
    address_index,
    check_manifests,
    load_addresses,
    load_distances,
    load_packages,
    normalize,
)
from routing.package import PackageTable


def loads() -> list[list[int]]:
    return [list(load) for load in MANIFESTS]


def move(all_loads: list[list[int]], package_id: int, to_truck: int) -> None:
    for load in all_loads:
        if package_id in load:
            load.remove(package_id)
    all_loads[to_truck - 1].append(package_id)


class DataFileTests(unittest.TestCase):
    packages: PackageTable

    @classmethod
    def setUpClass(cls) -> None:
        cls.packages = load_packages()

    def test_files_have_the_expected_shape(self) -> None:
        addresses = load_addresses()
        distances = load_distances()
        self.assertEqual(len(self.packages), 40)
        self.assertEqual(len(addresses), 27)
        self.assertEqual(len(distances), len(addresses))

    def test_every_package_address_is_in_the_distance_table(self) -> None:
        index_of = address_index(load_addresses())
        for package in self.packages.values():
            with self.subTest(package=package.package_id):
                index_of(package.address)
        index_of(CORRECTED_ADDRESS)

    def test_notes_set_arrival_and_correction_times(self) -> None:
        delayed = self.packages.lookup(6)
        wrong = self.packages.lookup(9)
        assert delayed is not None and wrong is not None
        self.assertGreater(delayed.hub_arrival_time, 9.0)
        self.assertEqual(wrong.address_at(8.0), "300 State St")
        self.assertEqual(wrong.address_at(11.0), CORRECTED_ADDRESS)


class NormalizeTests(unittest.TestCase):
    def test_matches_spelled_out_directions_and_drops_unit_numbers(self) -> None:
        self.assertEqual(
            normalize("5383 South 900 East #104"), normalize("5383 S 900 E")
        )
        self.assertEqual(normalize("  600 E  900 South "), "600 e 900 s")

    def test_unknown_address_is_an_error(self) -> None:
        index_of = address_index(["HUB", "1 Main St"])
        self.assertEqual(index_of("1 MAIN ST"), 1)
        with self.assertRaises(ValueError):
            index_of("2 Main St")


class LoadDistancesTests(unittest.TestCase):
    def write(self, text: str) -> Path:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "distances.csv"
        path.write_text(text, encoding="utf-8")
        return path

    def test_rejects_a_bad_matrix(self) -> None:
        bad = {
            "ragged": "0,1\n1\n",
            "asymmetric": "0,1\n2,0\n",
            "nonzero diagonal": "1,1\n1,0\n",
        }
        for name, text in bad.items():
            with self.subTest(name), self.assertRaises(ValueError):
                load_distances(self.write(text))


class CheckManifestsTests(unittest.TestCase):
    packages: PackageTable

    @classmethod
    def setUpClass(cls) -> None:
        cls.packages = load_packages()

    def assert_rejected(self, all_loads: list[list[int]], message: str) -> None:
        with self.assertRaisesRegex(ValueError, message):
            check_manifests(all_loads, self.packages)

    def test_shipped_loads_pass(self) -> None:
        check_manifests(loads(), self.packages)

    def test_rejects_a_package_on_two_trucks(self) -> None:
        all_loads = loads()
        all_loads[0].append(all_loads[1][0])
        self.assert_rejected(all_loads, "more than one truck")

    def test_rejects_a_package_left_at_the_hub(self) -> None:
        all_loads = loads()
        all_loads[2].remove(2)
        self.assert_rejected(all_loads, r"not on any truck: \[2\]")

    def test_rejects_a_package_that_does_not_exist(self) -> None:
        all_loads = loads()
        all_loads[2].append(41)
        self.assert_rejected(all_loads, "do not exist")

    def test_rejects_more_than_sixteen_packages(self) -> None:
        all_loads = loads()
        for package_id in [2, 4, 5]:
            move(all_loads, package_id, 2)
        self.assert_rejected(all_loads, "truck 2 carries 17")

    def test_rejects_a_truck_two_package_on_another_truck(self) -> None:
        all_loads = loads()
        move(all_loads, 3, 1)
        self.assert_rejected(all_loads, "package 3 must ride on truck 2")

    def test_rejects_a_delayed_package_on_the_eight_oclock_truck(self) -> None:
        all_loads = loads()
        move(all_loads, 25, 1)
        self.assert_rejected(all_loads, "package 25 is not at the hub")

    def test_rejects_the_wrong_address_package_before_ten_twenty(self) -> None:
        all_loads = loads()
        move(all_loads, 9, 1)
        self.assert_rejected(all_loads, "package 9 needs the 10:20 AM address")

    def test_rejects_splitting_a_group(self) -> None:
        all_loads = loads()
        move(all_loads, 19, 3)
        self.assert_rejected(all_loads, "must travel with 19")


if __name__ == "__main__":
    unittest.main()
