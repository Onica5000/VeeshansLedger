# Code audit — 2026-09-01

Scope: `src/eqlsky/` (app, model, parsers, pdfout), `tools/`, `build/`, `tests/`.
3,571 lines. Everything below was measured or reproduced, not inferred.

## Defects found and fixed

### 1. Search index took 137 ms — 400x slower than every other hot path

Measured over 20 iterations against the live export:

| call | before | after |
|---|---|---|
| `farm_list()` | 0.17 ms | 0.17 ms |
| `all_progress()` | 0.11 ms | 0.11 ms |
| `summary()` | 0.36 ms | 0.36 ms |
| `epic shopping()` | 0.55 ms | 0.55 ms |
| **`build_index()`** | **137.16 ms** | **2.01 ms** |

`cProfile` named the cause: 852,209 calls to `re.sub`, all from `norm_item()`.
`where()` normalised **every** inventory location on every lookup miss — the
punctuation fallback added in v1.3.0 shipped without an index behind it, and
`Tracker` and `EpicTracker` each carried their own copy of the bug.

Fixed by extracting `_InventoryView`, which builds the normalised `counts` and
`locations` maps **once per tracker**. Both trackers now inherit it; two
duplicated blocks went away with it. Results are byte-identical (72 done,
24 to farm, 31 epic items held).

The cache is keyed on `id(self.inv)` so replacing the inventory rebuilds it.
Trackers are constructed fresh on every reload today, so this is belt-and-braces
against a future in-place swap serving stale counts. Pinned by a test.

### 2. Stacked items were counted as one

`parse_inventory()` added 1 per row and ignored column 4, `Count`. The live
export has 23 stacked rows; 448 Bone Chips — a real epic component — read as 1.

Fixed to use the stack size, falling back to 1 on an unparsable value.
Class-unlock and farm totals are unchanged (nothing currently outstanding asks
for more than one of a stackable), but displayed quantities are now correct.

### 3. A failed settings write lost the user's work silently

`save_overrides()` and `save_settings()` return a bool that all eight call sites
discarded. On a read-only or full `%APPDATA%`, manual "I have this" marks and
the confirmed game folder vanished at exit with no indication.

Both now route through `_save_overrides()` / `_save_settings()`, which warn
**once** — repeating the dialog on every click would be worse than silence.

### 4. A corrupt bundle died in a raw traceback

`epics.json` was guarded as optional; `sky.json` was not. Now it reports what
failed and suggests re-downloading, instead of a stack trace.

### 5. The epic tab advertised a binding that was removed on purpose

The hint label read "Double-click a step to mark the item as held." Only
`<space>` and `<Button-3>` were bound.

My first instinct was to add the missing `<Double-1>` binding. That was wrong:
`665eb1b` deliberately removed double-click mutation everywhere, because
double-click meant *navigate* in Search but *write to your overrides* in the
other two panes. The defect is the stale label, not a missing binding.

Label corrected to "Select a step and press Space, or right-click it".
Double-click still means navigate, everywhere.

### 6. A manual farm mark could not be undone the way its own row said

Manual rows render at tree root and read "double-click to undo". `_toggle_have`
rejected root rows outright, and no double-click was bound — so the only way out
was *Clear all overrides*. Rows now resolve through a map and the hint reads
"press Space to undo", matching the binding that exists.

### 7. Display text was parsed back into data

`_toggle_epic_have`, `_epic_menu`, `_toggle_have` and `_farm_menu` recovered item
names by string-slicing the rendered line (`"[x] 3 Item"` → `split(None, 1)[1]`).
That is correct only while every step label stays a single whitespace-free token.
It holds for all 57 current labels — verified — but it is a silent-corruption trap:
a label like `"3 (alt)"` would write overrides under a truncated key.

Replaced with `_epic_lines` / `_farm_items` maps populated during render. The
display format and the data model are no longer coupled.

## Reviewed, no change needed

- **Ten `except Exception` handlers.** Six are genuine boundaries where failure
  does not matter (dark title bar, `os.startfile`, destroying the overlay,
  remembering geometry, settings/overrides IO). Two were the defects above.
  None mask a logic error.
- **No unclosed file handles** anywhere in `src/`, `tools/`, `build/`.
- **`asksaveasfilename`** prompts natively on overwrite; the PDF path is fine.
- **`find_exports()`** groups by `<Char>_<server>` stem, so a character's
  achievements can never be paired with another character's inventory.
- **`build_exe.py`** enforces `PyInstaller >= 6.22` — below that, Python 3.14's
  Tcl/Tk 9.0 layout produces an exe that dies at launch.

## Known, deliberate, unchanged

- `app.py` is 1,512 lines — by far the largest module. Splitting it per tab is
  the obvious move, but it is the file with no automated UI coverage, and region
  splices have twice deleted live methods here. Not worth the risk without a
  reason beyond tidiness.
- `test_status` does about 1.7x redundant work (475 calls where ~285 is the
  floor). At 0.36 ms for a full `summary()` there is nothing to win.

## Verification

41 tests pass (3 added: stack sizes, an unparsable count, cache invalidation).
`TestAppIntegrity` still catches any `self._x` reference with no definition
behind it. Exe rebuilt and smoke-tested by window title and `PrintWindow`
capture on the Epic Quests and Farming List tabs — no synthetic input.
