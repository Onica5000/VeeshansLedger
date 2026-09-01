# EQL Sky Tracker

[![Download](https://img.shields.io/badge/Download-EQLSkyTracker.exe-2ea44f?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/Onica5000/EQLSkyTracker/releases/latest/download/EQLSkyTracker.exe)
[![Latest release](https://img.shields.io/github/v/release/Onica5000/EQLSkyTracker?style=flat-square)](https://github.com/Onica5000/EQLSkyTracker/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/Onica5000/EQLSkyTracker/total?style=flat-square)](https://github.com/Onica5000/EQLSkyTracker/releases)
[![Licence](https://img.shields.io/github/license/Onica5000/EQLSkyTracker?style=flat-square)](LICENSE)

**Plane of Sky and class epic quest tracker for
[EverQuest Legends](https://www.everquestlegends.com/).**
Tells you which class you are closest to unlocking, exactly what you still need, and which boss
drops it - with a search box across everything.

## Download

### **[Download EQLSkyTracker.exe](https://github.com/Onica5000/EQLSkyTracker/releases/latest/download/EQLSkyTracker.exe)**

That link always gives you the newest build. Single file, ~38 MB. No install, no Python,
nothing to configure - save it anywhere and double-click.

> **Windows will warn you on first run.** The exe is not code-signed, so SmartScreen shows
> "Windows protected your PC". Click **More info -> Run anyway**. This is expected for any
> unsigned hobby tool.

Or browse [all releases](https://github.com/Onica5000/EQLSkyTracker/releases).

> Completing a class's Plane of Sky Tests unlocks that class as a **Primary Class** option in
> your loadouts. This app exists to make that grind legible.

## Quick start

1. **In game, run these two commands:**

   ```
   /outputfile achievements
   /outputfile inventory
   ```

   Stand at a banker with the bank window open before the inventory one, or your bank
   contents may be missing.

2. **Run `EQLSkyTracker.exe`.** It searches for your EverQuest Legends folder and asks you
   to confirm it. If it guesses wrong, use **Browse…** on the Setup & Help tab.

3. Click **Refresh** after any future export.

## What it shows

| Tab | Answers |
|---|---|
| **Class Unlocks** | Which classes you are closest to unlocking, how many Tests remain, who to turn each one in to, and exactly which components you still need |
| **Farming List** | Grouped by the boss that drops it — what to kill tonight and which Test each drop feeds |
| **Zone Guide** | Island progression, which boss drops which key, and the mechanics that will otherwise cost you a trip |
| **Epic Quests** | All 15 class epics, with every step marked collectable-now or blocked until Kunark |
| **Setup & Help** | The `/outputfile` commands, folder detection, and file freshness |

**Export PDF…** produces a printable report — Sky class progress, the Sky farming list, both, or the epic collect-now list.

## Things the app knows that will save you time

- **Turn-ins consume the component.** An item needed by two Tests must be farmed twice. The
  farming list shows `x2` where that applies.
- **Wind Runes are class-restricted.** Each Test shows which classes can loot its rune — put
  that class in your loadout before you farm.
- **Your achievements file is the truth.** Rewards you sold or merged away still count toward
  the unlock, so the app trusts achievements over your current bags.

## Privacy

Everything is local. The app reads two text files the game writes, and stores your folder
choice in `%APPDATA%\EQLSkyTracker\`. Nothing is sent anywhere.

## Building from source

```
python tools/build_dataset.py
python build/build_exe.py
```

Requires Python 3.11+ with `reportlab` and `pyinstaller`. Output: `dist/EQLSkyTracker.exe`.

## Epic quests — read this before you farm

**No class epic can be completed in EverQuest Legends yet, and Kunark launching will not change
that.** Epics are their own content era: the EQL timeline puts **Epics at Patch 18** and **Ruins
of Kunark at Patch 13**, so epics arrive *after* Kunark.

The wiki's `Template:PageEra` marks `epics` and `epicquests` as **out of era**, alongside
`kunark` and `velious`. Many epic NPCs and quest items are epic-era tagged and **do not exist
yet even in zones you can already walk into** — General V`ghera stands in Kithicor Forest, a
Classic zone, but is himself tagged Kunark Era.

So the Epic Quests tab is a **route-planning aid, not a shopping list**. It shows which steps sit
in zones that are reachable today (278 of 407), which is genuinely useful for planning, but a
reachable zone does not promise the item exists.

**One documented exception:** the Paladin prerequisite chain **SoulFire → Ghoulbane → Fiery
Avenger** is tagged Classic Era and carries a live EQL confirmation dated 2026-08-08, so it is
believed doable today. It needs Warmly Deepwater Knights and Plane of Sky Island 4 access. The
Fiery Defender chain that follows it is epic-era and is not available.

> **Corrected in v1.2.0.** v1.1.0 claimed Paladin and Rogue were completable today. That was
> wrong — see [`docs/AUDIT-EPICS-2026-08-31.md`](docs/AUDIT-EPICS-2026-08-31.md) for the full
> retraction and evidence. Apologies to anyone who started farming on it.

> **Data quality.** The Plane of Sky data was audited field-by-field and is solid. The epic data
> is weaker: eqlwiki's epic pages are largely unconverted classic-EQ content tagged Out of Era.
> Known gaps are listed in the audit. If the game disagrees with the app, the game is right.

When the eras land, two flags in `tools/build_epics.py` unblock everything.

## Privacy

Everything is local. The app reads two text files the game writes, and stores your folder
choice in `%APPDATA%\EQLSkyTracker\`. Nothing is sent anywhere.

## Building from source

```
python tools/build_dataset.py
python build/build_exe.py
```

Requires Python 3.11+ with `reportlab` and `pyinstaller`. Output: `dist/EQLSkyTracker.exe`.

## Epic quests and Kunark

**Kunark is not released in EverQuest Legends yet**, so most epic chains cannot be finished.
Two can: **Paladin** and **Rogue** run entirely through original zones and are completable
today. Every other epic still has components you can farm now and bank.

The Epic Quests tab defaults to *"show only what I can collect now"*, and marks the rest as
blocked rather than hiding it, so you can see what is waiting.

Of 406 epic steps across 15 classes, **281 are collectable today**.

> **Data quality warning.** Every epic page on eqlwiki carries the `{{Epics Era}}` tag — which
> the wiki itself defines as the last sub-era of Kunark. Those pages are largely unconverted
> classic-EQ content with a few live-EQ edits mixed in, and only a handful of lines carry
> Legends verification stamps. The Sky data is solid; **treat the epic data as a best-effort
> guide**. If the game disagrees with it, the game is right — please open an issue.

When Kunark launches, one flag in `tools/build_epics.py` unblocks everything.

## Data

Quest data is derived from [eqlwiki.com/Plane_of_Sky](https://eqlwiki.com/Plane_of_Sky) and the
game's own in-client help files. 16 classes, 95 Tests, 127 component slots.
