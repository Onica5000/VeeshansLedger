# eql-sky-tracker &mdash; ships as **Veeshan's Ledger**

| | |
|---|---|
| **What** | Windows desktop app (single `.exe`) that tracks **Plane of Sky** class-unlock progress in **EverQuest Legends** |
| **Stack** | Python 3.14 · tkinter · reportlab (PDF) · PyInstaller (one-file build) |
| **Ships as** | `dist\VeeshansLedger.exe` — no install, no Python needed on the target machine |
| **Audience** | The owner and their guildmates. **Character-agnostic** — never hardcode a character, server or folder |

## The one thing to understand

**The achievements export is the authority, not the inventory.**

`Untapped Potential: Classes` in `<Char>_<server>-Achievements.txt` records what the character
has **obtained**. Rewards that were sold, merged or destroyed still count toward the unlock.
Inventory is used *only* to work out which quest components are currently held.

Deriving completion from inventory alone undercounts — that mistake cost a rewrite once already.

## Verified game facts baked into the data

These were confirmed against `eqlwiki.com` raw wikitext and the in-game help files. Do not
"correct" them from classic-EQ sources — Legends differs.

| Fact | Consequence |
|---|---|
| **Turn-ins consume the component** | An item feeding two Tests must be farmed **twice**. `farm_list()` counts per Test, not per item |
| **Wind Runes are class-restricted** | 15 runes, each usable by a subset of classes. Shown per Test so a player knows which loadout to wear while farming |
| **Completing a class's Tests unlocks it as a Primary Class** | This is the app's whole reason to exist |
| **Shadow Knight has 7 Tests** | Six `Test of …` plus `Raising of the Dead`. A regex counting only "Test of" gives 94 instead of the correct **95** |
| **Beastlord Test of Claw awards TWO items** | Windhowl *and* Spirit Render, a primary/secondary H2H pair. Stored as the single string `Windhowl and Spirit Render`, which also matches the achievement file exactly |
| Island 4 boss is **Keeper of Souls** | Rendered wiki HTML garbles it into "King of Storms/Sky/Spades" — use raw wikitext |
| **No Sirran the Lunatic in Legends** | Island bosses drop the progression keys directly. `Plane_of_Sky_Keys` still describes a token hand-in to Sirran — that is stale classic-EQ content and was shipped in error. Removed 2026-08-31 |
| Efreeti Great Staff drops from **Eye of Veeshan only** | The item page's `dropsfrom` is authoritative; a prose note on the Eye page claiming Noble Dojorn also drops it is the weaker source (audit 2026-08-31) |

## Epic quests - and the Kunark gate

The app also tracks the 15 **class epic quests**. The organising fact:

> **Kunark is not released in EverQuest Legends yet, so no epic weapon can be completed.**
> Many components drop in original zones and can be collected today. The Epics tab exists to
> surface exactly those, and to be honest about the rest.

Every step carries an `era`: `NOW` (original pre-Kunark zone), `KUNARK`, `LATER`, or `UNKNOWN`.
`build_epics.py` turns `era` into a `blocked` boolean using the release flag.

### Zone availability is NOT the same as item availability

**The mistake that shipped in v1.1.0.** Epics are gated by **content era**, not by zone.
`Template:PageEra` on eqlwiki sets `epics = out` and `epicquests = out` alongside
`kunark = out`; the EQL timeline puts Epics at **Patch 18** and Kunark at **Patch 13**, so
epics arrive AFTER Kunark. An NPC can stand in a Classic zone and still be out of era -
General V`ghera is in Kithicor Forest and tagged Kunark Era.

Always check the entity's own era tag, not just its zone. There are two flags now:
`EPICS_RELEASED` and `KUNARK_RELEASED`, and both must be true before anything is completable.

### When the eras land

1. Set `EPICS_RELEASED = True` (and `KUNARK_RELEASED = True`) in `tools/build_epics.py`
2. `python tools/build_epics.py`
3. `python build/build_exe.py`

Every `KUNARK` step unblocks across the tab, the shopping list and the PDF. **No other code
changes.** `test_flipping_kunark_flag_unblocks_everything` covers this.

### Epic tracking differs from Sky tracking

| | Sky Tests | Epics |
|---|---|---|
| Completion source | **Achievements export** (authoritative) | **Inventory + manual ticks only** |
| Why | `Untapped Potential: Classes` records what was obtained | The achievements file contains **no epic entries at all** - verified 2026-08-31, because epics are not live |

So the app never claims an epic step is "done" - only "held" or "not held". Do not add inferred
completion here; there is no data to infer it from.

**Epic data is far weaker than Sky data.** eqlwiki's epic pages are largely unconverted classic
EQ content. Treat the dataset as a best-effort guide, not verified Legends fact, and keep the
`notes` field honest about it.

Epic overrides use the `epic_have:` key prefix so they never collide with Sky's `have:`.

## Name mismatches — the recurring trap

The wiki and the achievement file spell several rewards differently. `REWARD_ALIAS` in
`tools/build_dataset.py` maps them, and `Tracker.test_status` checks both. When counts look
wrong, **check for a new alias first** — that has been the cause every time.

Known: Fae Amulet↔Amulet of the Fae · Griffon-Hide↔Griffin-Hide Armguards ·
Staff of The Magister↔Staff of the Magister ·
Al'Kabor's (straight quote)↔Al\`Kabor's (backtick) · Shadow Knight↔Shadowknight.

## Source hierarchy - the wiki is not uniformly current

`eqlwiki.com` mixes live Legends data with unconverted classic-EQ pages, and it contradicts
itself. Resolve conflicts in this order:

1. **A player who actually plays the game.** Sirran the Lunatic was in the dataset for a day
   because two wiki pages disagreed and the conflict was documented rather than resolved.
   A player settled it in one sentence.
2. **The game's own files** - `Help\*.html` and the `/outputfile` exports.
3. **An item page's structured field** (`dropsfrom`, `Class:`).
4. **Prose on a related page.** Weakest. The Efreeti Great Staff source was widened wrongly on
   the strength of a sentence on the Eye of Veeshan page.

When two wiki pages disagree, **say so in the output and pick one** - do not ship both as
though they were alternatives. A tracker that lists a non-existent NPC sends someone hunting.

## Layout

```
data\sky.json           GENERATED - the dataset. Do not hand-edit
tools\sky_tests.py      the 95 Tests: (class, test, rune, [(component, source)], reward)
tools\build_dataset.py  turns the above + islands/keys/NPCs/runes into sky.json
src\main.py             entry point
src\eqlsky\parsers.py   reads the two /outputfile exports
src\eqlsky\model.py     joins dataset + exports; Tracker is the only public API
src\eqlsky\pdfout.py    reportlab reports (classes / farm / both)
src\eqlsky\app.py       tkinter UI
build\build_exe.py      PyInstaller one-file build
```

**After editing `tools\`, re-run `python tools\build_dataset.py`.** `data\sky.json` is derived;
a stale dataset is worse than none.

## Rules

1. **Never hardcode a character, server or install path.** `find_installs()` searches the
   registry and every drive, then the UI **asks the user to confirm** before saving. That
   confirmation step is a user requirement, not a nicety.
2. **The `/outputfile` commands must stay visible.** They appear on the Setup tab, in the
   status bar, in the first-run dialog and in the PDF footer. A user who does not know to run
   them sees an empty app and blames it.
3. **Data lives in JSON, not in code.** Another zone should be addable without touching `src\`.
4. UI ordering is deliberate: **closest-to-unlocking first**, because the original reports were
   comprehensive but had no actionable order. Do not re-sort alphabetically.
5. Windows-only assumptions are fine (registry, `os.startfile`), but keep them guarded so the
   module still imports elsewhere.


## Build traps (both cost real time - do not rediscover)

**PyInstaller must be >= 6.22.** Python 3.14 ships **Tcl/Tk 9.0**, whose library lives in
`C:\Python314\tcl\libtcl9.0.4.zip` rather than the old `tcl8.6\` directory tree.
PyInstaller <= 6.20 emits a `_tcl_data` path it never populates, and the built exe dies at
launch with:

```
Failed to execute script 'pyi_rth__tkinter' ... Tcl data directory "...\_MEI...\_tcl_data" not found
```

6.22.2 detects Tcl 9 correctly (`tcl_data_missing: False`, zero separate data files - the DLL
loads its own zip). The build script enforces this version floor and refuses to run below it.

**Smoke-testing a one-file build: check the WINDOW, not the process.** Two traps here:

1. A PyInstaller one-file exe spawns a **child** process that owns the GUI. Enumerating windows
   for the pid returned by `Start-Process` finds nothing. Match on the process *name* instead.
2. "Process still alive after N seconds" passes even when the app is showing a fatal-error
   dialog - that dialog is what keeps it alive. **Assert on the window title.** This bit twice:
   once on the Tcl/Tk 9 crash, and again when a screenshot script reported "captured" for six
   tabs that were all the crash dialog. Any capture or smoke tooling MUST check the title text,
   not merely that a window exists.

```powershell
$t = @(Get-Process VeeshansLedger | ? {$_.MainWindowTitle} | % {$_.MainWindowTitle})
if ($t -match "Veeshan") { "PASS" } else { "FAIL" }
```

If a build fails mysteriously, rebuild with `--console` instead of `--windowed` - the traceback
goes to stdout instead of a dialog.

**Delete `dist\VeeshansLedger.exe` before rebuilding.** A still-running instance locks it and
PyInstaller fails with `PermissionError: [WinError 5]`, which is easy to miss in the log tail.

## Build

```
python tools\build_dataset.py     # regenerate data
python build\build_exe.py         # -> dist\VeeshansLedger.exe  (~38 MB)
```

Settings and manual overrides live in `%APPDATA%\VeeshansLedger\`, never beside the exe.
