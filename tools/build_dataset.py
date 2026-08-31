"""Generate data/sky.json from the canonical Test table.

Source of truth: https://eqlwiki.com/Plane_of_Sky (EverQuest Legends).
Run:  python tools/build_dataset.py
"""
import json, os, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKY_PY = os.environ.get("SKY_TABLE")  # optional external table

TURNIN = {
    "Bard": "Cilin Spellsinger",
    "Beastlord": "Animist Kratho",
    "Berserker": "Stragen The Hewer",
    "Cleric": "Josin Faithbringer",
    "Druid": "Strandar Pinemist",
    "Enchanter": "Enchanter Jolas",
    "Magician": "Magus Frinon",
    "Monk": "Holwin",
    "Necromancer": "Drakis Bloodcaster",
    "Paladin": "Dason Goldblade",
    "Ranger": "Ranger Spirit",
    "Rogue": "Thalik Silenthand",
    "Shadow Knight": "Sarkis Ebonblade",
    "Shaman": "Medicine Man Veetra",
    "Warrior": "Torgon Blademaster",
    "Wizard": "Wizard Schrock",
}

# Achievement files spell it "Shadowknight"; the wiki uses "Shadow Knight".
ACH_ALIAS = {"Shadow Knight": "Shadowknight"}


# Reward names differ between eqlwiki and the in-game achievement file.
# Key = dataset/wiki name, value = achievement-file name.
REWARD_ALIAS = {
    "Fae Amulet": "Amulet of the Fae",
    "Griffon-Hide Armguards": "Griffin-Hide Armguards",
    "Staff of The Magister": "Staff of the Magister",
    "Al'Kabor's Cap of Binding": "Al`Kabor's Cap of Binding",
}

# Hail trigger word per test. Most match the test name; these do not.
TRIGGER_OVERRIDE = {
    ("Ranger", "Test of The Earth"): "elemental earth",
    ("Ranger", "Test of Thunder"): "elemental thunder",
    ("Berserker", "Test of Fools Errand"): "fools errand",
    ("Shaman", "Test of The Witch Doctor"): "witch doctor",
    ("Ranger", "Test of Ranged Attack"): "ranged attack",
    ("Cleric", "Test of The Weak"): "weak",
    ("Druid", "Test of The Bee"): "bee",
    ("Shadow Knight", "Raising of the Dead"): "raising of the dead",
}

# Wind Rune class restrictions (eqlwiki item pages). SHD = Shadow Knight.
RUNE_CLASSES = {
    "Azia": "WAR RNG DRU BRD NEC MAG BER",
    "Beza": "WAR SHD MNK SHM ENC BST",
    "Caza": "CLR MNK BRD NEC WIZ ENC",
    "Dena": "WAR SHD DRU ROG WIZ MAG BER",
    "Ena":  "CLR RNG DRU ROG SHM MAG BER",
    "Fana": "WAR SHD BRD NEC WIZ ENC",
    "Geza": "PAL MNK ROG SHM WIZ BST",
    "Heda": "RNG SHD BRD SHM MAG BST",
    "Izah": "PAL SHD DRU ROG WIZ ENC BST",
    "Jaka": "WAR MNK ROG WIZ BER",
    "Kala": "CLR RNG SHD DRU BRD SHM BST",
    "Lena": "CLR PAL MNK NEC MAG BER",
    "Meda": "BRD CLR DRU ENC RNG SHM",   # wiki page says NONE; derived from related quests
    "Neza": "WAR CLR RNG MNK NEC MAG",
    "Ozah": "PAL SHD ROG NEC ENC BER",
}
RUNE_UNVERIFIED = {"Meda"}

ISLANDS = [
    {"id": "I1",   "name": "Fairy Island",   "boss": "Thunder Spirit Princess",
     "needs_key": None, "yields": ["Key of Swords", "Key of the Misplaced"],
     "trash": ["a thunder spirit"],
     "notes": "Entry point. Fairies are NOT KOS - safe staging and buff area. Succor returns here. Good Wind Rune farm."},
    {"id": "I1.5", "name": "Noble Island",   "boss": "Noble Dojorn",
     "needs_key": "Key of Swords", "yields": [],
     "trash": ["a blade storm"],
     "notes": "TRAP: no keys drop here. Carry the Key of the Misplaced before entering. First boss of the Efreeti Cycle - killing Dojorn spawns Overseer of Air on Island 4. Blade storms assist."},
    {"id": "I2",   "name": "Azarack Island", "boss": "Protector of Sky",
     "needs_key": "Key of the Misplaced", "yields": ["Key of Misfortune"],
     "trash": ["an azarack"],
     "notes": "Initially aggressive. Azaracks are social - expect adds."},
    {"id": "I3",   "name": "Harpy Island",   "boss": "Gorgalosk",
     "needs_key": "Key of Misfortune", "yields": ["Key of Beasts"],
     "trash": ["a gorgalask", "a crystalline cloud", "a gust of wind", "a shimmering meteor",
               "an avenging gazer", "heart harpie", "a watchful guard", "a spirited harpie"],
     "notes": "Gorgalosk casts Stone Breath, a 12-15 second stun. Watchful guards and avenging gazers rarely cast Mana Detonation (knockback) - do not fight near the edge. Fighting inside the structure is safest."},
    {"id": "I4",   "name": "Pegasus Island", "boss": "Keeper of Souls",
     "needs_key": "Key of Beasts", "yields": ["Avian Key"],
     "trash": ["a soul carrier", "an essence carrier", "an essence tamer", "a soul harvester", "a soul tamer"],
     "notes": "Split mobs: each death spawns a replacement, so expect to tank two at once. Some proc a Whirl Till You Hurl stun that breaks tank aggro. Overseer of Air (Efreeti Cycle #2) also spawns here."},
    {"id": "I5",   "name": "Spiroc Island",  "boss": "The Spiroc Lord",
     "needs_key": "Avian Key", "yields": ["Key of the Swarm"],
     "trash": ["a spiroc arbiter", "a spiroc banisher", "a spiroc caller", "a spiroc expulser",
               "a spiroc revolter", "a spiroc walker", "a spiroc vanquisher"],
     "notes": "ENDLESSLY FARMABLE - respawns quickly. Kill a banisher, walker or revolter to spawn The Spiroc Guardian, which spawns The Spiroc Lord. Spirocs cast directional Dark Terror knockbacks - face the tank toward island centre."},
    {"id": "I6",   "name": "Bee Island",     "boss": "Bazzt Zzzt",
     "needs_key": "Key of the Swarm", "yields": ["Key of Scale"],
     "trash": ["Bzzazzt", "Bazzzazzt", "Bizazzt", "Bzzzt"],
     "notes": "Only a 1-SPLIT chains to the Queen: Bzzazzt -> Bazzzazzt -> Bzzzt (mini-queen) -> Bazzt Zzzt. A 2-split or 3-split dead-ends. Bees do not see invis but are social with a huge aggro radius; they proc ~100hp/tick poison DoTs. On a wipe the boss relocates to the previous mob's death spot."},
    {"id": "I7",   "name": "Drake Island",   "boss": "Sister of the Spire",
     "needs_key": "Key of Scale", "yields": ["Veeshan's Key"],
     "trash": ["a heartsbane drake", "a fatestealer drake", "a windrider drake", "a greater sphinx", "undine spirit"],
     "notes": "Highest-value single boss - the most Tests draw from her table. Clear greater sphinxes first, they aggro socially through walls. Windrider drakes cast gravity flux and will shoot you off the island."},
    {"id": "I8",   "name": "Veeshan Island", "boss": "Eye of Veeshan",
     "needs_key": "Veeshan's Key", "yields": [],
     "trash": [],
     "notes": "Final boss. 32,000 HP in a solo instance at difficulty 0. Spams lifetaps with unpredictable damage spikes and resists slow without mote-upgraded spells. The Hand of Veeshan (Efreeti Cycle #3) also spawns here - engage it at the north end to split it from the Eye."},
]

SOURCE_TO_ISLAND = {
    "I2 Protector of Sky": "I2", "I3 Gorgalosk": "I3", "I4 Keeper of Souls": "I4",
    "I5 Spiroc Lord": "I5", "I6 Bazzt Zzzt": "I6", "I7 Sister of the Spire": "I7",
    "I7 trash": "I7", "I8 Eye of Veeshan": "I8", "Efreeti cycle": "EFREETI",
    "Efreeti cycle: Dojorn / Overseer only": "EFREETI",
    "Efreeti cycle: Dojorn / Hand only": "EFREETI",
    "I6 split bees (not the Queen)": "I6",
    "Dojorn / Overseer only": "EFREETI",
}

KEYS = [
    # EQ Legends: island BOSSES drop the progression keys directly.
    # There is no Sirran the Lunatic and no token hand-in - that is classic-EQ
    # content still lingering on the wiki's Plane_of_Sky_Keys page.
    # Confirmed 2026-08 by a player: Sirran does not exist in Legends.
    {"key": "Key of Swords",        "from": "Thunder Spirit Princess (I1)", "to": "I1.5"},
    {"key": "Key of the Misplaced", "from": "Thunder Spirit Princess (I1)", "to": "I2"},
    {"key": "Key of Misfortune",    "from": "Protector of Sky (I2)",        "to": "I3"},
    {"key": "Key of Beasts",        "from": "Gorgalosk (I3)",               "to": "I4"},
    {"key": "Avian Key",            "from": "Keeper of Souls (I4)",         "to": "I5"},
    {"key": "Key of the Swarm",     "from": "The Spiroc Lord (I5)",         "to": "I6"},
    {"key": "Key of Scale",         "from": "Bazzt Zzzt (I6)",              "to": "I7"},
    {"key": "Veeshan's Key",        "from": "Sister of the Spire (I7)",     "to": "I8"},
]

ZONE = {
    "name": "Plane of Sky",
    "zone_short": "airplane",
    "entry": "Click the orb in East Freeport bay, on a rock at approximately -425, -1200.",
    "min_level": 46,
    "turnin_location": "Efreeti Chamber - north teleport pad on Island 1, approximately 1600, 520. Requires Efreeti's Key (free from the Key Master on Island 1, purchased once).",
    "efreeti_cycle": ["Noble Dojorn (I1.5)", "Overseer of Air (I4)", "The Hand of Veeshan (I8)"],
    "notes": [
        "Keys are permanent on the keyring once used - right-click to reclaim the inventory slot.",
        "Island bosses drop the progression keys directly. There is no token hand-in NPC in Legends.",
        "Boss NPCs no longer have a deathtouch in Legends.",
        "Turn-ins CONSUME the component - a shared item must be farmed once per Test that uses it.",
        "Wind Runes drop from all Sky mobs and are class-restricted.",
        "Completing a class's Sky Tests unlocks that class as a Primary Class option in loadouts.",
        "Farm components at D0 - difficulty scales random loot quality, not whether a named quest drop appears.",
        "Island jumps (one-way portals aside): 7->2 easiest, 4->2, 4->3, 6->5 hardest. Low gravity, no fall damage.",
        "Most boss-dropped components are NO DROP; Efreeti-cycle items are mostly Attunable and tradeable - so a guildmate can hand you an Efreeti item but not a boss component.",
        "There are no documented prerequisites between Tests within a class. The only ordering is physical: island access via the key chain.",
    ],
}


def load_tests():
    """The 95 Tests. (class, test, rune, [(component, source)], reward)"""
    from sky_tests import TESTS
    return TESTS


def main():
    sys.path.insert(0, HERE)
    tests = load_tests()
    by_class = collections.OrderedDict()
    for cls, name, rune, comps, reward in tests:
        trig = TRIGGER_OVERRIDE.get((cls, name))
        if not trig:
            trig = name.replace("Test of ", "").replace("The ", "").strip().lower()
        by_class.setdefault(cls, []).append({
            "test": name,
            "trigger": trig,
            "rune": "Wind Rune " + rune,
            "rune_classes": RUNE_CLASSES.get(rune, ""),
            "rune_unverified": rune in RUNE_UNVERIFIED,
            "reward": reward,
            "reward_alias": REWARD_ALIAS.get(reward),
            "components": [{"item": c, "source": s,
                            "island": SOURCE_TO_ISLAND.get(s, "?")} for c, s in comps],
        })

    classes = []
    for cls, ts in by_class.items():
        classes.append({
            "name": cls,
            "achievement_name": ACH_ALIAS.get(cls, cls),
            "turnin_npc": TURNIN[cls],
            "tests": ts,
        })

    data = {
        "schema": 1,
        "generated": "2026-08-31",
        "game": "EverQuest Legends",
        "source": "https://eqlwiki.com/Plane_of_Sky",
        "zone": ZONE,
        "islands": ISLANDS,
        "keys": KEYS,
        "classes": classes,
    }

    out = os.path.join(ROOT, "data", "sky.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)

    n_tests = sum(len(c["tests"]) for c in classes)
    n_comps = sum(len(t["components"]) for c in classes for t in c["tests"])
    print("wrote %s" % out)
    print("  classes: %d  tests: %d  component slots: %d" % (len(classes), n_tests, n_comps))


if __name__ == "__main__":
    main()
