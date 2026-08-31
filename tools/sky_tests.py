# -*- coding: utf-8 -*-
"""The 95 Plane of Sky class Tests (EverQuest Legends).

Format: (class, test name, wind rune suffix, [(component, source)], reward)
Source: https://eqlwiki.com/Plane_of_Sky
"""

TESTS = [
("Bard","Test of Tone","Meda",[("Light Woolen Mask","I3 Gorgalosk")],"Mask of Song"),
("Bard","Test of Voice","Kala",[("Light Woolen Mantle","I4 Keeper of Souls")],"Mantle of the Songweaver"),
("Bard","Test of Pitch","Azia",[("Crude Wooden Flute","I5 Spiroc Lord")],"Ervaj's Flute of Flight"),
("Bard","Test of Wind","Caza",[("Amulet of Woven Hair","I6 Bazzt Zzzt")],"Fae Amulet"),
("Bard","Test of Brass","Fana",[("Glowing Diamond","I7 Sister of the Spire"),("Efreeti War Horn","Efreeti cycle")],"Denon's Horn of Disaster"),
("Bard","Test of Harmony","Heda",[("Nebulous Diamond","I8 Eye of Veeshan"),("Efreeti War Spear","Efreeti cycle: Dojorn / Overseer only")],"Spear of Harmony"),

("Beastlord","Test of Aviak","Beza",[("Spiroc Elder's Totem","I5 Spiroc Lord")],"Spiroc Beak Earcuff"),
("Beastlord","Test of Azarack","Heda",[("Azarack Skin","I2 Protector of Sky")],"Azarack Skin Wristwraps"),
("Beastlord","Test of Claw","Izah",[("Sphinx Claw","I7 Sister of the Spire"),("Mithril Bands","I8 Eye of Veeshan"),("Brass Knuckles","Efreeti cycle")],"Windhowl and Spirit Render"),
("Beastlord","Test of Harpy","Kala",[("Leather Cord","I3 Gorgalosk")],"Griffon-Hide Armguards"),
("Beastlord","Test of Wind","Geza",[("Silken Wrap","I6 Bazzt Zzzt")],"Diaphonous Waistband"),

("Berserker","Test of Sharpness","Jaka",[("Djinni War Blade","I7 Sister of the Spire"),("Efreeti Standard","Efreeti cycle")],"Skycleaver"),
("Berserker","Test of Will","Ena",[("Pulsating Ruby","I6 Bazzt Zzzt")],"Molten Coil"),
("Berserker","Test of Ferocity","Ozah",[("High Quality Raiment","I5 Spiroc Lord")],"Sash of Ferocity"),
("Berserker","Test of Burden","Azia",[("Feathered Cape","I3 Gorgalosk")],"Shroud of the Sky"),
("Berserker","Test of Blood","Lena",[("Azarack Blood","I2 Protector of Sky")],"Blood-Drawn Runes"),
("Berserker","Test of Fools Errand","Dena",[("Jester's Mask","I4 Keeper of Souls"),("Efreeti Great Staff","I8 Eye of Veeshan")],"Cudgel of the Fool"),

("Cleric","Test of Courage","Lena",[("Silver Hoop","I3 Gorgalosk")],"Truewind Earring"),
("Cleric","Test of Skill","Meda",[("Small Shield","I4 Keeper of Souls")],"Aegis of the Wind"),
("Cleric","Test of Protection","Caza",[("Shiny Pauldrons","I5 Spiroc Lord")],"Pauldrons of Piety"),
("Cleric","Test of Resolution","Neza",[("Silvered Spiroc Necklace","I6 Bazzt Zzzt")],"Necklace of Resolution"),
("Cleric","Test of Theurgy","Kala",[("Djinni Aura","I7 Sister of the Spire"),("Efreeti Mace","Efreeti cycle")],"Theurgist's Star"),
("Cleric","Test of The Weak","Ena",[("Mithril Bands","I8 Eye of Veeshan"),("Efreeti Standard","Efreeti cycle")],"Baton of the Sky"),

("Druid","Test of Wolf","Meda",[("Worn Leather Mask","I3 Gorgalosk")],"Drake-Hide Mask"),
("Druid","Test of Bear","Kala",[("Mantle of Woven Grass","I4 Keeper of Souls")],"Nature Walker's Mantle"),
("Druid","Test of Tree","Azia",[("Spiroc Battle Staff","I5 Spiroc Lord"),("Efreeti Statuette","Efreeti cycle")],"Shillelagh"),
("Druid","Test of The Bee","Dena",[("Divine Honeycomb","I6 Bazzt Zzzt")],"Honeycomb Belt"),
("Druid","Test of Eagle","Ena",[("Ethereal Ruby","I7 Sister of the Spire"),("Spiroc Elder's Totem","I5 Spiroc Lord")],"Spiroc Banisher Focus"),
("Druid","Test of Nature","Izah",[("Storm Sky Opal","I8 Eye of Veeshan"),("Efreeti Scimitar","Efreeti cycle: Dojorn / Overseer only")],"Espri"),

("Enchanter","Test of Illusion","Meda",[("Finely Woven Cloth Cord","I3 Gorgalosk")],"Sphinx Hair Cord"),
("Enchanter","Test of Metamorphism","Ozah",[("Light Cloth Mantle","I4 Keeper of Souls")],"Wind Walker's Mantle"),
("Enchanter","Test of Deception","Beza",[("Silken Mask","I5 Spiroc Lord")],"Ivory Mask"),
("Enchanter","Test of Dislocation","Caza",[("Adamantium Earring","I6 Bazzt Zzzt")],"Earring of Displacement"),
("Enchanter","Test of Memorization","Fana",[("Glowing Necklace","I7 Sister of the Spire")],"Necklace of Whispering Winds"),
("Enchanter","Test of Incapacitation","Izah",[("Large Sky Sapphire","I8 Eye of Veeshan"),("Efreeti Wind Staff","Efreeti cycle")],"Rod of the Protecting Winds"),

("Magician","Test of Clarification","Lena",[("Feathered Cape","I3 Gorgalosk")],"Bracelet of Clarification"),
("Magician","Test of Empowerment","Neza",[("Ceramic Mask","I4 Keeper of Souls")],"Mask of Empowerment"),
("Magician","Test of Shielding","Azia",[("Golden Coffer","I5 Spiroc Lord")],"Gold White Pendant"),
("Magician","Test of Summoning","Dena",[("Large Diamond","I6 Bazzt Zzzt")],"Drake-Hide Amice"),
("Magician","Test of Interpretation","Ena",[("Golden Efreeti Ring","I7 Sister of the Spire")],"Duennan Shielding Ring"),
("Magician","Test of Gesticulation","Jaka",[("Hazy Opal","I8 Eye of Veeshan"),("Efreeti Magi Staff","Efreeti cycle: Dojorn / Overseer only")],"Staff of The Magister"),
("Magician","Test of Displacement","Heda",[("Crown of Elemental Mastery","I7 trash"),("Large Opal","I8 Eye of Veeshan"),("Djinni Stave","I7 Sister of the Spire")],"Staff of Elemental Mastery: Air"),

("Monk","Test of Strength","Caza",[("Silken Strands","I3 Gorgalosk")],"Back Straps of Mastery"),
("Monk","Test of Sight","Geza",[("Cracked Leather Eyepatch","I4 Keeper of Souls")],"Ton Po's Eye Patch"),
("Monk","Test of Speed","Jaka",[("Dove Slippers","I5 Spiroc Lord")],"Sandals of Alacrity"),
("Monk","Test of Tears","Beza",[("Silken Wrap","I6 Bazzt Zzzt")],"Ton Po's Shoulder Wraps"),
("Monk","Test of Fists","Neza",[("Nebulous Sapphire","I7 Sister of the Spire"),("Brass Knuckles","Efreeti cycle")],"Wu's Fist of Mastery"),
("Monk","Test of Tranquility","Lena",[("Tear of Quellious","I8 Eye of Veeshan")],"Golden Sash of Tranquility"),

("Necromancer","Test of Flight","Lena",[("Griffon's Beak","I3 Gorgalosk")],"Bloody Griffon-Hide Wrist Guard"),
("Necromancer","Test of Power","Neza",[("Black Silk Cape","I4 Keeper of Souls")],"Cloak of Spiroc Feathers"),
("Necromancer","Test of Mind","Ozah",[("Fine Cloth Raiment","I5 Spiroc Lord")],"Bloodsoaked Raiment"),
("Necromancer","Test of Heart","Azia",[("Pulsating Ruby","I6 Bazzt Zzzt")],"Sphinx Heart Amulet"),
("Necromancer","Test of Finger","Caza",[("Ring of Veeshan","I7 Sister of the Spire")],"Band of Wailing Winds"),
("Necromancer","Test of Hands","Fana",[("Gorgon Head","I3 Gorgalosk"),("Efreeti Great Staff","I8 Eye of Veeshan")],"Gorgon Head Staff"),

("Paladin","Test of Spirit","Lena",[("Ivory Sky Diamond","I5 Spiroc Lord")],"Girdle of Faith"),
("Paladin","Test of Sacrifice","Ozah",[("Bixie Sword Blade","I6 Bazzt Zzzt")],"Aldryn, Blade of the Ocean"),
("Paladin","Test of Love","Geza",[("Golden Hilt","I7 trash"),("Sphinx Claw","I7 Sister of the Spire")],"Thelvorn, Blade of Light"),
("Paladin","Test of Compassion","Izah",[("Large Sky Diamond","I8 Eye of Veeshan"),("Efreeti Zweihander","Efreeti cycle")],"Truvinan"),

("Ranger","Test of Body","Meda",[("Griffon Talon","I3 Gorgalosk")],"Griffon Talon Necklace"),
("Ranger","Test of Defense","Neza",[("Fine Velvet Cloak","I4 Keeper of Souls")],"Dark Cloak of the Sky"),
("Ranger","Test of The Earth","Kala",[("Spiroc Earth Totem","I5 Spiroc Lord")],"Earthshaker's Mantle"),
("Ranger","Test of Thunder","Azia",[("White Gold Earring","I6 Bazzt Zzzt")],"Thunderforged Earring"),
("Ranger","Test of Blade","Ena",[("Circlet of Brambles","I7 Sister of the Spire"),("Efreeti Long Sword","Efreeti cycle")],"Arydryidriyorn"),
("Ranger","Test of Ranged Attack","Heda",[("Shimmering Pearl","I8 Eye of Veeshan"),("Efreeti War Bow","Efreeti cycle")],"Windstriker"),

("Rogue","Test of Thievery","Ozah",[("Inlaid Choker","I3 Gorgalosk")],"Wispy Choker of Vigor"),
("Rogue","Test of Trickery","Izah",[("Sphinxian Circlet","I7 Sister of the Spire")],"Renard's Belt of Quickness"),
("Rogue","Test of Silence","Ena",[("Spiroc Sky Totem","I5 Spiroc Lord")],"Griffon Wing Spaulders"),
("Rogue","Test of Cunning","Dena",[("Jester's Mask","I4 Keeper of Souls")],"Crystal Mask"),
("Rogue","Test of Stealth","Geza",[("Fine Wool Cloak","I6 Bazzt Zzzt")],"Shimmering Bracer of Protection"),
("Rogue","Test of Deception","Jaka",[("Bixie Stinger","I6 Bazzt Zzzt"),("Bloodsky Sapphire","I8 Eye of Veeshan")],"Thornstinger"),

("Shadow Knight","Test of Bash","Ozah",[("Finely Crafted Amulet","I3 Gorgalosk")],"Amulet of the Sphinx Eye"),
("Shadow Knight","Test of Smash","Beza",[("Silvery Ring","I4 Keeper of Souls")],"Crimson Ring of the Djinni"),
("Shadow Knight","Test of Slash","Dena",[("Finely Woven Cloth Belt","I5 Spiroc Lord")],"Pegasus-Hide Belt"),
("Shadow Knight","Test of Disempowerment","Fana",[("Rusted Pauldrons","I6 Bazzt Zzzt")],"Blood Sky Face Plate"),
("Shadow Knight","Test of Envenoming","Heda",[("Efreeti War Shield","Efreeti cycle")],"Obtenebrate Mithril Guard"),
("Shadow Knight","Raising of the Dead","Izah",[("Sphinxian Ring","I7 Sister of the Spire"),("Fae Pauldrons","I8 Eye of Veeshan")],"Pearlescent Pauldrons"),
("Shadow Knight","Test of Necropotence","Kala",[("Blood Sky Ruby","I8 Eye of Veeshan"),("Efreeti War Axe","Efreeti cycle")],"Khyldorn the Blood Drinker"),

("Shaman","Test of Might","Meda",[("Leather Cord","I3 Gorgalosk")],"Amulet of the Fang"),
("Shaman","Test of Health","Kala",[("Ceremonial Belt","I5 Spiroc Lord")],"Bracelet of the Spirits"),
("Shaman","Test of Sight","Beza",[("Light Damask Mantle","I5 Spiroc Lord")],"Fairy-Hide Mantle"),
("Shaman","Test of Shrink","Ena",[("Corrosive Venom","I6 Bazzt Zzzt"),("Efreeti War Club","Efreeti cycle")],"Warhammer of the Wind"),
("Shaman","Test of Snake","Heda",[("Bixie Essence","I6 split bees (not the Queen)"),("Spiritualist's Ring","I7 Sister of the Spire")],"Vermilion Sky Ring"),
("Shaman","Test of The Witch Doctor","Geza",[("Symbol of Veeshan","I8 Eye of Veeshan"),("Efreeti War Maul","Efreeti cycle")],"Garduk"),

("Warrior","Test of Skill","Neza",[("Azure Ring","I3 Gorgalosk")],"Azure Ruby Ring"),
("Warrior","Test of Strength","Azia",[("Stone Amulet","I4 Keeper of Souls")],"Runed Wind Amulet"),
("Warrior","Test of Force","Beza",[("Spiroc Air Totem","I5 Spiroc Lord")],"Pauldrons of the Blue Sky"),
("Warrior","Test of Think","Fana",[("Wind Tablet","I6 Bazzt Zzzt"),("Efreeti Belt","Efreeti cycle: Dojorn / Hand only")],"Belt of the Four Winds"),
("Warrior","Test of Smash","Jaka",[("Djinni War Blade","I7 Sister of the Spire"),("Gem of Invigoration","I7 trash")],"Dagas"),
("Warrior","Test of Bash","Dena",[("Ethereal Emerald","I8 Eye of Veeshan"),("Efreeti Battle Axe","Efreeti cycle")],"Fangol"),

("Wizard","Test of Concentration","Dena",[("Grey Damask Cloak","I3 Gorgalosk")],"Augmentor's Mask"),
("Wizard","Test of Focus","Fana",[("Woven Skull Cap","I4 Keeper of Souls")],"Al'Kabor's Cap of Binding"),
("Wizard","Test of Meditation","Geza",[("High Quality Raiment","I5 Spiroc Lord")],"Raiment of Thunder"),
("Wizard","Test of Conception","Izah",[("Box of Winds","I6 Bazzt Zzzt"),("Efreeti Statuette","Efreeti cycle")],"Solidate Mithril Ring"),
("Wizard","Test of Visualization","Jaka",[("Amethyst Amulet","I7 Sister of the Spire")],"Amulet of the Void"),
("Wizard","Test of Preparation","Caza",[("Large Sky Lapis","I8 Eye of Veeshan"),("Efreeti War Staff","Efreeti cycle")],"Nargon's Staff"),
]
