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

    def held(self, item):
        if self.overrides.get("have:" + item):
            return True
        return self.inv["counts"].get(item, 0) > 0

    def held_count(self, item):
        return self.inv["counts"].get(item, 0)

    def where(self, item):
        return ", ".join(sorted(self.inv["locations"].get(item, ())))

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
    d = os.path.join(base, "EQLSkyTracker")
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
