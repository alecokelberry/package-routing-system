# Package Routing System

[![CI](https://github.com/alecokelberry/package-routing-system/actions/workflows/ci.yml/badge.svg)](https://github.com/alecokelberry/package-routing-system/actions/workflows/ci.yml)

Plans one day of same-day deliveries in Salt Lake City: 40 packages, 3 trucks, 2 drivers. It uses a
hand-written chaining hash table and a nearest-neighbor route, and has no dependencies outside the
standard library.

**Result:** 107.4 total miles, all 40 packages delivered on time.

## Problem

Every package has an address, a deadline (9:00 AM, 10:30 AM, or end of day), and sometimes a
constraint:

- some can only ride on truck 2
- some must ride with certain other packages
- four arrive on a delayed flight at 9:05 AM
- package 9 has the wrong address until 10:20 AM

Each truck holds at most 16 packages and averages 18 mph. There are only two drivers, so truck 3 can't
leave until one of them is back at the hub. A supervisor must be able to ask where any package is at any
time of day.

## Approach

| Piece                | File                    | How                                                                                                 |
| -------------------- | ----------------------- | --------------------------------------------------------------------------------------------------- |
| Package lookup       | `routing/hash_table.py` | Separate-chaining hash table, multiplicative hashing, doubles past 0.75 load. O(1) average.         |
| Truck loads          | `routing/depot.py`      | Written by hand, then checked against every note (capacity, truck-2-only, groups, flight, pkg 9).   |
| Route                | `routing/truck.py`      | Greedy nearest neighbor: drive to the closest remaining package, re-checked at every stop. O(n²).   |
| Status at any time   | `routing/package.py`    | The day is simulated once and timestamps are saved. A query compares the asked time to them.        |
| Address corrections  | `routing/package.py`    | `address_at(t)` gives the address known at time `t`, so truck 3 routes to package 9's new address. |

The hash table is written from scratch on purpose, since implementing one is the point of the project.
Python's `dict` is used only for small helper lookups.

### The day

```text
8:00   truck 1 out       the must-ride-together group and most 10:30 deadlines
8:13   4580 S 2300 E     the 9:00 AM package, second stop (the first is closer and in its group)
9:05   truck 2 out       delayed flight lands. The four truck-2-only packages ride here
9:53   truck 1 back
10:20  truck 3 out       truck 1's driver takes it once package 9's address is corrected
11:18  truck 2 back
12:11  truck 3 back
```

## Run it

Python 3.11+, nothing to install. Run from the repo root:

```bash
python -m routing mileage                 # miles per truck, any missed deadlines
python -m routing route                   # stop-by-stop timeline for each truck
python -m routing status --at "10:00 AM"  # every package at one time
python -m routing lookup 9 --at 9:00      # one package at one time
python -m routing                         # interactive menu
```

```text
$ python -m routing mileage
Truck 1:  34.0 miles, back at the hub at 9:53 AM
Truck 2:  40.0 miles, back at the hub at 11:18 AM
Truck 3:  33.4 miles, back at the hub at 12:11 PM
Total: 107.4 miles
Every package is on time.

$ python -m routing lookup 9 --at "11:00 AM"
Package 9 at 11:00 AM
  Address:  410 S State St
  City:     Salt Lake City
  ZIP:      84111
  Deadline: EOD
  Weight:   2 kg
  Status:   Delivered at 10:59 AM by truck 3
```

Times can be written `9:00 AM`, `9am`, or `13:05`. Exit codes: `0` success, `1` unknown package or bad
data file, `2` bad arguments.

## Tests

```bash
python -m unittest discover -s tests -v   # no install needed
```

The 47 tests cover the hash table (collisions, growth, None values), time parsing edge cases,
nearest-neighbor order on a small map you can check by hand, every manifest rule rejecting a bad load,
malformed distance tables, the full day, and CLI exit codes.

For linting and type checking:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
ruff format --check . && ruff check . && mypy && pytest
```

CI runs all of these on Python 3.11–3.13.

## Project structure

```text
routing/
  hash_table.py   ChainingHashTable
  package.py      Package record, time-dependent address and status
  truck.py        nearest-neighbor delivery loop
  depot.py        CSV loading, manifest checks, the simulated day
  timeutil.py     "9:05 AM" <-> hours since midnight
  cli.py          argparse commands and interactive menu
data/             packages, addresses, and a symmetric distance matrix (miles)
tests/            unittest suite, one file per module
```

## Limitations

- **The loads are chosen by hand.** The program checks them against the constraints but doesn't search
  for them. A different package set needs new loads.
- **Nearest neighbor is a heuristic.** It's fast and easy to follow, but it isn't optimal. Something like
  2-opt would likely shorten the routes.
- **Simplified physics:** constant 18 mph, zero time spent at each stop, and the distance table is
  trusted as given.
- The package 9 correction and the flight delay come from constants in `depot.py`, not from a live feed.
- `data/` is read relative to the source tree, so run it from a clone (or an editable install).

## License

[MIT](LICENSE)
