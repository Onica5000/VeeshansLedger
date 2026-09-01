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

# ---------------------------------------------------------------- the flag
KUNARK_RELEASED = False
KUNARK_NOTE = (
    "Kunark has not been released in EverQuest Legends yet, so most epic chains cannot be "
    "finished. Paladin and Rogue are the exceptions - both run entirely through original "
    "zones and can be completed today. Everything else has components you can collect now "
    "and bank until Kunark launches."
)
DATA_WARNING = (
    "Epic data quality warning: every epic page on eqlwiki carries the {{Epics Era}} tag, "
    "which the wiki itself defines as the last sub-era of Kunark. These pages are largely "
    "unconverted classic-EQ content with some live-EQ edits mixed in, and only a handful of "
    "lines carry Legends verification stamps. Treat this as a best-effort guide, not verified "
    "Legends fact - and if the game disagrees with it, the game is right."
)
CHECKED = "2026-08-31"
# --------------------------------------------------------------------------

ERAS = {
    "NOW": {
        "label": "Available now",
        "blurb": "Drops in an original (pre-Kunark) zone. You can farm this today.",
        "blocked": False,
    },
    "KUNARK": {
        "label": "Needs Kunark",
        "blurb": "Drops in a Kunark zone. Not reachable until Kunark launches.",
        "blocked": not KUNARK_RELEASED,
    },
    "LATER": {
        "label": "Later expansion",
        "blurb": "From an expansion after Kunark. Not reachable yet.",
        "blocked": True,
    },
    "UNKNOWN": {
        "label": "Unconfirmed",
        "blurb": "Source zone not established - treat with caution.",
        "blocked": False,
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
            "now": sum(1 for s in steps if s["era"] == "NOW"),
            "blocked": sum(1 for s in steps if s["blocked"]),
        }
        c["completable"] = c["counts"]["blocked"] == 0

    data = {
        "schema": 1,
        "generated": CHECKED,
        "game": "EverQuest Legends",
        "source": "https://eqlwiki.com/Class_Epic_Quest_List",
        "availability": {
            "kunark_released": KUNARK_RELEASED,
            "note": KUNARK_NOTE,
            "data_warning": DATA_WARNING,
            "checked": CHECKED,
            "how_to_update": ("Set KUNARK_RELEASED = True in tools/build_epics.py and re-run "
                              "it, then rebuild the exe."),
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
