# villain_release_order.py

"""
Villain release data for wave-based filtering in the tier list.
Similar structure to hero_release_order.py.

Format: (villain_name, wave_label, release_index, is_legacy)
- wave_label: Groups villains by their product release
- release_index: Overall release order (used for sorting)
- is_legacy: True for older products, False for recent/upcoming
"""

VILLAIN_RELEASE_DATA = [
    # Wave 1 - Core Set (2019-11)
    ("Rhino", "Wave 1 - Core Set", 1, True),
    ("Klaw", "Wave 1 - Core Set", 2, True),
    ("Ultron", "Wave 1 - Core Set", 3, True),
    
    # Wave 1 - Green Goblin Scenario Pack (2019-12)
    ("Risky Business", "Wave 1 - Green Goblin", 4, True),
    ("Mutagen Formula", "Wave 1 - Green Goblin", 5, True),
    
    # Wave 1 - Wrecking Crew Scenario Pack (2020-02)
    ("Wrecking Crew", "Wave 1 - Wrecking Crew", 6, True),
    
    # Wave 2 - Rise of Red Skull (2020-09)
    ("Crossbones", "Wave 2 - Rise of Red Skull", 7, True),
    ("Absorbing Man", "Wave 2 - Rise of Red Skull", 8, True),
    ("Taskmaster", "Wave 2 - Rise of Red Skull", 9, True),
    ("Zola", "Wave 2 - Rise of Red Skull", 10, True),
    ("Red Skull", "Wave 2 - Rise of Red Skull", 11, True),
    
    # Wave 2 - Once and Future Kang (2020-10)
    ("Kang", "Wave 2 - Once and Future Kang", 12, True),
    
    # Wave 3 - Galaxy's Most Wanted (2021-04)
    ("Drang", "Wave 3 - Galaxy's Most Wanted", 13, True),
    ("Collector 1", "Wave 3 - Galaxy's Most Wanted", 14, True),
    ("Collector 2", "Wave 3 - Galaxy's Most Wanted", 15, True),
    ("Nebula", "Wave 3 - Galaxy's Most Wanted", 16, True),
    ("Ronan", "Wave 3 - Galaxy's Most Wanted", 17, True),
    
    # Wave 4 - Mad Titan's Shadow (2021-09)
    ("Ebony Maw", "Wave 4 - Mad Titan's Shadow", 18, True),
    ("Tower Defense", "Wave 4 - Mad Titan's Shadow", 19, True),
    ("Thanos", "Wave 4 - Mad Titan's Shadow", 20, True),
    ("Hela", "Wave 4 - Mad Titan's Shadow", 21, True),
    ("Loki", "Wave 4 - Mad Titan's Shadow", 22, True),
    
    # Wave 4 - The Hood Scenario Pack (2021-11)
    ("The Hood", "Wave 4 - The Hood", 23, True),
    
    # Wave 5 - Sinister Motives (2022-04)
    ("Sandman", "Wave 5 - Sinister Motives", 24, True),
    ("Venom", "Wave 5 - Sinister Motives", 25, True),
    ("Mysterio", "Wave 5 - Sinister Motives", 26, True),
    ("Sinister Six", "Wave 5 - Sinister Motives", 27, True),
    ("Venom Goblin", "Wave 5 - Sinister Motives", 28, True),
    
    # Wave 6 - Mutant Genesis (2022-09)
    ("Sabertooth", "Wave 6 - Mutant Genesis", 29, True),
    ("Project Wideawake", "Wave 6 - Mutant Genesis", 30, True),
    ("Master Mold", "Wave 6 - Mutant Genesis", 31, True),
    ("Mansion Attack", "Wave 6 - Mutant Genesis", 32, True),
    ("Magneto", "Wave 6 - Mutant Genesis", 33, True),
    
    # Wave 6 - Mojo Mania (2022-11)
    ("Magog", "Wave 6 - Mojo Mania", 34, True),
    ("Spiral", "Wave 6 - Mojo Mania", 35, True),
    ("Mojo", "Wave 6 - Mojo Mania", 36, True),
    
    # Wave 7 - NeXt Evolution (2023-08)
    ("Morlock Siege", "Wave 7 - NeXt Evolution", 37, True),
    ("On The Run", "Wave 7 - NeXt Evolution", 38, True),
    ("Juggernaut", "Wave 7 - NeXt Evolution", 39, True),
    ("Mister Sinister", "Wave 7 - NeXt Evolution", 40, True),
    ("Stryfe", "Wave 7 - NeXt Evolution", 41, True),
    
    # Wave 8 - Age of Apocalypse (2024-03)
    ("Unus", "Wave 8 - Age of Apocalypse", 42, False),
    ("Four Horsemen", "Wave 8 - Age of Apocalypse", 43, False),
    ("Apocalypse 1", "Wave 8 - Age of Apocalypse", 44, False),
    ("Dark Beast", "Wave 8 - Age of Apocalypse", 45, False),
    ("Apocalypse 2", "Wave 8 - Age of Apocalypse", 46, False),
    
    # Wave 9 - Agents of S.H.I.E.L.D. (2025-02)
    ("Black Widow", "Wave 9 - Agents of S.H.I.E.L.D.", 47, False),
    ("Batroc", "Wave 9 - Agents of S.H.I.E.L.D.", 48, False),
    ("M.O.D.O.K.", "Wave 9 - Agents of S.H.I.E.L.D.", 49, False),
    ("Thunderbolts", "Wave 9 - Agents of S.H.I.E.L.D.", 50, False),
    ("Baron Zemo", "Wave 9 - Agents of S.H.I.E.L.D.", 51, False),
    
    # Wave 10 - Trickster Takeover (2025-08)
    ("Enchantress", "Wave 10 - Trickster Takeover", 52, False),
    ("God of Lies", "Wave 10 - Trickster Takeover", 53, False),
    
    # Wave 10 - Civil War (2025-10)
    ("Iron Man (Civil War)", "Wave 10 - Civil War", 54, False),
    ("Captain Marvel (Civil War)", "Wave 10 - Civil War", 55, False),
    ("Captain America (Civil War)", "Wave 10 - Civil War", 56, False),
    ("Spider-Woman (Civil War)", "Wave 10 - Civil War", 57, False),
    
    # Wave 10 - Synthezoid Smackdown (2025-12)
    ("She-Hulk (Synthezoid)", "Wave 10 - Synthezoid Smackdown", 58, False),
    ("Vision (Synthezoid)", "Wave 10 - Synthezoid Smackdown", 59, False),
]

# Quick lookup dictionaries
VILLAIN_RELEASE_INDEX = {name: idx for name, wave, idx, legacy in VILLAIN_RELEASE_DATA}
VILLAIN_WAVE = {name: wave for name, wave, idx, legacy in VILLAIN_RELEASE_DATA}
VILLAIN_LEGACY = {name: legacy for name, wave, idx, legacy in VILLAIN_RELEASE_DATA}

# Ordered list of waves for filter dropdown
VILLAIN_WAVE_ORDER = list(dict.fromkeys(wave for name, wave, idx, legacy in VILLAIN_RELEASE_DATA))
