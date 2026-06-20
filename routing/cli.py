"""Mileage, one package, the whole board, or the stop order."""

from __future__ import annotations

import argparse
import sys

from routing.depot import Day, run_day
from routing.package import Package
from routing.timeutil import format_time, parse_time


def mileage_report(day: Day) -> str:
    lines = []
    for truck in day.trucks:
        lines.append(
            f"Truck {truck.truck_id}: {truck.mileage:5.1f} miles, "
            f"back at the hub at {format_time(truck.return_time or 0)}"
        )
    lines.append(f"Total: {day.total_mileage:.1f} miles")
    late = [package for package in day.packages.values() if not package.on_time()]
    if late:
        ids = ", ".join(str(package.package_id) for package in sorted(late, key=lambda p: p.package_id))
        lines.append(f"Missed deadlines: {ids}")
    else:
        lines.append("Every package is on time.")
    return "\n".join(lines)


def route_report(day: Day) -> str:
    lines = []
    for truck in day.trucks:
        lines.append(
            f"Truck {truck.truck_id} leaves {format_time(truck.departure_time or 0)}"
        )
        for number, package_id in enumerate(truck.stops, start=1):
            package = day.packages.lookup(package_id)
            assert package is not None
            lines.append(
                f"  {number:2}  {format_time(package.delivery_time or 0):8}  "
                f"{package.address_at(package.delivery_time or 0)}"
            )
        lines.append(f"  back at the hub {format_time(truck.return_time or 0)}")
        lines.append("")
    return "\n".join(lines).rstrip()


def status_report(day: Day, when: float) -> str:
    lines = [f"Status at {format_time(when)}", ""]
    for truck in day.trucks:
        lines.append(f"Truck {truck.truck_id}, departs {format_time(truck.departure_time or 0)}")
        lines.append(f"{'ID':<4} {'Deadline':<9} {'Status'}")
        for package_id in sorted(truck.package_ids):
            package = day.packages.lookup(package_id)
            assert package is not None
            lines.append(
                f"{package_id:<4} {package.deadline:<9} {package.status_at(when)}"
            )
        lines.append("")
    return "\n".join(lines).rstrip()


def package_report(package: Package, when: float) -> str:
    return "\n".join(
        [
            f"Package {package.package_id} at {format_time(when)}",
            f"  Address:  {package.address_at(when)}",
            f"  City:     {package.city}",
            f"  ZIP:      {package.zip_at(when)}",
            f"  Deadline: {package.deadline}",
            f"  Weight:   {package.weight} kg",
            f"  Status:   {package.status_at(when)}",
        ]
    )


def _ask_time() -> float:
    while True:
        entered = parse_time(input("Time of day (9:00 AM or 13:05): "))
        if entered is not None:
            return entered
        print("That is not a valid time.")


def interactive(day: Day) -> int:
    print("Parcel route")
    print(mileage_report(day))
    while True:
        print()
        print("1  Look up one package")
        print("2  Status of every package")
        print("3  Mileage")
        print("4  Exit")
        choice = input("Choose 1-4: ").strip()
        if choice == "1":
            raw = input("Package ID: ").strip()
            if not raw.isdigit() or day.packages.lookup(int(raw)) is None:
                print("No package with that ID.")
                continue
            when = _ask_time()
            print()
            print(package_report(day.packages.lookup(int(raw)), when))
        elif choice == "2":
            print()
            print(status_report(day, _ask_time()))
        elif choice == "3":
            print()
            print(mileage_report(day))
        elif choice == "4":
            return 0
        else:
            print("Choose 1, 2, 3, or 4.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="routing",
        description="Look up parcel status for a finished same-day route.",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("mileage", help="Miles driven and whether every deadline was met")
    sub.add_parser("route", help="Stop order for each truck")
    status = sub.add_parser("status", help="Every package at one time of day")
    status.add_argument("--at", required=True, help="Time, such as '10:00 AM'")
    lookup = sub.add_parser("lookup", help="One package at one time of day")
    lookup.add_argument("package_id", type=int)
    lookup.add_argument("--at", required=True, help="Time, such as '11:00 AM'")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        day = run_day()
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1

    if args.command is None:
        try:
            return interactive(day)
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

    if args.command == "mileage":
        print(mileage_report(day))
        return 0
    if args.command == "route":
        print(route_report(day))
        return 0

    when = parse_time(args.at)
    if when is None:
        print(f"Not a time of day: {args.at}", file=sys.stderr)
        return 1
    if args.command == "status":
        print(status_report(day, when))
        return 0

    package = day.packages.lookup(args.package_id)
    if package is None:
        print(f"No package {args.package_id}.", file=sys.stderr)
        return 1
    print(package_report(package, when))
    return 0
