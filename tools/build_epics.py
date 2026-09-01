"""Generate data/epics.json from tools/epic_steps.txt.

Source of truth: https://eqlwiki.com/Class_Epic_Quest_List and the per-class
`<Class>_Epic_Quest` pages on eqlwiki.

`epic_steps.txt` is pipe-delimited and hand-maintainable:

    CLASS: Cleric
    REWARD: Water Sprinkler of Nem Ankh
    SUMMARY: one line about how much is doable pre-Kunark
    step|item|from_mob|zone|era|notes
    1|Words of the Departed|a spectre|Kithicor Forest|NOW|any spectre

`era` is one of NOW / KUNARK / LATER / UNKNOWN.

*** WHEN KUNARK LAUNCHES ***
Set KUNARK_RELEASED = True below and re-run. Every KUNARK step flips from
"blocked" to actionable across the whole app - no other code changes needed.

Run:  python tools/build_epics.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(HERE, "epic_steps.txt")
OUT = os.path.join(ROOT, "data", "epics.json")

# ---------------------------------------------------------------- the flags
#
# CORRECTION 2026-08-31: epics are gated by CONTENT ERA, not by zone.
# eqlwiki's Template:PageEra sets   epics = out   epicquests = out
# alongside kunark = out and velious = out, while classic/fear/hate/hole/sky/
# paineel are "in". EQL's own EverQuest Timeline puts Epics at Patch 18
# (Sept-2000 equivalent) and Ruins of Kunark at Patch 13 - so epics arrive
# AFTER Kunark, not with it.
#
# Consequence: a live zone does NOT mean the component exists. Many epic
# quest-giver NPCs and quest items are themselves epic-era and simply are not
# in the game yet, even in zones you can walk into today.

EPICS_RELEASED = False      # flip when EQL reaches Patch 18 (Epics)
KUNARK_RELEASED = False     # flip when EQL reaches Patch 13 (Ruins of Kunark)

KUNARK_NOTE = (
    "No class epic can be completed yet. Epics are their own content era in EverQuest "
    "Legends and release AFTER Kunark - the EQL timeline puts Epics at Patch 18 and Ruins "
    "of Kunark at Patch 13. Many epic NPCs and quest items are epic-era tagged and do not "
    "exist yet even in zones you can already walk into."
)
DATA_WARNING = (
    "Epic data quality warning: eqlwiki's epic pages are largely unconverted classic-EQ "
    "content and are tagged Out of Era. The zone column below tells you whether the ZONE is "
    "live today - it does NOT promise the item or the NPC exists yet. Treat this as a "
    "planning aid for when epics arrive, not a shopping list you can complete now. If the "
    "game disagrees with it, the game is right."
)
EXCEPTION_NOTE = (
    "One documented exception: the Paladin prerequisite chain SoulFire -> Ghoulbane -> "
    "Fiery Avenger is tagged Classic Era and carries a live EQL confirmation dated "
    "2026-08-08, so it is believed doable today. It needs Warmly Deepwater Knights and "
    "Plane of Sky Island 4 access. The Fiery Defender chain that follows it is epic-era "
    "and is NOT available."
)
CHECKED = "2026-08-31"
ERAS = {
    "NOW": {
        "label": "Zone is live now",
        "blurb": ("The zone is in-era and reachable today. The epic ITEM may still not exist "
                  "- epic-era items and NPCs arrive with the Epics patch."),
        "blocked": not EPICS_RELEASED,
        "zone_live": True,
    },
    "KUNARK": {
        "label": "Zone needs Kunark",
        "blurb": "Kunark zone. Not reachable until Ruins of Kunark launches.",
        "blocked": not (KUNARK_RELEASED and EPICS_RELEASED),
        "zone_live": False,
    },
    "LATER": {
        "label": "Later expansion",
        "blurb": "From an expansion after Kunark. Not reachable yet.",
        "blocked": True,
        "zone_live": False,
    },
    "UNKNOWN": {
        "label": "Zone unconfirmed",
        "blurb": "Source zone not established - treat with caution.",
        "blocked": not EPICS_RELEASED,
        "zone_live": False,
    },
}

VALID = set(ERAS)


def parse(path):
    classes = []
    cur = None
    lineno = 0
    problems = []
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            lineno += 1
            line = raw.rstrip("\n").strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("CLASS:"):
                cur = {"name": line.split(":", 1)[1].strip(), "reward": "",
                       "summary": "", "steps": []}
                classes.append(cur)
                continue
            if cur is None:
                problems.append("line %d: data before any CLASS:" % lineno)
                continue
            if line.startswith("REWARD:"):
                cur["reward"] = line.split(":", 1)[1].strip()
                continue
            if line.startswith("SUMMARY:"):
                cur["summary"] = line.split(":", 1)[1].strip()
                continue
            if line.lower().startswith("step|"):
                continue                      # header row
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 5:
                problems.append("line %d: expected 5-6 fields, got %d: %.60s"
                                % (lineno, len(parts), line))
                continue
            step, item, mob, zone, era = parts[:5]
            notes = parts[5] if len(parts) > 5 else ""
            era = era.upper()
            if era not in VALID:
                problems.append("line %d: bad era %r for %r" % (lineno, era, item))
                era = "UNKNOWN"
            cur["steps"].append({
                "step": step,
                "item": item,
                "mob": mob,
                "zone": zone,
                "era": era,
                "blocked": ERAS[era]["blocked"],
                "zone_live": ERAS[era]["zone_live"],
                "notes": notes,
            })
    return classes, problems


def main():
    if not os.path.exists(SRC):
        sys.exit("Missing %s" % SRC)
    classes, problems = parse(SRC)
    for c in classes:
        steps = c["steps"]
        c["counts"] = {
            "total": len(steps),
            "now": sum(1 for s in steps if s.get("zone_live")),
            "blocked": sum(1 for s in steps if s["blocked"]),
        }
        # Nothing is "completable" until the Epics era lands, regardless of zones.
        c["completable"] = EPICS_RELEASED and c["counts"]["blocked"] == 0
        c["zones_all_live"] = all(s.get("zone_live") for s in steps)

    data = {
        "schema": 1,
        "generated": CHECKED,
        "game": "EverQuest Legends",
        "source": "https://eqlwiki.com/Class_Epic_Quest_List",
        "availability": {
            "kunark_released": KUNARK_RELEASED,
            "epics_released": EPICS_RELEASED,
            "exception_note": EXCEPTION_NOTE,
            "note": KUNARK_NOTE,
            "data_warning": DATA_WARNING,
            "checked": CHECKED,
            "how_to_update": ("In tools/build_epics.py set EPICS_RELEASED = True when EQL "
                              "reaches the Epics patch, and KUNARK_RELEASED = True when it "
                              "reaches Ruins of Kunark. Re-run the script, rebuild the exe."),
        },
        "eras": ERAS,
        "classes": classes,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)

    tot = sum(c["counts"]["total"] for c in classes)
    now = sum(c["counts"]["now"] for c in classes)
    print("wrote %s" % OUT)
    print("  classes: %d  steps: %d  collectable now: %d  blocked: %d"
          % (len(classes), tot, now, sum(c["counts"]["blocked"] for c in classes)))
    if problems:
        print("\n  %d PROBLEM(S):" % len(problems))
        for p in problems:
            print("   -", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
