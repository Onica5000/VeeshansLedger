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
    "General2\tBone Chips\t6\t448\t0",
    "General3\tBone Chips\t7\t52\t0",
    "General4\tMystery Thing\t8\tnot-a-number\t0",
    "Personal-Depot9\tMetal Bits\t9\t222\t0",
    "Hoard 5\tEfreeti War Bow\t10\t1\t0",
    "Hoard 1-Slot2\tPower of Wind\t11\t1\t0",
    "KeyRing\tSky Key\t12\t1\t0",
    "Any Slot-Slot7\tIdol of the Underking\t13\t1\t0",
    "Chest\tBreastplate of Wind\t14\t1\t0",
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

    def test_every_storage_location_is_searched(self):
        """Nothing is skipped. The Depot exclusion hid four real epic components."""
        self._write("Testchar_server")
        inv = parsers.parse_inventory(os.path.join(self.dir, "Testchar_server-Inventory.txt"))
        self.assertEqual(inv["counts"]["Metal Bits"], 222, "Personal Depot must be searched")
        self.assertEqual(inv["locations"]["Metal Bits"], {"Depot"})
        self.assertEqual(inv["locations"]["Efreeti War Bow"], {"Dragon's Hoard"})
        self.assertEqual(inv["locations"]["Power of Wind"], {"Dragon's Hoard"})
        self.assertEqual(inv["locations"]["Sky Key"], {"Key Ring"})
        self.assertEqual(inv["locations"]["Blue Diamond"], {"Depot"})

    def test_equipment_slots_collapse_to_worn(self):
        self.assertEqual(parsers.area_for("Chest"), "Worn")
        self.assertEqual(parsers.area_for("Fingers2"), "Worn")
        self.assertEqual(parsers.area_for("Any Slot-Slot7"), "Worn",
                         "must not be truncated at the space to 'Any'")
        self.assertEqual(parsers.area_for("Activated"), "Worn")

    def test_an_unknown_location_surfaces_by_name(self):
        """A storage type added by a future patch must not read as worn gear.

        This is the guard that would have caught the Dragon's Hoard being
        labelled "Worn" - the item was found, but the app never named the
        place it was in, so it read as "not checking the hoard".
        """
        self.assertEqual(parsers.area_for("GuildVault9"), "GuildVault")
        self.assertEqual(parsers.area_for("Mount Keeper 2"), "Mount Keeper")

    def test_every_container_prefix_has_a_label(self):
        for prefix, label in parsers.CONTAINERS:
            self.assertEqual(parsers.area_for(prefix + "1"), label)

    def test_inventory_uses_stack_size_not_row_count(self):
        """A stack of 448 Bone Chips is 448, and two stacks add up."""
        self._write("Testchar_server")
        inv = parsers.parse_inventory(os.path.join(self.dir, "Testchar_server-Inventory.txt"))
        self.assertEqual(inv["counts"]["Bone Chips"], 500)
        self.assertEqual(inv["counts"]["Efreeti Standard"], 1)

    def test_inventory_survives_an_unparsable_count(self):
        self._write("Testchar_server")
        inv = parsers.parse_inventory(os.path.join(self.dir, "Testchar_server-Inventory.txt"))
        self.assertEqual(inv["counts"]["Mystery Thing"], 1)

    def test_normalise_strips_suffix_and_exaltation(self):
        self.assertEqual(parsers.normalise_item("Khyldorn +10"), "Khyldorn")
        self.assertEqual(parsers.normalise_item("Orb of Tishan (Exaltation)"), "Orb of Tishan")
        self.assertEqual(parsers.normalise_item("Plain Item"), "Plain Item")

    def test_inventory_skips_empty_slots_but_nothing_else(self):
        """Only "Empty" placeholder rows are dropped.

        This test used to assert the opposite for the Personal Depot. That was
        wrong - the depot holds epic components, and skipping it hid items the
        player owned.
        """
        self._write("Testchar_server")
        inv = parsers.parse_inventory(os.path.join(self.dir, "Testchar_server-Inventory.txt"))
        self.assertIn("Efreeti Standard", inv["counts"])
        self.assertNotIn("Empty", inv["counts"])
        self.assertEqual(inv["counts"]["Blue Diamond"], 51, "depot rows count")
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




EPIC_DATA = {
    "schema": 1,
    "availability": {"kunark_released": False, "epics_released": False,
                     "note": "Epics are a later era than Kunark.",
                     "exception_note": "", "data_warning": ""},
    "eras": {
        "NOW": {"label": "Available now", "blocked": False},
        "KUNARK": {"label": "Needs Kunark", "blocked": True},
    },
    "classes": [
        {"name": "Warrior", "reward": "Jagged Blade of War", "summary": "",
         "completable": False, "counts": {"total": 3, "now": 2, "blocked": 1},
         "steps": [
             {"step": "1", "item": "Efreeti Standard", "mob": "Noble Dojorn",
              "zone": "Plane of Sky", "era": "NOW", "blocked": True,
              "zone_live": True, "notes": ""},
             {"step": "2", "item": "Nonexistent Thing", "mob": "a mob",
              "zone": "Kithicor Forest", "era": "NOW", "blocked": True,
              "zone_live": True, "notes": ""},
             {"step": "3", "item": "Kunark Thing", "mob": "a sarnak",
              "zone": "Chardok", "era": "KUNARK", "blocked": True,
              "zone_live": False, "notes": ""},
         ]},
        {"name": "Cleric", "reward": "Water Sprinkler of Nem Ankh", "summary": "",
         "completable": False, "counts": {"total": 1, "now": 0, "blocked": 1},
         "steps": [
             {"step": "1", "item": "Kunark Thing", "mob": "a sarnak",
              "zone": "Chardok", "era": "KUNARK", "blocked": True,
              "zone_live": False, "notes": ""},
         ]},
    ],
}


class TestEpics(unittest.TestCase):
    def setUp(self):
        inv = {"counts": {"Efreeti Standard": 1},
               "locations": {"Efreeti Standard": {"Bank"}}}
        self.et = model.EpicTracker(EPIC_DATA, inv)

    def test_nothing_is_completable_while_the_epics_era_is_unreleased(self):
        """Epics land AFTER Kunark in EQL, so a live zone never means completable."""
        self.assertFalse(self.et.epics_released)
        s = self.et.summary()
        self.assertEqual(s["blocked"], 4, "every step blocked until the Epics era")
        self.assertEqual(s["zone_live"], 2, "but two zones are reachable today")
        self.assertEqual(s["completable"], [])

    def test_only_now_filter_keeps_live_zones(self):
        allsteps = self.et.steps_for("Warrior")
        nowsteps = self.et.steps_for("Warrior", only_now=True)
        self.assertEqual(len(allsteps), 3)
        self.assertEqual(len(nowsteps), 2)
        self.assertTrue(all(s["zone_live"] for s in nowsteps))

    def test_held_comes_from_inventory(self):
        steps = {s["item"]: s for s in self.et.steps_for("Warrior")}
        self.assertTrue(steps["Efreeti Standard"]["held"])
        self.assertFalse(steps["Nonexistent Thing"]["held"])
        self.assertEqual(steps["Efreeti Standard"]["where"], "Bank")

    def test_shopping_list_excludes_held_and_unreachable_zones(self):
        sl = self.et.shopping_list()
        items = [i["item"] for rows in sl.values() for i in rows]
        self.assertIn("Nonexistent Thing", items)
        self.assertNotIn("Efreeti Standard", items, "already held")
        self.assertNotIn("Kunark Thing", items, "zone not reachable")

    def test_manual_override_marks_epic_item_held(self):
        self.et.overrides["epic_have:Nonexistent Thing"] = True
        self.assertTrue(self.et.held("Nonexistent Thing"))
        items = [i["item"] for rows in self.et.shopping_list().values() for i in rows]
        self.assertNotIn("Nonexistent Thing", items)

    def test_classes_with_most_outstanding_sort_first(self):
        rows = self.et.class_rows()
        self.assertEqual(rows[0]["name"], "Warrior")

    def test_flipping_both_era_flags_unblocks_everything(self):
        """Both flags must flip: Epics is a separate, later era than Kunark."""
        import copy
        data = copy.deepcopy(EPIC_DATA)
        data["availability"]["kunark_released"] = True
        data["availability"]["epics_released"] = True
        for c in data["classes"]:
            for s in c["steps"]:
                s["blocked"] = False
        et = model.EpicTracker(data, {"counts": {}, "locations": {}})
        self.assertTrue(et.epics_released)
        self.assertEqual(et.summary()["blocked"], 0)



class TestSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sky = model.load_dataset(DATA)
        epics = model.load_dataset(os.path.join(ROOT, "data", "epics.json"))
        inv = {"counts": {"Efreeti Standard": 1, "Ball of Everliving Golem": 1},
               "locations": {"Efreeti Standard": {"Bank"},
                             "Ball of Everliving Golem": {"Equipment"}}}
        cls.idx = model.build_index(model.Tracker(sky, None, inv),
                                    model.EpicTracker(epics, inv))

    def test_index_spans_both_datasets(self):
        kinds = {r["dataset"] for r in self.idx}
        self.assertEqual(kinds, {model.SKY, model.EPIC})
        self.assertGreater(len(self.idx), 400)

    def test_empty_query_returns_nothing(self):
        self.assertEqual(model.search(self.idx, ""), [])
        self.assertEqual(model.search(self.idx, "   "), [])

    def test_item_search_finds_every_test_that_needs_it(self):
        hits = model.search(self.idx, "Mithril Bands")
        classes = {h["cls"] for h in hits}
        self.assertIn("Cleric", classes)
        self.assertIn("Beastlord", classes)

    def test_mob_search_spans_classes(self):
        """One Phinigel kill serves several different epics - the app should say so."""
        hits = model.search(self.idx, "Phinigel")
        self.assertGreaterEqual(len({h["cls"] for h in hits}), 3)

    def test_zone_search(self):
        hits = model.search(self.idx, "Plane of Hate")
        self.assertTrue(hits)
        self.assertTrue(all("hate" in h["zone"].lower() for h in hits))

    def test_terms_narrow_rather_than_widen(self):
        broad = model.search(self.idx, "plane")
        narrow = model.search(self.idx, "plane hate")
        self.assertLess(len(narrow), len(broad))

    def test_held_state_is_reported(self):
        hits = model.search(self.idx, "Ball of Everliving Golem")
        self.assertTrue(hits)
        self.assertTrue(hits[0]["held"])
        self.assertEqual(hits[0]["where"], "Equipment")

    def test_exact_item_match_ranks_first(self):
        hits = model.search(self.idx, "Ragebringer")
        self.assertEqual(hits[0]["item"], "Ragebringer")

    def test_blocked_results_rank_after_available(self):
        hits = model.search(self.idx, "Kunark") or model.search(self.idx, "Chardok")
        if hits:
            blocked = [i for i, h in enumerate(hits) if h["blocked"]]
            avail = [i for i, h in enumerate(hits) if not h["blocked"]]
            if blocked and avail:
                self.assertGreater(min(blocked), max(avail))



class TestItemNameMatching(unittest.TestCase):
    """The wiki and the game disagree on punctuation; matching must survive it.

    Reported by a player: epic items sitting in the bank were showing as not held.
    """

    def setUp(self):
        inv = {"counts": {"Slime Blood of Cazic-Thule": 1,
                          "Torn Page of Mastery Wind": 1,
                          "Al`Kabor's Cap of Binding": 1},
               "locations": {"Slime Blood of Cazic-Thule": {"Worn"},
                             "Torn Page of Mastery Wind": {"Bank"},
                             "Al`Kabor's Cap of Binding": {"Bank"}}}
        self.tr = model.Tracker(model.load_dataset(DATA), None, inv)

    def test_norm_item_ignores_punctuation(self):
        self.assertEqual(model.norm_item("Cazic-Thule"), model.norm_item("Cazic Thule"))
        self.assertEqual(model.norm_item("Mastery: Wind"), model.norm_item("Mastery Wind"))
        self.assertEqual(model.norm_item("Al`Kabor's"), model.norm_item("Al'Kabor's"))

    def test_hyphen_mismatch_still_counts_as_held(self):
        self.assertTrue(self.tr.held("Slime Blood of Cazic Thule"))

    def test_colon_mismatch_still_counts_as_held(self):
        self.assertTrue(self.tr.held("Torn Page of Mastery: Wind"))

    def test_backtick_apostrophe_mismatch_still_counts_as_held(self):
        self.assertTrue(self.tr.held("Al'Kabor's Cap of Binding"))

    def test_where_survives_punctuation_drift(self):
        self.assertEqual(self.tr.where("Slime Blood of Cazic Thule"), "Worn")

    def test_unrelated_item_is_still_not_held(self):
        self.assertFalse(self.tr.held("Something Nobody Owns"))



class TestIndexCache(unittest.TestCase):
    """The normalised lookup maps are cached; make sure they cannot go stale."""

    def test_replacing_inventory_rebuilds_the_cache(self):
        data = model.load_dataset(os.path.join(ROOT, "data", "sky.json"))
        tr = model.Tracker(data, {"classes": {}}, {"counts": {}, "locations": {}})
        self.assertFalse(tr.held("Efreeti Standard"))
        tr.inv = {"counts": {"Efreeti Standard": 3},
                  "locations": {"Efreeti Standard": {"Bank"}}}
        self.assertTrue(tr.held("Efreeti Standard"))
        self.assertEqual(tr.held_count("Efreeti Standard"), 3)
        self.assertEqual(tr.where("Efreeti Standard"), "Bank")


class TestAppIntegrity(unittest.TestCase):
    """Guards against edits that splice out a method still referenced by the UI.

    This has happened twice: a region replacement removed methods that lived
    between the two anchors, and the app only failed at launch. A bare
    `self._x` in a bind() or command= is easy to miss, so check those too.
    """

    @classmethod
    def setUpClass(cls):
        import re
        path = os.path.join(ROOT, "src", "eqlsky", "app.py")
        with open(path, encoding="utf-8") as fh:
            cls.src = fh.read()
        cls.re = re

    def test_no_referenced_method_is_missing(self):
        defined = set(self.re.findall(r"^    def (\w+)", self.src, self.re.M))
        assigned = set(self.re.findall(r"self\.(_\w+)\s*=", self.src))
        refs = set(self.re.findall(r"self\.(_[a-z]\w+)", self.src))
        missing = sorted(r for r in refs if r not in defined and r not in assigned)
        self.assertEqual(missing, [], "referenced but undefined: %s" % missing)

    def test_app_module_imports(self):
        import importlib
        mod = importlib.import_module("eqlsky.app")
        self.assertTrue(hasattr(mod, "App"))
        self.assertTrue(hasattr(mod, "main"))

if __name__ == "__main__":
    unittest.main(verbosity=2)
