# TODO

> **Done since this list was written:** search (v1.2.0), the double-click safety fix and the compact overlay (v1.5.0).

## Search — requested 2026-08-31

**Add search to both trackers: Plane of Sky and Epic Quests.**

Right now the only way to find something is to know which class or island it belongs to and
click through. With 95 Sky Tests plus 406 epic steps across 15 classes, that is the main
usability gap.

### What it should answer

| Question | Example |
|---|---|
| Where does this item come from? | type `Mithril Bands` → I8 Eye of Veeshan, needed by Cleric Test of The Weak and Beastlord Test of Claw |
| What does this mob drop that I need? | type `Phinigel` → Kedge Backbone (Bard epic), Blue Crystal Staff (Wizard epic), Staff of Elemental Mastery: Water (Magician epic), Robe of the Kedge (Rogue epic) |
| What can I get in this zone? | type `Plane of Hate` → every Sky and epic component sourced there |
| Do I already hold this? | any hit shows held / not held, and where it is |

### Design notes

- **One search box, both datasets.** A player does not think in terms of "the Sky tab" versus
  "the Epics tab" — they think "what is this item for". Results should be grouped by source
  dataset but come from a single query.
- Match against **item name, mob name, zone, class, and Test/step name**. Substring, case
  insensitive. Fuzzy matching is not needed; exact spellings come from the game.
- Show **held state** in results, since that is the point of the app.
- Clicking a result should jump to its class in the relevant tab and select it.
- Keyboard: `Ctrl+F` focuses the box, `Esc` clears it.
- A zone query is the highest-value case — it answers "I am going here anyway, what should I
  keep an eye out for", which currently requires reading the whole farming list.

### Implementation sketch

- Build a flat index once per reload in `model.py`: one record per
  `(dataset, class, step/test, item, mob, zone, held)`.
- Both `Tracker` and `EpicTracker` already expose everything needed; the index can be assembled
  from `farm_list()` / `steps_for()` without new parsing.
- New `Search` tab, or a search box in the toolbar that switches to a results view. A tab is
  simpler and avoids disturbing the existing layouts.
- Include search results in the PDF export only if asked — probably not by default.

---

## Done

- **Search** — shipped v1.2.0.
- **Double-click meant two different things** — navigate in Search, mutate saved state in the
  Farming List and epic pane. Mutation moved to Space and right-click in v1.5.0, so an
  impatient double tap can no longer write to your overrides.
- **Compact always-on-top mode** — shipped v1.5.0. Ctrl+M or the Compact button.

## Other candidates, not requested

- **App icon** — cosmetic; the exe currently uses the default PyInstaller icon.
- **Item page deep links** — several eqlwiki titles use backticks rather than apostrophes and
  one is lowercase, so links need a title-normalisation map. See `docs/AUDIT-2026-08-31.md`.
- **NO DROP / Attunable flag per component** — would tell you whether a guildmate can hand you
  an item. Data is not consistently published.
- **Kunark flip** — when Kunark launches, set `KUNARK_RELEASED = True` in
  `tools/build_epics.py`, rebuild the dataset and the exe. Nothing else changes.
