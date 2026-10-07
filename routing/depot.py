"""Load the day's packages and run the three trucks.

Two drivers and three trucks. Trucks 1 and 2 leave in the morning. The first
driver back takes truck 3, and not before the corrected address for package 9
is known. Each truck holds at most 16 packages and drives at 18 mph.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from routing.hash_table import ChainingHashTable
from routing.package import Package
from routing.truck import Truck

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Package 9 is on file at the wrong street until 10:20 AM.
CORRECTION_TIME = 10.0 + 20.0 / 60.0
CORRECTED_ADDRESS = "410 S State St"
CORRECTED_ZIP = "84111"
DELAYED_ARRIVAL = 9.0 + 5.0 / 60.0
TRUCK_CAPACITY = 16

# Loads are written by hand. check_manifests() rejects a list that breaks
# a note on the package file.
TRUCK1_PACKAGES = [1, 13, 14, 15, 16, 19, 20, 29, 30, 31, 34, 37, 40]
TRUCK2_PACKAGES = [3, 6, 11, 12, 17, 18, 23, 25, 26, 28, 32, 35, 36, 38]
TRUCK3_PACKAGES = [2, 4, 5, 7, 8, 9, 10, 21, 22, 24, 27, 33, 39]


@dataclass
class Day:
    """A finished simulation: the package index and the three trucks."""

    packages: ChainingHashTable
    trucks: list[Truck]

    @property
    def total_mileage(self) -> float:
        return sum(truck.mileage for truck in self.trucks)


def normalize(address: str) -> str:
    """Make a street string comparable across the package file and the distance table."""
    text = address.lower().split("#")[0]
    text = re.sub(r"\b(south)\b", "s", text)
    text = re.sub(r"\b(north)\b", "n", text)
    text = re.sub(r"\b(east)\b", "e", text)
    text = re.sub(r"\b(west)\b", "w", text)
    return re.sub(r"\s+", " ", text).strip()


def load_addresses(path: Path | None = None) -> list[str]:
    """Street column, in distance-matrix order. Index 0 is the hub."""
    addresses: list[str] = []
    with (path or DATA_DIR / "addresses.csv").open(newline="") as handle:
        reader = csv.reader(handle)
        next(reader)
        for row in reader:
            addresses.append(row[2])
    return addresses


def load_distances(path: Path | None = None) -> list[list[float]]:
    """Full mileage matrix. Row i, column j is the miles from i to j."""
    matrix: list[list[float]] = []
    with (path or DATA_DIR / "distances.csv").open(newline="") as handle:
        for row in csv.reader(handle):
            matrix.append([float(cell) for cell in row])
    return matrix


def address_index(addresses: list[str]):
    """Return a function from street text to a distance-matrix index."""
    normalized = [normalize(address) for address in addresses]

    def index_of(address: str) -> int:
        target = normalize(address)
        for i, candidate in enumerate(normalized):
            if candidate == target:
                return i
        raise ValueError(f"address not in the distance table: {address}")

    return index_of


def load_packages(path: Path | None = None) -> ChainingHashTable:
    """Insert every package from the CSV into a chaining hash table."""
    packages: ChainingHashTable = ChainingHashTable()
    with (path or DATA_DIR / "packages.csv").open(newline="") as handle:
        reader = csv.reader(handle)
        next(reader)
        for row in reader:
            package = Package(
                int(row[0]),
                row[1],
                row[2],
                row[3],
                row[4],
                row[5],
                int(row[6]),
                row[7],
            )
            if "Delayed on flight" in package.notes:
                package.hub_arrival_time = DELAYED_ARRIVAL
            if "Wrong address" in package.notes:
                package.correction_time = CORRECTION_TIME
                package.corrected_address = CORRECTED_ADDRESS
                package.corrected_zip = CORRECTED_ZIP
            packages.insert(package.package_id, package)
    return packages


def manifests() -> list[list[int]]:
    return [list(TRUCK1_PACKAGES), list(TRUCK2_PACKAGES), list(TRUCK3_PACKAGES)]


def check_manifests(packages: ChainingHashTable) -> None:
    """Raise if a manifest breaks a note from the package file."""
    loads = manifests()
    flat = [package_id for load in loads for package_id in load]
    if len(flat) != len(set(flat)) or len(flat) != len(packages):
        raise ValueError("manifests must contain each package once")
    for load in loads:
        if len(load) > TRUCK_CAPACITY:
            raise ValueError("a truck is over capacity")

    def truck_of(package_id: int) -> int:
        for number, load in enumerate(loads, start=1):
            if package_id in load:
                return number
        raise KeyError(package_id)

    for package in packages.values():
        truck_number = truck_of(package.package_id)
        notes = package.notes.lower()
        if "can only be on truck 2" in notes and truck_number != 2:
            raise ValueError(f"package {package.package_id} must ride on truck 2")
        if "delayed on flight" in notes and truck_number == 1:
            raise ValueError(
                f"package {package.package_id} is not at the hub at 8:00 AM"
            )
        if "wrong address" in notes and truck_number != 3:
            raise ValueError(f"package {package.package_id} needs the 10:20 AM address")
        if "must be delivered with" in notes:
            partners = [int(token) for token in re.findall(r"\d+", package.notes)]
            for partner in partners:
                if truck_of(partner) != truck_number:
                    raise ValueError(
                        f"package {package.package_id} must travel with {partner}"
                    )


def run_day() -> Day:
    """Simulate the day once. Status queries then replay the saved timestamps."""
    addresses = load_addresses()
    distances = load_distances()
    index_of = address_index(addresses)
    packages = load_packages()
    check_manifests(packages)

    truck1 = Truck(1, TRUCK1_PACKAGES, 8.0)
    truck2 = Truck(2, TRUCK2_PACKAGES, DELAYED_ARRIVAL)
    truck3 = Truck(3, TRUCK3_PACKAGES, None)
    truck1.deliver(packages, distances, index_of)
    truck2.deliver(packages, distances, index_of)
    first_driver_back = min(truck1.return_time or 0, truck2.return_time or 0)
    truck3.departure_time = max(first_driver_back, CORRECTION_TIME)
    truck3.deliver(packages, distances, index_of)
    return Day(packages, [truck1, truck2, truck3])
