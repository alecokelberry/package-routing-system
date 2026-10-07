"""Command-line output and exit codes."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from routing.cli import main


def run(*argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = main(list(argv))
        except SystemExit as exit_:
            code = int(exit_.code or 0)
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def test_mileage(self) -> None:
        code, out, _ = run("mileage")
        self.assertEqual(code, 0)
        self.assertIn("Total: 107.4 miles", out)
        self.assertIn("Every package is on time.", out)

    def test_route_lists_every_stop(self) -> None:
        code, out, _ = run("route")
        self.assertEqual(code, 0)
        self.assertEqual(out.count("back at the hub"), 3)
        self.assertIn("Truck 3 leaves 10:20 AM", out)

    def test_status_at_a_time(self) -> None:
        code, out, _ = run("status", "--at", "10:00 AM")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("Status at 10:00 AM"))
        self.assertIn("Delivered at", out)

    def test_lookup_shows_the_address_known_at_that_time(self) -> None:
        _, before, _ = run("lookup", "9", "--at", "9:00 AM")
        _, after, _ = run("lookup", "9", "--at", "11:00 AM")
        self.assertIn("300 State St", before)
        self.assertIn("410 S State St", after)
        self.assertIn("Delivered at 10:59 AM by truck 3", after)

    def test_unknown_package_exits_1(self) -> None:
        code, out, err = run("lookup", "99", "--at", "9:00")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("no package with id 99", err)

    def test_bad_time_is_a_usage_error(self) -> None:
        code, _, err = run("status", "--at", "25:00")
        self.assertEqual(code, 2)
        self.assertIn("not a time of day", err)

    def test_missing_time_is_a_usage_error(self) -> None:
        code, _, _ = run("lookup", "9")
        self.assertEqual(code, 2)

    def test_version(self) -> None:
        code, out, _ = run("--version")
        self.assertEqual(code, 0)
        self.assertRegex(out, r"^routing \d+\.\d+\.\d+")


if __name__ == "__main__":
    unittest.main()
