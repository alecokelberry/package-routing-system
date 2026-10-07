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

from routing.package import Package, PackageTable
from routing.truck import AddressIndex, Truck

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

DAY_START = 8.0
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
MANIFESTS = (TRUCK1_PACKAGES, TRUCK2_PACKAGES, TRUCK3_PACKAGES)

_DIRECTIONS = {"north": "n", "south": "s", "east": "e", "west": "w"}


@dataclass
class Day:
    """A finished simulation: the package index and the three trucks."""

    packages: PackageTable
    trucks: list[Truck]

    @property
    def total_mileage(self) -> float:
        return sum(truck.mileage for truck in self.trucks)


def normalize(address: str) -> str:
    """Make street text comparable between the package file and distance table."""
    text = address.lower().split("#")[0]
    for word, letter in _DIRECTIONS.items():
        text = re.sub(rf"\b{word}\b", letter, text)
    return re.sub(r"\s+", " ", text).strip()


def load_addresses(path: Path | None = None) -> list[str]:
    """Street column, in distance-matrix order. Index 0 is the hub."""
    with (path or DATA_DIR / "addresses.csv").open(newline="") as handle:
        reader = csv.reader(handle)
        next(reader)
        return [row[2] for row in reader]


def load_distances(path: Path | None = None) -> list[list[float]]:
    """Full mileage matrix. Row i, column j is the miles from i to j."""
    with (path or DATA_DIR / "distances.csv").open(newline="") as handle:
        matrix = [[float(cell) for cell in row] for row in csv.reader(handle)]
    size = len(matrix)
    if any(len(row) != size for row in matrix):
        raise ValueError("distance table must be square")
    for i in range(size):
        if matrix[i][i] != 0:
            raise ValueError(f"distance table row {i} is not zero on the diagonal")
        for j in range(i):
            if matrix[i][j] != matrix[j][i]:
                raise ValueError(f"distance table is not symmetric at ({i}, {j})")
    return matrix


def address_index(addresses: list[str]) -> AddressIndex:
    """Return a function from street text to a distance-matrix index."""
    rows: dict[str, int] = {}
    for i, address in enumerate(addresses):
        key = normalize(address)
        if key in rows:
            raise ValueError(f"address listed twice in the distance table: {address}")
        rows[key] = i

    def index_of(address: str) -> int:
        try:
            return rows[normalize(address)]
        except KeyError:
            raise ValueError(f"address not in the distance table: {address}") from None

    return index_of


def load_packages(path: Path | None = None) -> PackageTable:
    """Insert every package from the CSV into a chaining hash table."""
    packages = PackageTable()
    with (path or DATA_DIR / "packages.csv").open(newline="") as handle:
        reader = csv.reader(handle)
        next(reader)
        for row in reader:
            package_id, address, city, state, zip_code, deadline, weight, notes = row
            package = Package(
                int(package_id),
                address,
                city,
                state,
                zip_code,
                deadline,
                int(weight),
                notes,
            )
            if "Delayed on flight" in package.notes:
                package.hub_arrival_time = DELAYED_ARRIVAL
            if "Wrong address" in package.notes:
                package.correction_time = CORRECTION_TIME
                package.corrected_address = CORRECTED_ADDRESS
                package.corrected_zip = CORRECTED_ZIP
            packages.insert(package.package_id, package)
    return packages


def check_manifests(loads: list[list[int]], packages: PackageTable) -> None:
    """Raise ValueError if the truck loads break a note from the package file."""
    flat = [package_id for load in loads for package_id in load]
    if len(flat) != len(set(flat)):
        raise ValueError("a package is loaded on more than one truck")
    missing = sorted(set(packages) - set(flat))
    if missing:
        raise ValueError(f"packages not on any truck: {missing}")
    unknown = sorted(set(flat) - set(packages))
    if unknown:
        raise ValueError(f"loads name packages that do not exist: {unknown}")
    for number, load in enumerate(loads, start=1):
        if len(load) > TRUCK_CAPACITY:
            raise ValueError(f"truck {number} carries {len(load)} packages, over 16")

    truck_of = {
        package_id: number
        for number, load in enumerate(loads, start=1)
        for package_id in load
    }
    for package in packages.values():
        package_id = package.package_id
        truck_number = truck_of[package_id]
        notes = package.notes.lower()
        if "can only be on truck 2" in notes and truck_number != 2:
            raise ValueError(f"package {package_id} must ride on truck 2")
        if "delayed on flight" in notes and truck_number == 1:
            raise ValueError(f"package {package_id} is not at the hub at 8:00 AM")
        if "wrong address" in notes and truck_number != 3:
            raise ValueError(f"package {package_id} needs the 10:20 AM address")
        if "must be delivered with" in notes:
            for partner in (int(token) for token in re.findall(r"\d+", notes)):
                if truck_of.get(partner) != truck_number:
                    raise ValueError(f"package {package_id} must travel with {partner}")


def run_day(data_dir: Path = DATA_DIR) -> Day:
    """Simulate the day once. Status queries then replay the saved timestamps."""
    addresses = load_addresses(data_dir / "addresses.csv")
    distances = load_distances(data_dir / "distances.csv")
    if len(distances) != len(addresses):
        raise ValueError(
            f"{len(addresses)} addresses but a {len(distances)}-row distance table"
        )
    index_of = address_index(addresses)
    packages = load_packages(data_dir / "packages.csv")
    check_manifests([list(load) for load in MANIFESTS], packages)

    truck1 = Truck(1, TRUCK1_PACKAGES, DAY_START)
    truck2 = Truck(2, TRUCK2_PACKAGES, DELAYED_ARRIVAL)
    truck3 = Truck(3, TRUCK3_PACKAGES, None)
    first_driver_back = min(
        truck1.deliver(packages, distances, index_of),
        truck2.deliver(packages, distances, index_of),
    )
    truck3.departure_time = max(first_driver_back, CORRECTION_TIME)
    truck3.deliver(packages, distances, index_of)
    return Day(packages, [truck1, truck2, truck3])
