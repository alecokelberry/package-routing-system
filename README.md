# Parcel route

40 packages, 3 trucks, 2 drivers, Salt Lake City. 107.4 miles. Nothing late.

```text
8:00   truck 1 out
8:06   4300 S 1300 E
8:13   4580 S 2300 E     three packages, one of them due at 9:00
9:05   truck 2 out       flight landed. four packages can only ride this truck
9:53   truck 1 back
10:20  truck 3 out       package 9 has the right street. truck 1's driver takes it
11:18  truck 2 back
12:11  truck 3 back
```

The 9:00 package is the second stop, not the first. 4300 S 1300 E is closer, and that box has to ride with the 9:00 one.

Ask about package 9 at 9:00 and the file still says 300 State St. At 11:00 it says 410 S State St, delivered at 10:59.

Who rides which truck is listed in `routing/depot.py`. Those lists get checked against the notes before a truck leaves: 16 max, truck 2 only, the together groups, the flight, package 9. After that the truck drives to whichever of its packages is closest. 18 mph.

Packages sit in a hash table keyed by id, so a lookup doesn't walk the whole list.

```shell
python3 -m routing mileage
python3 -m routing route
python3 -m routing lookup 9 --at "9:00 AM"
python3 -m unittest discover -s tests -v
```

Python 3.11 or newer. Nothing to install. Code is [MIT](LICENSE).
