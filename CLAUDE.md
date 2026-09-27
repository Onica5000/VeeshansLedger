# eql-sky-tracker — ships as **Veeshan's Ledger**

Windows desktop app (single `.exe`) tracking **Plane of Sky** class-unlock progress + the 15 **class epics** in **EverQuest Legends**.
Python 3.14 · tkinter · reportlab (PDF) · PyInstaller one-file. For the owner and guildmates — **character-agnostic**.
Public: [github.com/Onica5000/VeeshansLedger](https://github.com/Onica5000/VeeshansLedger) (latest v1.6.0, 2026-09-02). Folder name is the old one.

## Rules

| Rule | Detail |
|---|---|
| **Never hardcode a character, server or install path** | `find_installs()` searches registry + every drive, then the UI **asks the user to confirm** before saving — a user requirement |
| **The achievements export is the authority, not the inventory** | `Untapped Potential: Classes` in `<Char>_<server>-Achievements.txt` records what was **obtained** (sold/merged/destroyed rewards still count). Inventory only says which components are held. Inventory-only completion undercounts — cost a rewrite once |
| **Every storage location counts — never re-add a location filter** | Bank, Shared Bank, bags, Equipment, Augments, Key Ring, **Personal Depot**, **Dragon's Hoard**. Where it sits is display info, never a reason to ignore it |
| **`/outputfile` commands stay visible** | Setup tab, status bar, first-run dialog, PDF footer. Without them the app looks empty and gets blamed |
| **After editing `tools\`, regenerate** | `python tools\build_dataset.py` (and `build_epics.py`). `data\*.json` is derived — never hand-edit; stale is worse than none |
| **Data in JSON, not code** | Another zone must be addable without touching `src\` |
| **UI order: closest-to-unlocking first** | Deliberate. Never re-sort alphabetically |
| Windows-only calls (registry, `os.startfile`) | Fine, but guarded so the module imports elsewhere |

## Cleanup tab — the one feature that can lose someone's items

Acting on it is irreversible: **being unhelpful is cheap, being wrong is not.** An item is withheld if **any** holds:

| Withheld when | Why |
|---|---|
| An unfinished Test needs it | `outstanding` counts per Test — turn-ins consume, two Tests wanting one item need two |
| It's the reward of an unfinished Test | Not earned yet |
| **It appears anywhere in the epic data** | Blunt on purpose — no epic is completable, so a component is *early*, not spare |

- **Never phrase output as an instruction to destroy.** Say what's spare and why; the player decides. Banner + PDF carry the caution (duplicates are merge fuel; Exaltation sources).
- Every row shows its reason/blockers (`Keep N for <Test>`).
- `TestCleanup` covers the withholding rules — add a case before relaxing one.

## Build traps — `docs\build-traps.md` before debugging a build or writing smoke tooling

| Trap | One-line form |
|---|---|
| **PyInstaller ≥ 6.22** | Python 3.14 ships Tcl/Tk 9.0; older versions emit an unpopulated `_tcl_data` path and the exe dies at launch. Build script enforces it |
| **Smoke-test the WINDOW, not the process** | One-file exe spawns a GUI-owning *child*; a fatal-error dialog keeps the process alive. **Assert on the window title** — bit twice |
| **Delete `dist\VeeshansLedger.exe` before rebuilding** | A running instance locks it → `PermissionError: [WinError 5]`, easy to miss |

## Build, test, release

```
python -m unittest discover -s tests   # regression tests (tests\test_core.py)
python tools\build_dataset.py          # regenerate data\sky.json
python tools\build_epics.py            # regenerate data\epics.json
python build\build_exe.py              # -> dist\VeeshansLedger.exe (~38 MB)
```

Release asset must be named **`VeeshansLedger.exe`** — the README's download badge uses `releases/latest/download/VeeshansLedger.exe`.
Settings + manual overrides: `%APPDATA%\VeeshansLedger\`, never beside the exe.

## Name mismatches — check first when counts look wrong

Wiki and achievement file spell rewards differently. `REWARD_ALIAS` (`tools/build_dataset.py`) maps them; `Tracker.test_status` checks both. **A new alias has been the cause every time.**
Known: Fae Amulet↔Amulet of the Fae · Griffon-Hide↔Griffin-Hide Armguards · Staff of The Magister↔Staff of the Magister · Al'Kabor's (straight quote)↔Al\`Kabor's (backtick) · Shadow Knight↔Shadowknight.

## Epics — gated by content ERA, not zone

> **Nothing is completable yet.** EQL timeline: Kunark at **Patch 13**, Epics at **Patch 18**. Components that drop in original zones can be collected today — the Epics tab surfaces those and is honest about the rest.

- **The v1.1.0 mistake:** `Template:PageEra` sets `epics = out` / `epicquests = out` alongside `kunark = out`. An NPC in a Classic zone can still be out of era (General V`ghera, Kithicor Forest, Kunark Era). Check the entity's own era tag.
- Each step has `era`: `NOW` / `KUNARK` / `LATER` / `UNKNOWN`; `build_epics.py` → `blocked` via **both** `EPICS_RELEASED` and `KUNARK_RELEASED` (both `False` as of 2026-09-24).
- **When the eras land:** set both `True` in `tools/build_epics.py` → `python tools/build_epics.py` → `python build/build_exe.py`. No other code changes (`test_flipping_kunark_flag_unblocks_everything`).
- **Epic completion = inventory + manual ticks only** — the achievements file has **no epic entries** (verified 2026-08-31). Never claim "done", only "held"/"not held"; never infer completion.
- **Epic data is far weaker than Sky data** — eqlwiki epic pages are mostly unconverted classic EQ. Best-effort; keep `notes` honest.
- Epic overrides use the `epic_have:` prefix (Sky uses `have:`).

## Verified game facts — don't "correct" from classic-EQ sources

| Fact | Consequence |
|---|---|
| **Turn-ins consume the component** | Item feeding two Tests is farmed **twice**; `farm_list()` counts per Test |
| **Wind Runes are class-restricted** | 15 runes, shown per Test so the player knows which loadout to farm in |
| Completing a class's Tests unlocks it as a Primary Class | The app's reason to exist |
| **Shadow Knight has 7 Tests** | Six `Test of …` + `Raising of the Dead` → **95** total (a "Test of" regex gives 94) |
| **Beastlord Test of Claw awards TWO items** | Stored as `Windhowl and Spirit Render` — matches the achievement file |
| Island 4 boss is **Keeper of Souls** | Rendered wiki HTML garbles it — use raw wikitext |
| **No Sirran the Lunatic in Legends** | Island bosses drop keys directly; wiki `Plane_of_Sky_Keys` is stale classic content (removed 2026-08-31) |
| Efreeti Great Staff: **Eye of Veeshan only** | Item page `dropsfrom` beats prose on the Eye page |

## Inventory + key-ring parsing

| Fact | Detail |
|---|---|
| `CONTAINERS` / `WORN_SLOTS` (`parsers.py`) are **explicit allowlists** | Unrecognised locations report under their raw name, never absorbed into `Worn`. Past bugs: Depot skipped (holds epic gems/Metal Bits); Hoard mislabelled "Worn". `test_core` covers it |
| **`/outputfile inventory` writes a `KeyRing` header with no rows** | Empty = *not exported*, not *no keys*. Only record: chat-log line `<Key> has been added to your key ring` |
| `parsers.scan_keyring()` | Resumes from a cached byte offset — logs reach **450 MB+**. Bindings only append; a shrunk log is re-read |
| **Legends window is "Alt Storage"** | **EQ button > Inventory > Alt Storage** (`CMD_TOGGLE_KEYRINGS`), **no default keybind**. Never advise `/keyring` or `K` |

## Source hierarchy — resolve conflicts in this order

1. **A player who actually plays.** (Sirran sat in the dataset a day because two wiki pages disagreed; a player settled it in one sentence.)
2. **The game's own files** — `Help\*.html`, `uifiles\default\*`, `eqstr_us.txt`/`dbstr_us.txt`, `/outputfile` exports. ⚠️ **`eqlsnews.txt`/`eqnews.txt` are LIVE EverQuest's patch notes**, not Legends'. A string existing proves the *client* knows a feature, **not that Legends enables it** — check `CascadeMenu.txt`, the UI XML, and the chat log.
3. **An item page's structured field** (`dropsfrom`, `Class:`).
4. **Prose on a related page** — weakest.

Two wiki pages disagree → **say so in the output and pick one**; never ship both as alternatives.

## Layout

```
data\sky.json · epics.json   GENERATED - never hand-edit
tools\sky_tests.py           the 95 Tests: (class, test, rune, [(component, source)], reward)
tools\build_dataset.py       -> sky.json (+ REWARD_ALIAS)
tools\build_epics.py         -> epics.json (+ release flags); source epic_steps.txt
src\main.py                  entry point
src\eqlsky\parsers.py        reads the /outputfile exports + key-ring scan
src\eqlsky\model.py          joins dataset + exports; Tracker is the only public API
src\eqlsky\pdfout.py         reportlab reports
src\eqlsky\app.py            tkinter UI
build\build_exe.py           PyInstaller one-file build
tests\test_core.py           regression tests
docs\                        build-traps, TODO, dated audits
```
