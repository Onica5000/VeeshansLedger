# Epic Quest Audit — 2026-08-31

Two independent adversarial research passes against **eqlwiki raw wikitext**. One was asked to
attack the Paladin/Rogue completability claim specifically; the other audited the remaining 13
classes for gaps.

## The headline: a shipped claim was wrong, and has been retracted

**v1.1.0 told players:**

> "Paladin (Fiery Defender) and Rogue (Ragebringer) are completable today, because every step
> runs through original pre-Kunark zones."

**That is false.** The zone research was correct — there is not a single Kunark or Velious zone
in either chain — but the *conclusion* was wrong, because **EQL does not gate epics by zone. It
gates them by content era.**

### The evidence

`Template:PageEra` is the wiki's machine-readable in/out switch:

```
classic = in    fear = in     hate = in
hole    = in    sky  = in     paineel = in
kunark  = out   velious = out
epics   = out   epicquests = out      <-- every epic chain lands here
```

The `EverQuest Timeline` page gives EQL's intended progression:

| Patch | Milestone | Status |
|---|---|---|
| 0 | Server launch | live 2026-07-28 |
| 4 / 7 / 10 / 11 | Fear, Solusek Ro, **Plane of Sky**, **Paineel** | live at launch |
| **13** | **Ruins of Kunark** | not yet |
| 15 | The Hole, Veeshan's Peak | The Hole live at launch |
| **18** | **Epics released** | not yet |
| 21 | Scars of Velious | not yet |

**Epics are Patch 18. Kunark is Patch 13.** Epics arrive *after* Kunark, so "blocked until
Kunark" was backwards — Kunark landing does not unlock epics. The `Class Epic Quest List` page
says the same in prose: *"Class epic quests were introduced shortly after the release of
Kunark."*

### Non-zone blockers — the failure mode that broke the claim

An NPC can be out of era while standing in a zone you can walk into today:

| Entity | Zone | Era tag |
|---|---|---|
| **General V`ghera** (Rogue, steps 11–12) | Kithicor Forest — Classic | **Kunark Era** |
| **Vilnius the Small** (Rogue, both auxiliary chains) | West Karana — Classic | **Kunark Era** |
| **Kurron Ni** (Shadow Knight, chain start) | The Overthere | **Kunark Era** |
| Malka Rale, Eldreth, Yendar Starpyre, Renux Herkanor, Jark, Kirak Vil | various Classic zones | Epics Era |
| Irak Altil, Keeper of the Tombs | Plane of Fear, The Hole | EpicQuests Era |

### The one part that survives

**SoulFire → Ghoulbane → Fiery Avenger** is tagged `{{Classic Era}}` and carries a live EQL
confirmation dated **2026-08-08**. That prerequisite chain is believed doable today. It needs
Warmly Deepwater Knights and Plane of Sky Island 4 access. The **Fiery Defender** chain that
consumes it is epic-era and is not available.

This is now surfaced in the app as an explicit exception rather than a blanket claim.

## Data corrections applied

| Class | Step | Was | Now |
|---|---|---|---|
| Bard | Mystical Lute Head | available | **blocked** — needs Petrified Werewolf Skull (Karnor's Castle) |
| Bard | Mystical Lute | available | **blocked** — needs the Old Sebilis strings |
| Berserker | Gnashing Kobold Paw | Kunark | **zone live** — Stonebrunt Mountains is Classic on the Zones page |
| Cleric | Blood Soaked Plasmatic Priest Robe | unknown | **blocked** — Temple of Solusek Ro *is* Classic, but the step is gated on the Coral Statue from Timorous Deep |
| Shadow Knight | Darkforge Breastplate / Greaves / Helm | unknown | **zone live** — `Darkforge Armor Quests` is tagged `{{Classic Era}}`; undead knights in the Temple of Solusek Ro, needs Decayed Armor from Cazic Thule |
| Shadow Knight | Corrupted Ghoulbane | available | **blocked** — Duriek only corrupts it after the Letter from Kurron Ni |
| Shadow Knight | *(new step)* Letter to Duriek | — | added: Kurron Ni, The Overthere |

### Shadow Knight — a second refuted claim

v1.1.0 said a player could arrive at Kunark launch holding all four final turn-in items. They
cannot: `Corrupted Ghoulbane` is gated at the start on Kurron Ni in The Overthere. **Three** of
the four are reachable — Heart of the Innocent, Head of the Valiant, Will of Innoruuk.

## Confirmed correct

- Every zone in the Paladin and Rogue chains really is Classic — the zone data was right.
- Temple of Solusek Ro, Stonebrunt Mountains, The Hole, Paineel, The Warrens, and all three
  Planes are **Classic** on the Zones page.
- Timorous Deep and Emerald Jungle are **Kunark** — they gate Cleric, Monk, Necromancer, Ranger,
  Warrior, Druid, Berserker and Shaman steps.
- Green Dragon Scales (Warrior) really has **no** classic source — Severilous or Hoshkar only.
- Jade Reaver (Druid, Ranger) is genuinely Kunark-only.
- Ornate Velium Pendant (Wizard) is correctly tagged Velious.
- Wizard's chain really is 14 steps — the low count was not an omission.

## Known gaps — not fixed, recorded honestly

| Class | Have | Wiki | Note |
|---|---:|---:|---|
| **Berserker** | 23 | ~41 | Worst gap. Its page uses a plain-text `[ ]` checklist rather than `{{CheckboxList}}` — the whole Trial of Mastery wave event in Warsliks Woods is missing (~9 steps). Every missing step is Kunark-gated anyway |
| **Shadow Knight** | 25 | 34 | Missing the Cough Elixir pair and the optional Kastane seal chain |
| **Necromancer** | 22 | 30 | Missing part of the Plane of Sky cloak sub-chain |
| Druid / Ranger | 47 / 42 | ~53 / ~47 | Shared Shiny Tin Bowl and Runecrested Bowl chains |
| Magician / Cleric / Shaman / Warrior / Monk / Bard | — | — | 1–3 steps each |

Also unresolved: the Ranger and Wizard pages each carry **two** `{{CheckboxList}}` blocks, and
the Wizard's second is a stale pre-revamp variant routing through Cazic's Skin. The dataset
follows the post-revamp path.

## Method note

Both passes classified zones against the wiki's own `Zones` page, which has explicit
`Classic` / `Kunark (Out of Era)` / `Velious (Out of Era)` sections, rather than from memory.
That is the right primary source and should be used for any future zone question.

**The deeper lesson:** zone availability is necessary but not sufficient. Always check the
entity's own era tag — `Template:PageEra` is authoritative and machine-readable.
