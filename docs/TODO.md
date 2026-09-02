# TODO

Shipped work lives in the release notes, not here. This file is only what is **not** done.

**Last reviewed:** 2026-09-02, at v1.6.0.

## Waiting on the game

| Item | Trigger | Work |
|---|---|---|
| **Kunark flip** | Ruins of Kunark (Patch 13) goes live | `KUNARK_RELEASED = True` in `tools/build_epics.py`, rebuild dataset + exe. Nothing else. `test_flipping_kunark_flag_unblocks_everything` covers it |
| **Epics flip** | Epics (Patch 18) goes live | `EPICS_RELEASED = True`, same rebuild. **Both flags must be true** before anything is completable |
| **Key ring for quest keys** | If Legends ever adds one | Players keep asking in General. Today only Equipment / Activated / Illusions / Familiars / Mounts / Teleportation / Hero's Forge have rings — quest keys bind individually |

## Real gaps

| Gap | Why it matters | Notes |
|---|---|---|
| **DPI robustness at 125% scaling** | Fixed pixel widths on the Treeview columns mean a 125% display can clip the right-hand columns. The dev machine runs at 100%, so this is unverified rather than known-broken | Fix is `ttk.PanedWindow` splits instead of fixed `width=` on the tree columns. The only item here previously called a *real* gap |
| **Epic dataset coverage is incomplete** | Recorded honestly in the app, but still a gap | Berserker 23 of ~41 steps · Shadow Knight 25 of 34 · Necromancer 22 of 30. eqlwiki's epic pages are largely unconverted classic-EQ content |
| **`NO DROP` / Attunable flag per component** | Would answer "can a guildmate hand me this?" | Data is not consistently published on the wiki |

## Cosmetic

| Item | Notes |
|---|---|
| **App icon** | The exe uses the default PyInstaller icon. Visible to every user; cheap to fix |
| **Item page deep links** | Several eqlwiki titles use backticks rather than apostrophes and one is lowercase, so links need a title-normalisation map. See `docs/AUDIT-2026-08-31.md` |

## Settled, do not redo

- **Settings migration from `%APPDATA%\EQLSkyTracker\`** — checked 2026-09-02. The old and new
  `settings.json` are identical and **no `overrides.json` exists in either**, so nothing is
  stranded. The old folder is dead weight, not lost data. Delete it or ignore it; there is
  nothing to migrate.
- **`app.py` size** (~1,600 lines). Splitting per tab is tidiness against the one file with no
  automated UI coverage, where region splices have twice deleted live methods. Not worth the
  risk without a reason beyond neatness. See `docs/AUDIT-CODE-2026-09-01.md`.
- **`test_status` redundant work** — ~1.7x, but a full `summary()` is 0.36 ms. Nothing to win.
