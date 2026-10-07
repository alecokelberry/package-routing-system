"""Mileage, one package, the whole board, or the stop order."""

from __future__ import annotations

import argparse
import sys

from routing import __version__
from routing.depot import Day, run_day
from routing.package import Package
from routing.timeutil import format_time, parse_time

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_INTERRUPTED = 130

EXAMPLES = """\
examples:
  python -m routing mileage
  python -m routing route
  python -m routing status --at "10:00 AM"
  python -m routing lookup 9 --at 9:00
  python -m routing            (interactive menu)

exit codes: 0 ok, 1 unknown package or bad data, 2 bad arguments
"""


def _clock(hours: float | None) -> str:
    return "--" if hours is None else format_time(hours)


def _package(day: Day, package_id: int) -> Package:
    package = day.packages.lookup(package_id)
    if package is None:
        raise KeyError(package_id)
    return package


def mileage_report(day: Day) -> str:
    lines = [
        f"Truck {truck.truck_id}: {truck.mileage:5.1f} miles, "
        f"back at the hub at {_clock(truck.return_time)}"
        for truck in day.trucks
    ]
    lines.append(f"Total: {day.total_mileage:.1f} miles")
    late = sorted(
        package.package_id for package in day.packages.values() if not package.on_time()
    )
    if late:
        lines.append(f"Missed deadlines: {', '.join(map(str, late))}")
    else:
        lines.append("Every package is on time.")
    return "\n".join(lines)


def route_report(day: Day) -> str:
    lines = []
    for truck in day.trucks:
        lines.append(f"Truck {truck.truck_id} leaves {_clock(truck.departure_time)}")
        for number, package_id in enumerate(truck.stops, start=1):
            package = _package(day, package_id)
            delivered = package.delivery_time or 0.0
            lines.append(
                f"  {number:2}  {format_time(delivered):8}  "
                f"{package.address_at(delivered)}"
            )
        lines.append(f"  back at the hub {_clock(truck.return_time)}")
        lines.append("")
    return "\n".join(lines).rstrip()


def status_report(day: Day, when: float) -> str:
    lines = [f"Status at {format_time(when)}", ""]
    for truck in day.trucks:
        lines.append(f"Truck {truck.truck_id}, departs {_clock(truck.departure_time)}")
        lines.append(f"{'ID':<4} {'Deadline':<9} Status")
        for package_id in sorted(truck.package_ids):
            package = _package(day, package_id)
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


def _time_argument(text: str) -> float:
    """argparse type: a time of day, or a usage error."""
    when = parse_time(text)
    if when is None:
        raise argparse.ArgumentTypeError(
            f"not a time of day: {text!r} (try '9:00 AM' or '13:05')"
        )
    return when


def _ask_time() -> float:
    while True:
        entered = parse_time(input("Time of day (9:00 AM or 13:05): "))
        if entered is not None:
            return entered
        print("That is not a valid time.")


def interactive(day: Day) -> int:
    print("Package routing")
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
            package = day.packages.lookup(int(raw)) if raw.isdigit() else None
            if package is None:
                print("No package with that ID.")
                continue
            when = _ask_time()
            print()
            print(package_report(package, when))
        elif choice == "2":
            when = _ask_time()
            print()
            print(status_report(day, when))
        elif choice == "3":
            print()
            print(mileage_report(day))
        elif choice == "4":
            return EXIT_OK
        else:
            print("Choose 1, 2, 3, or 4.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="routing",
        description=(
            "Simulate one same-day delivery run and report on it. "
            "With no command, opens an interactive menu."
        ),
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.add_parser("mileage", help="miles per truck and whether every deadline was met")
    sub.add_parser("route", help="stop order and delivery time for each truck")
    status = sub.add_parser("status", help="every package's status at one time of day")
    status.add_argument(
        "--at",
        required=True,
        type=_time_argument,
        metavar="TIME",
        help="e.g. '10:00 AM'",
    )
    lookup = sub.add_parser("lookup", help="one package's details at one time of day")
    lookup.add_argument("package_id", type=int, metavar="ID", help="package id, 1-40")
    lookup.add_argument(
        "--at",
        required=True,
        type=_time_argument,
        metavar="TIME",
        help="e.g. '11:00 AM'",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        day = run_day()
    except (OSError, ValueError, KeyError) as error:
        print(f"error: could not simulate the day: {error}", file=sys.stderr)
        return EXIT_ERROR

    if args.command is None:
        try:
            return interactive(day)
        except EOFError:
            print()
            return EXIT_OK
        except KeyboardInterrupt:
            print()
            return EXIT_INTERRUPTED

    if args.command == "mileage":
        print(mileage_report(day))
    elif args.command == "route":
        print(route_report(day))
    elif args.command == "status":
        print(status_report(day, args.at))
    else:
        package = day.packages.lookup(args.package_id)
        if package is None:
            print(f"error: no package with id {args.package_id}", file=sys.stderr)
            return EXIT_ERROR
        print(package_report(package, args.at))
    return EXIT_OK
