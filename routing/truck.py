"""One truck and a nearest-neighbor trip from the hub."""

from __future__ import annotations

from routing.hash_table import ChainingHashTable
from routing.package import Package

AVERAGE_SPEED_MPH = 18.0
HUB_INDEX = 0


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
        packages: ChainingHashTable,
        distances: list[list[float]],
        index_of_address,
    ) -> None:
        """Deliver this load one stop at a time.

        From the current street, the next stop is the closest package still
        on the truck. The route is not planned in advance, so an address that
        gets corrected during the day is used on the next choice. The truck
        then returns to the hub so its driver can leave again.
        """
        if self.departure_time is None:
            raise RuntimeError(f"truck {self.truck_id} has no departure time")

        clock = self.departure_time
        location = HUB_INDEX

        for package_id in self.package_ids:
            package = _require(packages, package_id)
            package.truck_id = self.truck_id
            package.departure_time = self.departure_time

        remaining = list(self.package_ids)
        while remaining:
            nearest_id = remaining[0]
            nearest_distance = _distance(
                packages, distances, index_of_address, location, nearest_id, clock
            )
            for package_id in remaining[1:]:
                distance = _distance(
                    packages, distances, index_of_address, location, package_id, clock
                )
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_id = package_id

            self.mileage += nearest_distance
            clock += nearest_distance / AVERAGE_SPEED_MPH
            delivered = _require(packages, nearest_id)
            delivered.delivery_time = clock
            location = index_of_address(delivered.address_at(clock))
            self.stops.append(nearest_id)
            remaining.remove(nearest_id)

        return_leg = distances[location][HUB_INDEX]
        self.mileage += return_leg
        clock += return_leg / AVERAGE_SPEED_MPH
        self.return_time = clock


def _require(packages: ChainingHashTable, package_id: int) -> Package:
    package = packages.lookup(package_id)
    if package is None:
        raise KeyError(package_id)
    return package


def _distance(
    packages, distances, index_of_address, location: int, package_id: int, clock: float
) -> float:
    package = _require(packages, package_id)
    destination = index_of_address(package.address_at(clock))
    return distances[location][destination]
