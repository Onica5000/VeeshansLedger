"""Combines the static Sky dataset with a character's parsed export files."""
import json
import os
import collections

# The in-game commands that produce the files this app reads.
# Surfaced in the UI, the first-run screen and the PDF footer.
CMD_ACHIEVEMENTS = "/outputfile achievements"
CMD_INVENTORY = "/outputfile inventory"
COMMANDS = (CMD_ACHIEVEMENTS, CMD_INVENTORY)
COMMAND_HELP = (
    "In game, type these two commands, then click Refresh:\n"
    "    {}\n"
    "    {}\n\n"
    "Both write into your EverQuest Legends folder.\n"
    "Stand at a banker with the bank window open before running the inventory "
    "command, or bank contents may be missing."
).format(CMD_ACHIEVEMENTS, CMD_INVENTORY)

DONE, READY, PARTIAL, TODO = "done", "ready", "partial", "todo"

STATUS_LABEL = {
    DONE: "Complete",
    READY: "Ready to turn in",
    PARTIAL: "Components partly held",
    TODO: "Not started",
}


import re as _re

_PUNCT = _re.compile(r"[^a-z0-9]+")


def norm_item(name):
    """Loose key for matching item names across sources.

    The wiki and the game disagree on punctuation constantly - backtick vs
    apostrophe, "Cazic Thule" vs "Cazic-Thule", "Mastery: Earth" vs
    "Mastery Earth". Comparing on letters and digits alone stops those from
    silently reading as "not held", which is the worst failure this app has:
    it sends someone to farm what is already in their bank.
    """
    return _PUNCT.sub(" ", (name or "").lower().replace("’", "'")).strip()


def load_dataset(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


class Tracker:
    """The joined view: dataset + achievements + inventory + manual overrides."""

    def __init__(self, data, ach=None, inv=None, overrides=None):
        self.data = data
        self.ach = ach or {"classes": {}, "race_created": None, "races_unlocked": []}
        self.inv = inv or {"counts": {}, "locations": {}}
        self.overrides = overrides or {}

    # ---------- helpers ----------

    def _held_index(self):
        idx = getattr(self, "_hidx", None)
        if idx is None:
            idx = {norm_item(k): v for k, v in self.inv["counts"].items()}
            self._hidx = idx
        return idx

    def held(self, item):
        if self.overrides.get("have:" + item):
            return True
        if self.inv["counts"].get(item, 0) > 0:
            return True
        return self._held_index().get(norm_item(item), 0) > 0

    def held_count(self, item):
        return self.inv["counts"].get(item, 0)

    def where(self, item):
        loc = self.inv["locations"].get(item)
        if loc is None:
            key = norm_item(item)
            for k, v in self.inv["locations"].items():
                if norm_item(k) == key:
                    loc = v
                    break
        return ", ".join(sorted(loc or ()))

    def _ach_for(self, cls):
        rec = self.ach["classes"].get(cls["achievement_name"])
        if rec is None:
            rec = self.ach["classes"].get(cls["name"])
        return rec

    def has_achievements(self):
        return bool(self.ach["classes"])

    # ---------- per-test ----------

    def test_status(self, cls, test):
        """Return (status, held_components, missing_components)."""
        rec = self._ach_for(cls)
        obtained = None
        if rec:
            # The achievement file spells a handful of rewards differently.
            names = [test["reward"]]
            if test.get("reward_alias"):
                names.append(test["reward_alias"])
            for nm in names:
                if nm in rec["obtained"]:
                    obtained = True
                    break
                if nm in rec["missing"]:
                    obtained = False
                    break
        if obtained is None:
            # No achievement data - fall back to "is the reward in my inventory".
            obtained = self.held(test["reward"])
        if self.overrides.get("done:" + test["reward"]):
            obtained = True
        if obtained:
            return DONE, list(test["components"]), []

        have, need = [], []
        for c in test["components"]:
            (have if self.held(c["item"]) else need).append(c)
        if not need:
            return READY, have, need
        return (PARTIAL if have else TODO), have, need

    # ---------- per-class ----------

    def class_progress(self, cls):
        rec = self._ach_for(cls)
        total = len(cls["tests"])
        done = ready = 0
        for t in cls["tests"]:
            st = self.test_status(cls, t)[0]
            if st == DONE:
                done += 1
            elif st == READY:
                ready += 1
        return {
            "name": cls["name"],
            "npc": cls["turnin_npc"],
            "total": total,
            "done": done,
            "ready": ready,
            "remaining": total - done,
            "unlocked": bool(rec and rec["unlocked"]),
            "confirmed_primary": bool(rec and rec["confirmed_primary"]),
            "token_used": bool(rec and rec["token_used"]),
        }

    def all_progress(self):
        rows = [self.class_progress(c) for c in self.data["classes"]]
        # Unlocked last; then fewest remaining first - "closest to unlocking" on top.
        rows.sort(key=lambda r: (r["unlocked"], r["remaining"], r["name"]))
        return rows

    # ---------- farm list ----------

    def farm_list(self):
        """{island_id: [ {item, source, needed_by:[(class,test)], count} ]}"""
        want = collections.OrderedDict()
        for cls in self.data["classes"]:
            for t in cls["tests"]:
                st, have, need = self.test_status(cls, t)
                if st in (DONE, READY):
                    continue
                for c in need:
                    key = (c["island"], c["item"], c["source"])
                    want.setdefault(key, []).append((cls["name"], t["test"]))
        out = collections.OrderedDict()
        for (island, item, source), users in want.items():
            out.setdefault(island, []).append(
                {"item": item, "source": source, "needed_by": users, "count": len(users)})
        for rows in out.values():
            rows.sort(key=lambda r: (-r["count"], r["item"]))
        order = [i["id"] for i in self.data["islands"]] + ["EFREETI", "?"]
        return collections.OrderedDict(
            (k, out[k]) for k in sorted(out, key=lambda k: order.index(k) if k in order else 99))

    def island_by_id(self, iid):
        for i in self.data["islands"]:
            if i["id"] == iid:
                return i
        if iid == "EFREETI":
            return {"id": "EFREETI", "name": "Efreeti Cycle", "boss": " -> ".join(self.data["zone"]["efreeti_cycle"]),
                    "needs_key": None, "yields": [], "trash": [],
                    "notes": "Kill Noble Dojorn on Island 1.5 early in the trip so the Overseer is up by the time you reach Island 4."}
        return {"id": iid, "name": "Unknown", "boss": "?", "needs_key": None,
                "yields": [], "trash": [], "notes": ""}

    # ---------- summary ----------

    def summary(self):
        rows = self.all_progress()
        tests = [(c, t) for c in self.data["classes"] for t in c["tests"]]
        counts = collections.Counter(self.test_status(c, t)[0] for c, t in tests)
        items = sum(len(v) for v in self.farm_list().values())
        return {
            "classes_total": len(rows),
            "classes_unlocked": sum(1 for r in rows if r["unlocked"]),
            "tests_total": len(tests),
            "done": counts[DONE], "ready": counts[READY],
            "partial": counts[PARTIAL], "todo": counts[TODO],
            "items_to_farm": items,
        }


# ---------- manual overrides ----------

def overrides_path():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "VeeshansLedger")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "overrides.json")


def load_overrides():
    try:
        with open(overrides_path(), "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def save_overrides(data):
    try:
        with open(overrides_path(), "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1)
        return True
    except Exception:
        return False


def load_settings():
    try:
        p = os.path.join(os.path.dirname(overrides_path()), "settings.json")
        with open(p, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def save_settings(data):
    try:
        p = os.path.join(os.path.dirname(overrides_path()), "settings.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1)
        return True
    except Exception:
        return False


GAME_MARKERS = ("eqgame.exe", "eqclient.ini", "EverQuest.ico")
_SUBPATHS = [
    r"Daybreak Game Company\Installed Games\EverQuest Legends",
    r"Program Files\Daybreak Game Company\Installed Games\EverQuest Legends",
    r"Program Files (x86)\Daybreak Game Company\Installed Games\EverQuest Legends",
    r"Games\EverQuest Legends",
    r"EverQuest Legends",
]


def looks_like_install(path):
    """True if the folder contains recognisable EQ Legends client files."""
    if not path or not os.path.isdir(path):
        return False
    try:
        names = set(os.listdir(path))
    except OSError:
        return False
    if any(m in names for m in GAME_MARKERS):
        return True
    # An export file alone is good enough - that is all this app actually needs.
    return any(n.endswith(("-Achievements.txt", "-Inventory.txt")) for n in names)


def _drives():
    out = []
    if os.name == "nt":
        import string
        for letter in string.ascii_uppercase:
            root = "%s:\\" % letter
            if os.path.isdir(root):
                out.append(root)
    else:
        out.append("/")
    return out


def _from_registry():
    """Look for the install path in the Windows uninstall registry."""
    found = []
    if os.name != "nt":
        return found
    try:
        import winreg
    except ImportError:
        return found
    roots = [(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
             (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
             (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")]
    for hive, sub in roots:
        try:
            key = winreg.OpenKey(hive, sub)
        except OSError:
            continue
        try:
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    name = winreg.EnumKey(key, i)
                    with winreg.OpenKey(key, name) as k:
                        disp = ""
                        try:
                            disp = str(winreg.QueryValueEx(k, "DisplayName")[0])
                        except OSError:
                            pass
                        if "everquest" not in disp.lower():
                            continue
                        for val in ("InstallLocation", "InstallPath"):
                            try:
                                p = str(winreg.QueryValueEx(k, val)[0]).strip('"')
                            except OSError:
                                continue
                            if p and os.path.isdir(p):
                                found.append(p)
                except OSError:
                    continue
        finally:
            key.Close()
    return found


def find_installs(deep=False, progress=None):
    """Return a de-duplicated list of candidate EQ Legends folders, best first.

    Cheap by default: registry + well-known paths on every drive. With deep=True
    also walks a few levels of each drive, which is slower but catches odd installs.
    """
    seen, out = set(), []

    def add(p):
        if not p:
            return
        p = os.path.normpath(p)
        key = p.lower()
        if key in seen:
            return
        seen.add(key)
        if looks_like_install(p):
            out.append(p)

    for p in _from_registry():
        add(p)
        add(os.path.join(p, "EverQuest Legends"))

    for drive in _drives():
        for sub in _SUBPATHS:
            add(os.path.join(drive, sub))

    if deep:
        for drive in _drives():
            if progress:
                progress(drive)
            for root, dirs, _files in os.walk(drive):
                depth = root[len(drive):].count(os.sep)
                if depth >= 4:
                    dirs[:] = []
                    continue
                dirs[:] = [d for d in dirs if not d.startswith(("$", ".")) and
                           d.lower() not in ("windows", "node_modules", "appdata")]
                for d in list(dirs):
                    if "everquest" in d.lower():
                        add(os.path.join(root, d))
    return out


def guess_folder():
    hits = find_installs()
    return hits[0] if hits else ""


# ============================ epic quests ============================
#
# Epics are tracked differently to Sky Tests: the achievements export contains
# no epic entries (verified 2026-08-31), because class epics are not live in
# Legends yet. So "held" comes from the inventory export plus manual overrides,
# and completion is never inferred.

class EpicTracker:
    """Joins the epic dataset with a character's inventory and overrides."""

    def __init__(self, data, inv=None, overrides=None):
        self.data = data
        self.inv = inv or {"counts": {}, "locations": {}}
        self.overrides = overrides or {}

    # ---------- availability ----------

    @property
    def kunark_released(self):
        return bool(self.data["availability"]["kunark_released"])

    @property
    def epics_released(self):
        """Epics are their own content era in EQL and land AFTER Kunark."""
        return bool(self.data["availability"].get("epics_released"))

    def exception_note(self):
        return self.data["availability"].get("exception_note", "")

    def availability_note(self):
        return self.data["availability"]["note"]

    def data_warning(self):
        return self.data["availability"].get("data_warning", "")

    def completable_now(self):
        """Classes whose entire chain is reachable today."""
        return [c["name"] for c in self.data["classes"] if c.get("completable")]

    # ---------- helpers ----------

    def _held_index(self):
        idx = getattr(self, "_hidx", None)
        if idx is None:
            idx = {norm_item(k): v for k, v in self.inv["counts"].items()}
            self._hidx = idx
        return idx

    def held(self, item):
        if self.overrides.get("epic_have:" + item):
            return True
        if self.inv["counts"].get(item, 0) > 0:
            return True
        return self._held_index().get(norm_item(item), 0) > 0

    def where(self, item):
        loc = self.inv["locations"].get(item)
        if loc is None:
            key = norm_item(item)
            for k, v in self.inv["locations"].items():
                if norm_item(k) == key:
                    loc = v
                    break
        return ", ".join(sorted(loc or ()))

    def classes(self):
        return self.data["classes"]

    def by_name(self, name):
        return next((c for c in self.data["classes"] if c["name"] == name), None)

    # ---------- per class ----------

    def class_rows(self):
        """One row per class, ordered by how much is collectable right now."""
        rows = []
        for c in self.data["classes"]:
            now = [s for s in c["steps"] if s.get("zone_live")]
            got = [s for s in now if self.held(s["item"])]
            rows.append({
                "name": c["name"],
                "reward": c["reward"],
                "summary": c.get("summary", ""),
                "total": len(c["steps"]),
                "now": len(now),
                "held_now": len(got),
                "blocked": sum(1 for s in c["steps"] if s["blocked"]),
                "completable": c.get("completable", False),
                "zones_all_live": c.get("zones_all_live", False),
            })
        # Most still-collectable items first; that is the actionable end.
        rows.sort(key=lambda r: (-(r["now"] - r["held_now"]), r["name"]))
        return rows

    def steps_for(self, class_name, only_now=False):
        c = self.by_name(class_name)
        if not c:
            return []
        out = []
        for s in c["steps"]:
            if only_now and not s.get("zone_live"):
                continue
            d = dict(s)
            d["held"] = self.held(s["item"])
            d["where"] = self.where(s["item"])
            out.append(d)
        return out

    # ---------- shopping list ----------

    def shopping_list(self):
        """{zone: [ {item, mob, needed_by:[class], held} ]} for unblocked, unheld items."""
        want = {}
        for c in self.data["classes"]:
            for s in c["steps"]:
                if not s.get("zone_live") or self.held(s["item"]):
                    continue
                key = (s["zone"], s["item"], s["mob"])
                want.setdefault(key, []).append(c["name"])
        out = {}
        for (zone, item, mob), users in want.items():
            label = zone if zone and zone != "-" else "Crafted, purchased or summoned"
            out.setdefault(label, []).append(
                {"item": item, "mob": mob, "needed_by": sorted(set(users)),
                 "count": len(set(users))})
        for rows in out.values():
            rows.sort(key=lambda r: (-r["count"], r["item"]))
        return dict(sorted(out.items(), key=lambda kv: (-len(kv[1]), kv[0])))

    # ---------- summary ----------

    def summary(self):
        rows = self.class_rows()
        return {
            "classes": len(rows),
            "steps_total": sum(r["total"] for r in rows),
            "zone_live": sum(r["now"] for r in rows),
            "collectable_now": sum(r["now"] for r in rows),
            "held_now": sum(r["held_now"] for r in rows),
            "blocked": sum(r["blocked"] for r in rows),
            "kunark_released": self.kunark_released,
            "epics_released": self.epics_released,
            "completable": self.completable_now(),
            "zones_all_live": [c["name"] for c in self.data["classes"]
                               if c.get("zones_all_live")],
        }


# ============================ search ============================
#
# One index across BOTH datasets. A player does not think "Sky tab" vs "Epics
# tab" - they think "what is this item for", or "I am going to Plane of Hate,
# what should I watch for". So a single query spans everything.

SKY, EPIC = "Sky", "Epic"


def build_index(tracker=None, epics=None):
    """Flat searchable records across the Sky Tests and the epic chains."""
    rows = []

    if tracker is not None:
        for cls in tracker.data["classes"]:
            for t in cls["tests"]:
                status, have, need = tracker.test_status(cls, t)
                for c in t["components"]:
                    isl = tracker.island_by_id(c["island"])
                    zone = "%s %s" % (isl.get("id", ""), isl.get("name", ""))
                    if isl.get("boss"):
                        zone += " - " + isl["boss"]
                    rows.append({
                        "dataset": SKY,
                        "cls": cls["name"],
                        "context": t["test"],
                        "item": c["item"],
                        "mob": c["source"],
                        "zone": zone.strip(),
                        "held": tracker.held(c["item"]),
                        "where": tracker.where(c["item"]),
                        "blocked": False,
                        "note": "%s - turn in to %s" % (STATUS_LABEL[status],
                                                        cls["turnin_npc"]),
                        "done": status == DONE,
                    })

    if epics is not None:
        for cls in epics.data["classes"]:
            for s in cls["steps"]:
                rows.append({
                    "dataset": EPIC,
                    "cls": cls["name"],
                    "context": "step %s -> %s" % (s["step"], cls["reward"]),
                    "item": s["item"],
                    "mob": s["mob"],
                    "zone": s["zone"],
                    "held": epics.held(s["item"]),
                    "where": epics.where(s["item"]),
                    "blocked": s["blocked"],
                    "note": epics.data["eras"][s["era"]]["label"],
                    "done": False,
                })
    return rows


def search(index, query, fields=("item", "mob", "zone", "cls", "context")):
    """Case-insensitive substring match across the given fields.

    Every whitespace-separated term must match somewhere in the record, so
    "hate cloak" narrows rather than widens.
    """
    terms = [t for t in (query or "").lower().split() if t]
    if not terms:
        return []
    out = []
    for r in index:
        hay = " ".join(str(r.get(f, "")) for f in fields).lower()
        if all(t in hay for t in terms):
            out.append(r)

    def rank(r):
        # exact item-name hits first, then unheld before held, then blocked last
        exact = 0 if r["item"].lower() == query.strip().lower() else 1
        starts = 0 if r["item"].lower().startswith(terms[0]) else 1
        return (exact, starts, r["blocked"], r["held"], r["dataset"],
                r["cls"], r["item"])

    out.sort(key=rank)
    return out
