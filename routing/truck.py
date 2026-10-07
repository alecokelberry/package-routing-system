"""One truck and a nearest-neighbor trip from the hub."""

from __future__ import annotations

from collections.abc import Callable

from routing.package import Package, PackageTable

AVERAGE_SPEED_MPH = 18.0
HUB_INDEX = 0

# Street text in, row of the distance matrix out.
AddressIndex = Callable[[str], int]


class Truck:
    """A loaded truck: manifest, clock, and miles driven."""

    def __init__(
        self, truck_id: int, package_ids: list[int], departure_time: float | None
    ) -> None:
        self.truck_id = truck_id
        self.package_ids = list(package_ids)
        self.departure_time = departure_time
        self.mileage = 0.0
        self.return_time: float | None = None
        self.stops: list[int] = []

    def deliver(
        self,
        packages: PackageTable,
        distances: list[list[float]],
        index_of_address: AddressIndex,
    ) -> float:
        """Deliver this load one stop at a time and return the time back at the hub.

        From the current street, the next stop is the closest package still
        on the truck. The route is not planned in advance, so an address that
        gets corrected during the day is used on the next choice. The truck
        then returns to the hub so its driver can leave again.

        Each choice scans the remaining packages, so a load of n packages
        costs O(n^2) distance lookups.
        """
        if self.departure_time is None:
            raise RuntimeError(f"truck {self.truck_id} has no departure time")

        clock = self.departure_time
        location = HUB_INDEX

        remaining = [_require(packages, package_id) for package_id in self.package_ids]
        for package in remaining:
            package.truck_id = self.truck_id
            package.departure_time = self.departure_time

        def miles_to(package: Package) -> float:
            return distances[location][index_of_address(package.address_at(clock))]

        while remaining:
            # min() keeps the first of equal distances, so ties go to manifest order.
            nearest = min(remaining, key=miles_to)
            distance = miles_to(nearest)
            self.mileage += distance
            clock += distance / AVERAGE_SPEED_MPH
            nearest.delivery_time = clock
            location = index_of_address(nearest.address_at(clock))
            self.stops.append(nearest.package_id)
            remaining.remove(nearest)

        return_leg = distances[location][HUB_INDEX]
        self.mileage += return_leg
        clock += return_leg / AVERAGE_SPEED_MPH
        self.return_time = clock
        return clock


def _require(packages: PackageTable, package_id: int) -> Package:
    package = packages.lookup(package_id)
    if package is None:
        raise KeyError(f"no package {package_id} in the table")
    return package
