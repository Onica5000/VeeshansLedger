# EQL Sky Tracker

[![Download](https://img.shields.io/badge/Download-EQLSkyTracker.exe-2ea44f?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/Onica5000/EQLSkyTracker/releases/latest/download/EQLSkyTracker.exe)
[![Latest release](https://img.shields.io/github/v/release/Onica5000/EQLSkyTracker?style=flat-square)](https://github.com/Onica5000/EQLSkyTracker/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/Onica5000/EQLSkyTracker/total?style=flat-square)](https://github.com/Onica5000/EQLSkyTracker/releases)
[![Licence](https://img.shields.io/github/license/Onica5000/EQLSkyTracker?style=flat-square)](LICENSE)

**Plane of Sky progress tracker for [EverQuest Legends](https://www.everquestlegends.com/).**
Tells you which class you're closest to unlocking, exactly what you still need, and which boss
drops it.

## ⬇️ Download

### **[Download EQLSkyTracker.exe](https://github.com/Onica5000/EQLSkyTracker/releases/latest/download/EQLSkyTracker.exe)**

That link always gives you the newest build. Single file, ~38 MB. No install, no Python,
nothing to configure — save it anywhere and double-click.

> **Windows will warn you on first run.** The exe isn't code-signed, so SmartScreen shows
> "Windows protected your PC". Click **More info → Run anyway**. This is expected for any
> unsigned hobby tool.

Or browse [all releases](https://github.com/Onica5000/EQLSkyTracker/releases).

> Completing a class's Plane of Sky Tests unlocks that class as a **Primary Class** option in
> your loadouts. This app exists to make that grind legible.

## Using it

**1. In game, run these two commands:**

```
/outputfile achievements
/outputfile inventory
```

Stand at a banker with the bank window open before the inventory one, or your bank contents
may be missing from the export.

**2. Run the exe.** It searches the registry and your drives for the EverQuest Legends folder
and asks you to confirm what it found. If it guesses wrong, point it at the folder yourself.

**3. Click Refresh** after any future export.

Everything stays on your machine. The app reads two local text files and stores your folder
choice in `%APPDATA%\EQLSkyTracker\`. Nothing is uploaded anywhere.

## What's in it

| Tab | What it answers |
|---|---|
| **Class Unlocks** | Which classes you're closest to unlocking. Click one for its remaining Tests, the hail word for each, the Wind Rune it needs, and which components you already hold |
| **Farming List** | Grouped by the boss that drops it — what to kill tonight, and which Test each drop feeds |
| **Zone Guide** | Island progression, which boss drops which key, and the mechanics that otherwise cost you a trip |
| **Setup & Help** | The `/outputfile` commands, folder detection, file freshness |

**Export PDF** produces a printable report — class progress, the farming list, or both.

Multiple characters exporting to the same folder are handled: files are paired by character, and
a picker appears when there's more than one.

## Things it knows that save you time

- **Turn-ins consume the component.** An item needed by two Tests must be farmed **twice** — the
  farming list marks those `x2`.
- **Wind Runes are class-restricted.** All 15 of them. Each Test shows which classes can loot its
  rune, so you know what to have in your loadout before you farm.
- **Your achievements file is the truth.** Rewards you sold, merged or destroyed still count
  toward the unlock, so completion is read from achievements, never from what's in your bags.
- **Island bosses drop the keys directly.** There is no token hand-in NPC in Legends.

## Data

16 classes · 95 Tests · 127 component slots.

Derived from [eqlwiki.com/Plane_of_Sky](https://eqlwiki.com/Plane_of_Sky) and the game's own
in-client help files, then audited field-by-field against the wiki's raw wikitext — see
[`docs/AUDIT-2026-08-31.md`](docs/AUDIT-2026-08-31.md) for what that found and fixed.

All quest data lives in [`data/sky.json`](data/sky.json). **Corrections are very welcome** — open
an issue. The wiki mixes live Legends data with unconverted classic-EQ pages, so if something
contradicts what you see in game, you're probably right and it's probably the wiki.

## Building from source

```
pip install -r requirements.txt
python tools/build_dataset.py     # regenerate data/sky.json
python build/build_exe.py         # -> dist/EQLSkyTracker.exe
python tests/test_core.py         # 14 regression tests
```

Requires Python 3.11+. **PyInstaller must be 6.22 or newer** — Python 3.14 ships Tcl/Tk 9.0 and
older PyInstaller versions produce an exe that dies at launch. The build script enforces this.

## Licence

MIT — see [LICENSE](LICENSE).

Not affiliated with Daybreak Game Company. EverQuest is a trademark of Daybreak Game Company LLC.
