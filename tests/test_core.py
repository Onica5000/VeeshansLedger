"""Regression tests. Run:  python tests/test_core.py"""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from eqlsky import parsers, model  # noqa: E402

DATA = os.path.join(ROOT, "data", "sky.json")

ACH = """Untapped Potential: Classes
I\tPrimary Class Unlock - Cleric
C\t\tObtain Truewind Earring.
I\t\tObtain Baton of the Sky.
I\t\tThis achievement will autocomplete if you chose to confirm your Primary Class as a Cleric.
I\t\tThis achievement can be bypassed using a Primary Class Unlock Token.
C\tPrimary Class Unlock - Ranger
C\t\tObtain Windstriker.
I\t\tThis achievement will autocomplete if you chose to confirm your Primary Class as a Ranger.
C\t\tThis achievement can be bypassed using a Primary Class Unlock Token.
Untapped Potential: Deity
"""

INV = "\t".join(["Location", "Name", "ID", "Count", "Slots"]) + "\n" + "\n".join([
    "Bank1\tEfreeti Standard\t1\t1\t0",
    "Bank2\tEmpty\t0\t0\t0",
    "General1\tKhyldorn the Blood Drinker +10\t2\t1\t0",
    "Equipment3\tWindstriker +9\t3\t1\t0",
    "Augmentation1\tOrb of Tishan (Exaltation)\t4\t1\t0",
    "Personal-Depot1\tBlue Diamond\t5\t51\t0",
])


class TestParsers(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def _write(self, stem, ach=True, inv=True):
        if ach:
            with open(os.path.join(self.dir, stem + "-Achievements.txt"), "w",
                      encoding="utf-8") as fh:
                fh.write(ACH)
        if inv:
            with open(os.path.join(self.dir, stem + "-Inventory.txt"), "w",
                      encoding="utf-8") as fh:
                fh.write(INV)

    def test_normalise_strips_suffix_and_exaltation(self):
        self.assertEqual(parsers.normalise_item("Khyldorn +10"), "Khyldorn")
        self.assertEqual(parsers.normalise_item("Orb of Tishan (Exaltation)"), "Orb of Tishan")
        self.assertEqual(parsers.normalise_item("Plain Item"), "Plain Item")

    def test_inventory_excludes_depot_and_empty(self):
        self._write("Testchar_server")
        inv = parsers.parse_inventory(os.path.join(self.dir, "Testchar_server-Inventory.txt"))
        self.assertIn("Efreeti Standard", inv["counts"])
        self.assertNotIn("Empty", inv["counts"])
        self.assertNotIn("Blue Diamond", inv["counts"], "depot rows must be ignored")
        self.assertEqual(inv["locations"]["Windstriker"], {"Equipment"})

    def test_achievements_status_and_flags(self):
        self._write("Testchar_server")
        ach = parsers.parse_achievements(os.path.join(self.dir, "Testchar_server-Achievements.txt"))
        self.assertIn("Truewind Earring", ach["classes"]["Cleric"]["obtained"])
        self.assertIn("Baton of the Sky", ach["classes"]["Cleric"]["missing"])
        self.assertTrue(ach["classes"]["Ranger"]["unlocked"])
        self.assertTrue(ach["classes"]["Ranger"]["token_used"])
        self.assertFalse(ach["classes"]["Cleric"]["unlocked"])

    def test_never_cross_pairs_two_characters(self):
        """The alt's inventory is newer, but must not be paired with the main's achievements."""
        self._write("Testchar_server")
        self._write("Altchar_server", ach=False, inv=True)
        os.utime(os.path.join(self.dir, "Altchar_server-Inventory.txt"), None)
        e = parsers.find_exports(self.dir)
        self.assertEqual(e["stem"], "Testchar_server")
        self.assertTrue(e["achievements"].endswith("Testchar_server-Achievements.txt"))
        self.assertTrue(e["inventory"].endswith("Testchar_server-Inventory.txt"))
        self.assertEqual(e["others"], ["Altchar_server"])

    def test_explicit_character_selection(self):
        self._write("Testchar_server")
        self._write("Altchar_server", ach=False, inv=True)
        e = parsers.find_exports(self.dir, prefer="Altchar_server")
        self.assertEqual(e["stem"], "Altchar_server")
        self.assertIsNone(e["achievements"])


class TestDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = model.load_dataset(DATA)

    def test_shape(self):
        tests = [t for c in self.data["classes"] for t in c["tests"]]
        self.assertEqual(len(self.data["classes"]), 16)
        self.assertEqual(len(tests), 95, "Shadow Knight has 7 tests incl. Raising of the Dead")
        per = {c["name"]: len(c["tests"]) for c in self.data["classes"]}
        self.assertEqual(per["Paladin"], 4)
        self.assertEqual(per["Beastlord"], 5)
        self.assertEqual(per["Magician"], 7)
        self.assertEqual(per["Shadow Knight"], 7)

    def test_every_component_resolves_to_an_island(self):
        bad = [(c["name"], t["test"], x["source"])
               for c in self.data["classes"] for t in c["tests"]
               for x in t["components"] if x["island"] == "?"]
        self.assertEqual(bad, [])

    def test_every_test_has_rune_and_trigger(self):
        for c in self.data["classes"]:
            for t in c["tests"]:
                self.assertTrue(t["rune"].startswith("Wind Rune "), t["test"])
                self.assertTrue(t.get("trigger"), t["test"])

    def test_turnin_npc_present_for_every_class(self):
        for c in self.data["classes"]:
            self.assertTrue(c["turnin_npc"], c["name"])


class TestTracker(unittest.TestCase):
    def setUp(self):
        self.data = model.load_dataset(DATA)
        self.dir = tempfile.mkdtemp()
        with open(os.path.join(self.dir, "Testchar_server-Achievements.txt"), "w",
                  encoding="utf-8") as fh:
            fh.write(ACH)
        with open(os.path.join(self.dir, "Testchar_server-Inventory.txt"), "w",
                  encoding="utf-8") as fh:
            fh.write(INV)
        e = parsers.find_exports(self.dir)
        self.tr = model.Tracker(self.data,
                                parsers.parse_achievements(e["achievements"]),
                                parsers.parse_inventory(e["inventory"]))

    def _cls(self, name):
        return next(c for c in self.data["classes"] if c["name"] == name)

    def test_achievements_beat_inventory(self):
        """Truewind Earring is obtained per achievements but NOT in the inventory."""
        cls = self._cls("Cleric")
        test = next(t for t in cls["tests"] if t["reward"] == "Truewind Earring")
        self.assertEqual(self.tr.test_status(cls, test)[0], model.DONE)

    def test_partial_when_one_component_held(self):
        cls = self._cls("Cleric")
        test = next(t for t in cls["tests"] if t["reward"] == "Baton of the Sky")
        status, have, need = self.tr.test_status(cls, test)
        self.assertEqual(status, model.PARTIAL)
        self.assertEqual([h["item"] for h in have], ["Efreeti Standard"])
        self.assertEqual([n["item"] for n in need], ["Mithril Bands"])

    def test_manual_override_marks_component_held(self):
        cls = self._cls("Cleric")
        test = next(t for t in cls["tests"] if t["reward"] == "Baton of the Sky")
        self.tr.overrides["have:Mithril Bands"] = True
        self.assertEqual(self.tr.test_status(cls, test)[0], model.READY)

    def test_farm_list_counts_per_test_not_per_item(self):
        """Turn-ins consume components, so a shared item is needed once per Test."""
        counts = {r["item"]: r["count"]
                  for rows in self.tr.farm_list().values() for r in rows}
        self.assertEqual(counts.get("Mithril Bands"), 2,
                         "Cleric Test of The Weak + Beastlord Test of Claw")

    def test_unlocked_classes_sort_last(self):
        rows = self.tr.all_progress()
        first_unlocked = next(i for i, r in enumerate(rows) if r["unlocked"])
        self.assertTrue(all(r["unlocked"] for r in rows[first_unlocked:]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
