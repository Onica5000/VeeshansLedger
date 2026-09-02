# Veeshan's Ledger

[![Download](https://img.shields.io/badge/Download-VeeshansLedger.exe-2ea44f?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/Onica5000/VeeshansLedger/releases/latest/download/VeeshansLedger.exe)
[![Latest release](https://img.shields.io/github/v/release/Onica5000/VeeshansLedger?style=flat-square)](https://github.com/Onica5000/VeeshansLedger/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/Onica5000/VeeshansLedger/total?style=flat-square)](https://github.com/Onica5000/VeeshansLedger/releases)
[![Licence](https://img.shields.io/github/license/Onica5000/VeeshansLedger?style=flat-square)](LICENSE)

**Plane of Sky and class epic quest tracker for
[EverQuest Legends](https://www.everquestlegends.com/).**

Reads the two text files the game already writes and tells you which class you are closest to
unlocking, exactly what you still need, and which boss drops it — with one search box across
everything.

## Download

### **[Download VeeshansLedger.exe](https://github.com/Onica5000/VeeshansLedger/releases/latest/download/VeeshansLedger.exe)**

Always the newest build. Single file, ~38 MB. No install, no Python, nothing to configure —
save it anywhere and double-click.

> **Windows will warn you on first run.** The exe is not code-signed, so SmartScreen shows
> "Windows protected your PC". Click **More info → Run anyway**. Expected for any unsigned
> hobby tool.

Or browse [all releases](https://github.com/Onica5000/VeeshansLedger/releases).

> **Upgrading from 1.5.0 or earlier?** Versions before 1.5.1 skipped the tradeskill depot
> entirely and mislabelled Dragon's Hoard items as "worn", so held counts could be too low.
> Re-run the two `/outputfile` commands and hit **Refresh**.

> Completing a class's Plane of Sky Tests unlocks that class as a **Primary Class** option in
> your loadouts. This app exists to make that grind legible.

## Quick start

**1. In game, run these two commands:**

```
/outputfile achievements
/outputfile inventory
```

Stand at a banker with the bank window open before the inventory one, or your bank contents may
be missing from the export.

**2. Run the exe.** It searches the registry and your drives for the EverQuest Legends folder
and asks you to confirm what it found. If it guesses wrong, point it at the folder yourself.

**3. Click Refresh** after any future export.

## What it shows

| Tab | What it answers |
|---|---|
| **Search** | One box across the Sky Tests and all 15 epic chains. Item, mob, zone, class or step. `Ctrl+F` from anywhere |
| **Class Unlocks** | Which classes you are closest to unlocking, their remaining Tests, hail words, Wind Rune, and which components you hold |
| **Farming List** | Grouped by the boss that drops it, with `x2` where an item feeds two Tests |
| **Zone Guide** | Island progression, which boss drops which key, and the mechanics that otherwise cost you a trip |
| **Epic Quests** | All 15 class epics, every step marked by whether its zone is reachable today |
| **Cleanup** | What you no longer need, so you can clear your bags without guessing |
| **Setup & Help** | The `/outputfile` commands, folder detection, file freshness |

To mark something as already held, select it and press **Space**, or right-click it. Double-click
always means "show me more", never "change my data".

**Compact mode** (`Ctrl+M`) opens a small always-on-top window with just what is actionable —
what is ready to turn in, what you are closest to, and the most-wanted drops. Meant to sit in a
corner while you play.

**Export PDF** produces printable reports — Sky progress, the Sky farming list, both, or the
epic planning list.

### Search is the quickest way in

| Type this | Get |
|---|---|
| `Phinigel` | The four different epics that need something off him |
| `Plane of Hate` | Everything worth watching for before you go |
| `Mithril Bands` | Both Sky Tests that need it, and that you need two |

Results show whether you already hold it and where. Double-click to jump to that class.

## Things it knows that save you time

- **Turn-ins consume the component.** An item needed by two Tests must be farmed **twice** — the
  farming list marks those `x2`.
- **Wind Runes are class-restricted.** All 15. Each Test shows which classes can loot its rune.
- **Your achievements file is the truth.** Rewards you sold, merged or destroyed still count
  toward the unlock, so Sky completion is read from achievements, never from your bags.
- **Island bosses drop the keys directly.** There is no token hand-in NPC in Legends.
- **Item names are matched loosely.** The wiki and the game disagree on punctuation constantly —
  `Cazic-Thule` vs `Cazic Thule`, `Mastery: Wind` vs `Mastery Wind` — so matching ignores it.
- **Stacks count as stacks.** A stack of 448 Bone Chips reads as 448, not as one item.
- **Every storage location is searched** — bank, shared bank, bags, equipment, augments, key
  ring, the **tradeskill depot** and the **Dragon's Hoard** — and each item says which one it is
  in. Anything the app doesn't recognise is reported under its own name rather than quietly
  filed as "worn", so a storage type added by a future patch can't hide from you.

## Cleaning out your bags

The **Cleanup** tab lists every item you hold that nothing outstanding still wants, with the
reason and where it is. Filter it, or print it as a checklist.

It is deliberately cautious. An item stays off the list while **any** unfinished Test needs it,
while it is the reward of a Test you have not finished, or while it appears **anywhere in the
epic data** — no epic is completable yet, so an epic component is not spare, it is early.

Where you need to keep some but not all, it says so: *"Keep 1 for Cleric — Test of The Weak.
The Tests you have left need 1; you hold 2."*

> **It will never tell you to destroy anything.** Duplicates are merge fuel in Legends, and an
> item can be the source of an Exaltation — not needed for a quest is not the same as worthless.
> The tab tells you what is spare and why; the decision stays yours.

**Sky keys are a special case.** Once a key binds to your key ring it is permanent, and the copy
in your bags does nothing. The inventory export doesn't list key ring contents, so the app reads
your chat log for the binding message instead. Confirm in game under **EQ button → Inventory →
Alt Storage** — in EverQuest Legends the window is called *Alt Storage*, not Key Rings, and it
has no default keybind.

## Epic quests — read this before you farm

**No class epic can be completed in EverQuest Legends yet, and Kunark launching will not change
that.** Epics are their own content era: the EQL timeline puts **Epics at Patch 18** and **Ruins
of Kunark at Patch 13**, so epics arrive *after* Kunark.

The wiki's `Template:PageEra` marks `epics` and `epicquests` as **out of era**, alongside
`kunark` and `velious`. Many epic NPCs and quest items are epic-era tagged and **do not exist yet
even in zones you can already walk into** — General V\`ghera stands in Kithicor Forest, a Classic
zone, but is himself tagged Kunark Era.

So the Epic Quests tab is a **route-planning aid, not a shopping list**. It shows which steps sit
in zones reachable today (278 of 407), which is genuinely useful, but a reachable zone does not
promise the item exists.

**One documented exception:** the Paladin prerequisite chain **SoulFire → Ghoulbane → Fiery
Avenger** is tagged Classic Era and carries a live EQL confirmation dated 2026-08-08, so it is
believed doable today. It needs Warmly Deepwater Knights and Plane of Sky Island 4 access. The
Fiery Defender chain that follows it is epic-era and is not available.

> **Corrected in v1.2.0.** An earlier release claimed Paladin and Rogue were completable today.
> That was wrong — see [`docs/AUDIT-EPICS-2026-08-31.md`](docs/AUDIT-EPICS-2026-08-31.md) for the
> full retraction and evidence.

> **Data quality.** The Plane of Sky data was audited field-by-field and is solid. The epic data
> is weaker: eqlwiki's epic pages are largely unconverted classic-EQ content tagged Out of Era.
> Known gaps are listed in the audit. If the game disagrees with the app, the game is right —
> please open an issue.

When the eras land, two flags in `tools/build_epics.py` unblock everything.

## Privacy

Everything is local. The app reads two text files the game writes and stores your folder choice
in `%APPDATA%\VeeshansLedger\`. Nothing is uploaded anywhere.

## Building from source

```
pip install -r requirements.txt
python tools/build_dataset.py     # regenerate data/sky.json
python tools/build_epics.py       # regenerate data/epics.json
python build/build_exe.py         # -> dist/VeeshansLedger.exe
python -m unittest discover -s tests   # 54 regression tests
```

Requires Python 3.11+. **PyInstaller must be 6.22 or newer** — Python 3.14 ships Tcl/Tk 9.0 and
older versions produce an exe that dies at launch. The build script enforces this.

## Data

**Plane of Sky:** 16 classes · 95 Tests · 127 component slots.

**Epics:** 15 classes · 407 steps · 278 in zones reachable today.

Derived from [eqlwiki.com](https://eqlwiki.com/Plane_of_Sky) and the game's own in-client help
files, then audited against the wiki's raw wikitext — see
[`docs/AUDIT-2026-08-31.md`](docs/AUDIT-2026-08-31.md) and
[`docs/AUDIT-EPICS-2026-08-31.md`](docs/AUDIT-EPICS-2026-08-31.md). The code itself was audited
separately — [`docs/AUDIT-CODE-2026-09-01.md`](docs/AUDIT-CODE-2026-09-01.md) covers a 68x search
regression, stack counting, and a silent save failure.

All quest data lives in [`data/`](data/). **Corrections are very welcome** — open an issue. The
wiki mixes live Legends data with unconverted classic-EQ pages, so if something contradicts what
you see in game, you are probably right.

## Licence

MIT — see [LICENSE](LICENSE).

Not affiliated with Daybreak Game Company. EverQuest is a trademark of Daybreak Game Company LLC.
