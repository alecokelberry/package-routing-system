"""One package and the clock times that decide its status."""

from __future__ import annotations

from routing.timeutil import format_time, parse_time, to_minutes

# End of day is 5:00 PM. Packages without a morning deadline are due then.
END_OF_DAY = 17.0


class Package:
    """A parcel plus the timestamps the simulator fills in."""

    def __init__(
        self,
        package_id: int,
        address: str,
        city: str,
        state: str,
        zip_code: str,
        deadline: str,
        weight: int,
        notes: str,
    ) -> None:
        self.package_id = package_id
        self.address = address
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.deadline = deadline
        self.weight = weight
        self.notes = notes

        # Some packages ship with a bad address that is corrected later.
        self.corrected_address: str | None = None
        self.corrected_zip: str | None = None
        self.correction_time: float | None = None

        self.hub_arrival_time = 8.0
        self.departure_time: float | None = None
        self.delivery_time: float | None = None
        self.truck_id: int | None = None

    def address_at(self, when: float) -> str:
        """Street address known at this time of day."""
        if self.correction_time is not None and when >= self.correction_time:
            return self.corrected_address or self.address
        return self.address

    def zip_at(self, when: float) -> str:
        """ZIP code known at this time of day."""
        if self.correction_time is not None and when >= self.correction_time:
            return self.corrected_zip or self.zip_code
        return self.zip_code

    def deadline_hours(self) -> float:
        """Deadline as hours since midnight. 'EOD' is 5:00 PM."""
        if self.deadline.strip().upper() == "EOD":
            return END_OF_DAY
        parsed = parse_time(self.deadline)
        if parsed is None:
            raise ValueError(f"package {self.package_id} has no deadline")
        return parsed

    def on_time(self) -> bool:
        """True when the delivery minute is at or before the deadline minute."""
        if self.delivery_time is None:
            return False
        return to_minutes(self.delivery_time) <= to_minutes(self.deadline_hours())

    def status_at(self, when: float) -> str:
        """Status a supervisor would see if they asked at `when`."""
        if when < self.hub_arrival_time:
            if "Delayed on flight" in self.notes:
                return f"Delayed, arrives at the hub at {format_time(self.hub_arrival_time)}"
            return "At the hub"
        if self.departure_time is None or when < self.departure_time:
            return f"At the hub since {format_time(self.hub_arrival_time)}"
        if self.delivery_time is None or when < self.delivery_time:
            return (
                f"En route on truck {self.truck_id} "
                f"(departed {format_time(self.departure_time)})"
            )
        return (
            f"Delivered at {format_time(self.delivery_time)} by truck {self.truck_id}"
        )
