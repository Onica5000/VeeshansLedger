"""Parsers for EverQuest Legends /outputfile exports.

Two files matter:
  <Char>_<server>-Achievements.txt  - authoritative for what has been OBTAINED
  <Char>_<server>-Inventory.txt     - what is currently HELD

The achievements file is the authority for Test completion, because it records
what you obtained, not what you still carry. Turn-ins consume components and
reward items can be sold or merged away, so inventory alone undercounts.
"""
import os
import re
import glob

# Achievements lines are "C\t" (complete) or "I\t" (incomplete) then tab-indented text.
_STATUS = re.compile(r"^([CI])\t+(.*)$")
_CLASS_HDR = "Primary Class Unlock - "
_RACE_HDR = "Race Unlock - "


def list_characters(folder):
    """Return [{'stem','character','server','achievements','inventory','mtime'}] in the folder.

    Files are grouped by the "<Character>_<server>" stem so a character's achievements
    are never paired with a different character's inventory.
    """
    if not folder or not os.path.isdir(folder):
        return []
    found = {}
    for kind, suffix in (("achievements", "-Achievements.txt"),
                         ("inventory", "-Inventory.txt")):
        for path in glob.glob(os.path.join(folder, "*" + suffix)):
            stem = os.path.basename(path)[:-len(suffix)]
            rec = found.setdefault(stem, {"stem": stem, "achievements": None,
                                          "inventory": None})
            rec[kind] = path
    out = []
    for stem, rec in found.items():
        char, server = (stem.split("_", 1) + [None])[:2] if "_" in stem else (stem, None)
        times = [os.path.getmtime(p) for p in (rec["achievements"], rec["inventory"]) if p]
        rec.update({"character": char, "server": server,
                    "mtime": max(times) if times else 0})
        out.append(rec)
    # Characters with both files first, then most recently exported.
    out.sort(key=lambda r: (r["achievements"] is None or r["inventory"] is None,
                            -r["mtime"]))
    return out


def find_exports(folder, prefer=None):
    """Return the export pair for one character.

    prefer: the "<Character>_<server>" stem to select. Falls back to the best
    candidate (both files present, most recently exported).
    """
    res = {"achievements": None, "inventory": None, "character": None,
           "server": None, "stem": None, "others": []}
    chars = list_characters(folder)
    if not chars:
        return res
    pick = None
    if prefer:
        pick = next((c for c in chars if c["stem"] == prefer), None)
    if pick is None:
        pick = chars[0]
    res.update({k: pick[k] for k in ("achievements", "inventory", "character",
                                     "server", "stem")})
    res["others"] = [c["stem"] for c in chars if c["stem"] != pick["stem"]]
    return res


def _read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read().splitlines()


def parse_achievements(path):
    """Return a dict describing class-unlock progress.

    {
      'classes': {name: {'unlocked': bool, 'confirmed_primary': bool,
                         'token_used': bool, 'obtained': set(), 'missing': set()}},
      'race_created': str|None,
      'races_unlocked': [str],
    }
    """
    out = {"classes": {}, "race_created": None, "races_unlocked": []}
    if not path or not os.path.isfile(path):
        return out

    section = None
    cur = None
    for raw in _read(path):
        if not raw.strip():
            continue
        if not raw.startswith(("C\t", "I\t")):
            section = raw.strip()
            cur = None
            continue
        m = _STATUS.match(raw)
        if not m:
            continue
        status, body = m.group(1), m.group(2).strip()

        if section == "Untapped Potential: Classes":
            if body.startswith(_CLASS_HDR):
                cur = body[len(_CLASS_HDR):].strip()
                out["classes"][cur] = {
                    "unlocked": status == "C",
                    "confirmed_primary": False,
                    "token_used": False,
                    "obtained": set(),
                    "missing": set(),
                }
                continue
            if cur is None:
                continue
            rec = out["classes"][cur]
            if body.startswith("Obtain "):
                item = body[len("Obtain "):].strip().rstrip(".")
                (rec["obtained"] if status == "C" else rec["missing"]).add(item)
            elif "chose to confirm your Primary Class" in body:
                rec["confirmed_primary"] = status == "C"
            elif "bypassed using a Primary Class Unlock Token" in body:
                rec["token_used"] = status == "C"

        elif section == "Untapped Potential: Races":
            if body.startswith(_RACE_HDR):
                cur = body[len(_RACE_HDR):].strip()
                if status == "C":
                    out["races_unlocked"].append(cur)
                continue
            if cur and "your character was created as" in body and status == "C":
                out["race_created"] = cur
    return out


_SUFFIX = re.compile(r"\s*\+\d+$")
_EXALT = re.compile(r"\s*\(Exaltation\)$")


def normalise_item(name):
    """Strip '+N' upgrade suffix and '(Exaltation)' marker to get the base item name."""
    name = _EXALT.sub("", name.strip())
    name = _SUFFIX.sub("", name)
    return name


def parse_inventory(path):
    """Return {'counts': {base_item: n}, 'locations': {base_item: set(area)}}.

    Personal Depot rows are excluded - those are tradeskill materials, never quest
    components, and including them only creates false matches.
    """
    out = {"counts": {}, "locations": {}}
    if not path or not os.path.isfile(path):
        return out
    lines = _read(path)
    for raw in lines[1:]:
        parts = raw.split("\t")
        if len(parts) < 2:
            continue
        loc, name = parts[0].strip(), parts[1].strip()
        if not name or name in ("Empty", "Name"):
            continue
        if loc.startswith("Personal-Depot"):
            continue
        base = normalise_item(name)
        out["counts"][base] = out["counts"].get(base, 0) + 1
        area = ("Bank" if loc.startswith("Bank")
                else "Shared Bank" if loc.startswith("SharedBank")
                else "Bags" if loc.startswith("General")
                else "Equipment" if loc.startswith("Equipment")
                else "Augments" if loc.startswith("Augmentation")
                else "Worn")
        out["locations"].setdefault(base, set()).add(area)
    return out


def file_age(path):
    """Human-readable modification time, or None."""
    if not path or not os.path.isfile(path):
        return None
    import datetime
    return datetime.datetime.fromtimestamp(os.path.getmtime(path))
