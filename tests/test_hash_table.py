"""ChainingHashTable: the core operations, collisions, and growth."""

from __future__ import annotations

import unittest

from routing.hash_table import ChainingHashTable


class HashTableTests(unittest.TestCase):
    def test_insert_lookup_replace_and_remove(self) -> None:
        table: ChainingHashTable[int, str] = ChainingHashTable()
        table.insert(1, "a")
        table.insert(1, "b")
        table.insert(2, "c")
        self.assertEqual(len(table), 2)
        self.assertEqual(table.lookup(1), "b")
        self.assertEqual(table.lookup(2), "c")
        self.assertIsNone(table.lookup(3))
        self.assertTrue(table.remove(1))
        self.assertFalse(table.remove(1))
        self.assertIsNone(table.lookup(1))
        self.assertEqual(len(table), 1)

    def test_every_key_in_one_bucket_still_resolves(self) -> None:
        table: ChainingHashTable[int, int] = ChainingHashTable(initial_capacity=1)
        table.insert(10, 100)
        table.insert(20, 200)
        self.assertEqual(table.lookup(10), 100)
        self.assertEqual(table.lookup(20), 200)
        self.assertTrue(table.remove(10))
        self.assertEqual(table.lookup(20), 200)

    def test_grows_past_three_quarters_load_and_keeps_every_key(self) -> None:
        table: ChainingHashTable[int, int] = ChainingHashTable(initial_capacity=4)
        for key in range(3):
            table.insert(key, key)
        self.assertEqual(table.capacity, 4)
        table.insert(3, 3)
        self.assertEqual(table.capacity, 8)
        for key in range(4, 200):
            table.insert(key, key * 10)
        self.assertEqual(len(table), 200)
        self.assertLessEqual(len(table) / table.capacity, 0.75)
        self.assertEqual(table.lookup(150), 1500)
        self.assertEqual(sorted(table), list(range(200)))

    def test_contains_sees_a_key_whose_value_is_none(self) -> None:
        table: ChainingHashTable[str, None] = ChainingHashTable()
        table.insert("present", None)
        self.assertIn("present", table)
        self.assertNotIn("absent", table)

    def test_values_returns_each_value_once(self) -> None:
        table: ChainingHashTable[int, str] = ChainingHashTable(initial_capacity=2)
        for key in range(10):
            table.insert(key, f"v{key}")
        self.assertEqual(sorted(table.values()), sorted(f"v{k}" for k in range(10)))

    def test_rejects_a_zero_capacity(self) -> None:
        with self.assertRaises(ValueError):
            ChainingHashTable(initial_capacity=0)


if __name__ == "__main__":
    unittest.main()
