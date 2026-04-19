"""
Hero release order and wave information for Marvel Champions: The Card Game.
Source: Fantasy Flight Games product page & Wikipedia.
Order is chronological by release date.

is_legacy follows the pack_legacy field from the marvelcdb.com API.
Core Set heroes and Wave 8+ hero packs are Current (False).
Wave 1–7 hero packs are Legacy (True).
"""

# (hero_name, wave_label, release_index, is_legacy)
# release_index is 1-based chronological order across all products.
# Campaign boxes are grouped with their corresponding hero-pack wave.
HERO_RELEASE_DATA = [
    # Wave 1: Core Box + Hero Packs (2019-2020)
    ("Spider-Man (Peter)",         "Core Box — Wave 1",     1,  False),  # Core Set (current)
    ("Captain Marvel",             "Core Box — Wave 1",     2,  False),  # Core Set (current)
    ("Iron Man",                   "Core Box — Wave 1",     3,  False),  # Core Set (current)
    ("Black Panther (T'challa)",   "Core Box — Wave 1",     4,  False),  # Core Set (current)
    ("She-Hulk",                   "Core Box — Wave 1",     5,  False),  # Core Set (current)
    ("Captain America",            "Core Box — Wave 1",     6,  True),   # Hero pack (legacy)
    ("Ms. Marvel",                 "Core Box — Wave 1",     7,  True),   # Hero pack (legacy)
    ("Thor",                       "Core Box — Wave 1",     8,  True),   # Hero pack (legacy)
    ("Black Widow",                "Core Box — Wave 1",     9,  True),   # Hero pack (legacy)
    ("Doctor Strange",             "Core Box — Wave 1",    10,  True),   # Hero pack (legacy)
    ("Hulk",                       "Core Box — Wave 1",    11,  True),   # Hero pack (legacy)
    # Wave 2: Rise of Red Skull + Hero Packs (2020-2021) — all Legacy
    ("Hawkeye",                    "Rise of Red Skull — Wave 2", 12, True),
    ("Spider-Woman",               "Rise of Red Skull — Wave 2", 13, True),
    ("Ant-Man",                    "Rise of Red Skull — Wave 2", 14, True),
    ("Wasp",                       "Rise of Red Skull — Wave 2", 15, True),
    ("Quicksilver",                "Rise of Red Skull — Wave 2", 16, True),
    ("Scarlet Witch",              "Rise of Red Skull — Wave 2", 17, True),
    # Wave 3: Galaxy's Most Wanted + Hero Packs (2021) — all Legacy
    ("Rocket",                     "Galaxy's Most Wanted — Wave 3", 18, True),
    ("Groot",                      "Galaxy's Most Wanted — Wave 3", 19, True),
    ("Star-Lord",                  "Galaxy's Most Wanted — Wave 3", 20, True),
    ("Gamora",                     "Galaxy's Most Wanted — Wave 3", 21, True),
    ("Drax",                       "Galaxy's Most Wanted — Wave 3", 22, True),
    ("Venom (Flash)",              "Galaxy's Most Wanted — Wave 3", 23, True),
    # Wave 4: Mad Titan's Shadow + Hero Packs (2021-2022) — all Legacy
    ("Spectrum",                   "Mad Titan's Shadow — Wave 4", 24, True),
    ("Adam Warlock",               "Mad Titan's Shadow — Wave 4", 25, True),
    ("Nebula",                     "Mad Titan's Shadow — Wave 4", 26, True),
    ("War Machine",                "Mad Titan's Shadow — Wave 4", 27, True),
    ("Valkyrie",                   "Mad Titan's Shadow — Wave 4", 28, True),
    ("Vision",                     "Mad Titan's Shadow — Wave 4", 29, True),
    # Wave 5: Sinister Motives + Hero Packs (2022) — all Legacy
    ("Spider-Man (Miles)",         "Sinister Motives — Wave 5", 30, True),
    ("Ghost Spider",               "Sinister Motives — Wave 5", 31, True),
    ("Nova",                       "Sinister Motives — Wave 5", 32, True),
    ("Ironheart",                  "Sinister Motives — Wave 5", 33, True),
    ("Spider-Ham",                 "Sinister Motives — Wave 5", 34, True),
    ("SP//dr",                     "Sinister Motives — Wave 5", 35, True),
    # Wave 6: Mutant Genesis + Hero Packs (2022-2023) — all Legacy
    ("Shadowcat",                  "Mutant Genesis — Wave 6", 36, True),
    ("Colossus",                   "Mutant Genesis — Wave 6", 37, True),
    ("Cyclops",                    "Mutant Genesis — Wave 6", 38, True),
    ("Phoenix",                    "Mutant Genesis — Wave 6", 39, True),
    ("Wolverine",                  "Mutant Genesis — Wave 6", 40, True),
    ("Storm",                      "Mutant Genesis — Wave 6", 41, True),
    ("Gambit",                     "Mutant Genesis — Wave 6", 42, True),
    ("Rogue",                      "Mutant Genesis — Wave 6", 43, True),
    # Wave 7: NeXt Evolution + Hero Packs (2023) — all Legacy
    ("Cable",                      "NeXt Evolution — Wave 7", 44, True),
    ("Domino",                     "NeXt Evolution — Wave 7", 45, True),
    ("Psylocke",                   "NeXt Evolution — Wave 7", 46, True),
    ("Angel",                      "NeXt Evolution — Wave 7", 47, True),
    ("X-23",                       "NeXt Evolution — Wave 7", 48, True),
    ("Deadpool",                   "NeXt Evolution — Wave 7", 49, True),
    # Wave 8: Age of Apocalypse + Hero Packs (2024) — all Current
    ("Bishop",                     "Age of Apocalypse — Wave 8", 50, False),
    ("Magik",                      "Age of Apocalypse — Wave 8", 51, False),
    ("Iceman",                     "Age of Apocalypse — Wave 8", 52, False),
    ("Jubilee",                    "Age of Apocalypse — Wave 8", 53, False),
    ("Nightcrawler",               "Age of Apocalypse — Wave 8", 54, False),
    ("Magneto",                    "Age of Apocalypse — Wave 8", 55, False),
    # Wave 9: Agents of S.H.I.E.L.D. + Hero Packs (2025) — all Current
    ("Maria Hill",                 "Agents of S.H.I.E.L.D. — Wave 9", 56, False),
    ("Nick Fury",                  "Agents of S.H.I.E.L.D. — Wave 9", 57, False),
    ("Black Panther (Shuri)",      "Agents of S.H.I.E.L.D. — Wave 9", 58, False),
    ("Silk",                       "Agents of S.H.I.E.L.D. — Wave 9", 59, False),
    ("Falcon",                     "Agents of S.H.I.E.L.D. — Wave 9", 60, False),
    ("Winter Soldier",             "Agents of S.H.I.E.L.D. — Wave 9", 61, False),
    # Wave 10: Civil War + Hero Packs (2025-2026) — all Current
    ("Hulkling",                   "Civil War — Wave 10",  62, False),
    ("Tigra",                      "Civil War — Wave 10",  63, False),
    ("Wonder Man",                 "Civil War — Wave 10",  64, False),
    ("Hercules",                   "Civil War — Wave 10",  65, False),
]

# Quick lookup dicts
HERO_RELEASE_INDEX = {name: idx for name, _, idx, _ in HERO_RELEASE_DATA}
HERO_WAVE = {name: wave for name, wave, _, _ in HERO_RELEASE_DATA}
HERO_LEGACY = {name: legacy for name, _, _, legacy in HERO_RELEASE_DATA}

# Ordered list of all waves (for filter dropdowns)
WAVE_ORDER = list(dict.fromkeys(wave for _, wave, _, _ in HERO_RELEASE_DATA))
_legacy_wave_set = {wave for _, wave, _, legacy in HERO_RELEASE_DATA if legacy}
LEGACY_WAVE_ORDER = [w for w in WAVE_ORDER if w in _legacy_wave_set]
