# hero_decks.py

"""
Mapping of hero names to their MarvelCDB deck lists.
Each hero maps to a list of deck entries (supports multiple decks per hero).
api_type: "deck" for /api/public/deck/{id}, "decklist" for /api/public/decklist/{id}
"""

hero_decks = {
    "Captain Marvel": [
        {"name": "Beast Recursion", "url": "https://marvelcdb.com/deck/view/1084856", "deck_id": "1084856", "api_type": "deck"},
        {"name": "Beginner Deck Core Box Only", "url": "https://marvelcdb.com/deck/view/1161364", "deck_id": "1161364", "api_type": "deck"},
    ],
    "Iron Man": [
        {"name": "Repurpose", "url": "https://marvelcdb.com/deck/view/1084866", "deck_id": "1084866", "api_type": "deck"},
    ],
    "Spider-Man (Peter)": [
        {"name": "I'm A Web-Warrior Now", "url": "https://marvelcdb.com/deck/view/1093366", "deck_id": "1093366", "api_type": "deck"},
        {"name": "Beginner Deck Core Box Only", "url": "https://marvelcdb.com/deck/view/1161362", "deck_id": "1161362", "api_type": "deck"},
    ],
    "Black Panther (T'challa)": [
        {"name": "Draw Power Forever", "url": "https://marvelcdb.com/deck/view/1085865", "deck_id": "1085865", "api_type": "deck"},
    ],
    "She-Hulk": [
        {"name": "Ready For A Fight", "url": "https://marvelcdb.com/deck/view/1085951", "deck_id": "1085951", "api_type": "deck"},
    ],
    "Captain America": [
        {"name": "Avengers Assemble", "url": "https://marvelcdb.com/deck/view/1086532", "deck_id": "1086532", "api_type": "deck"},
        {"name": "Basic ATK FTW", "url": "https://marvelcdb.com/deck/view/1161366", "deck_id": "1161366", "api_type": "deck"},
    ],
    "Ms. Marvel": [
        {"name": "Multithwart", "url": "https://marvelcdb.com/deck/view/1090684", "deck_id": "1090684", "api_type": "deck"},
    ],
    "Thor": [
        {"name": "A Very Vigilant Bub", "url": "https://marvelcdb.com/deck/view/1108780", "deck_id": "1108780", "api_type": "deck"},
    ],
    "Black Widow": [
        {"name": "Rapid Response", "url": "https://marvelcdb.com/deck/view/1089382", "deck_id": "1089382", "api_type": "deck"},
    ],
    "Doctor Strange": [
        {"name": "Mystical Avenging Readies", "url": "https://marvelcdb.com/deck/view/1086539", "deck_id": "1086539", "api_type": "deck"},
        {"name": "Did Someone Order A Doctor?", "url": "https://marvelcdb.com/deck/view/1122835", "deck_id": "1122835", "api_type": "deck"},
    ],
    "Hulk": [
        {"name": "Consistent Damage", "url": "https://marvelcdb.com/deck/view/1091215", "deck_id": "1091215", "api_type": "deck"},
    ],
    "Hawkeye": [
        {"name": "Minion Slaying", "url": "https://marvelcdb.com/deck/view/1086548", "deck_id": "1086548", "api_type": "deck"},
    ],
    "Spider-Woman": [
        {"name": "Cheap Value", "url": "https://marvelcdb.com/deck/view/1093311", "deck_id": "1093311", "api_type": "deck"},
    ],
    "Ant-Man": [
        {"name": "Form Flipping", "url": "https://marvelcdb.com/deck/view/1087593", "deck_id": "1087593", "api_type": "deck"},
    ],
    "Wasp": [
        {"name": "Mental Recursion", "url": "https://marvelcdb.com/deck/view/897938", "deck_id": "897938", "api_type": "deck"},
    ],
    "Quicksilver": [
        {"name": "Status Lock Ready", "url": "https://marvelcdb.com/deck/view/1087525", "deck_id": "1087525", "api_type": "deck"},
    ],
    "Scarlet Witch": [
        {"name": "S.H.I.E.L.D. Knows", "url": "https://marvelcdb.com/deck/view/1087171", "deck_id": "1087171", "api_type": "deck"},
    ],
    "Star-Lord": [
        {"name": "Diverse Ally Burst Damage", "url": "https://marvelcdb.com/deck/view/1086854", "deck_id": "1086854", "api_type": "deck"},
    ],
    "Groot": [
        {"name": "Alter-ego Access Burst Thwart", "url": "https://marvelcdb.com/deck/view/1090008", "deck_id": "1090008", "api_type": "deck"},
        {"name": "Deck 2", "url": "https://marvelcdb.com/decklist/view/48581/i-am-not-groot-1.0", "deck_id": "48581", "api_type": "decklist"},
    ],
    "Rocket": [
        {"name": "Repurpose", "url": "https://marvelcdb.com/deck/view/1086471", "deck_id": "1086471", "api_type": "deck"},
    ],
    "Gamora": [
        {"name": "Trigger Ability Each Phase", "url": "https://marvelcdb.com/deck/view/1105688", "deck_id": "1105688", "api_type": "deck"},
    ],
    "Drax": [
        {"name": "Repurpose", "url": "https://marvelcdb.com/deck/view/1090676", "deck_id": "1090676", "api_type": "deck"},
    ],
    "Venom (Flash)": [
        {"name": "Turbo Draw Quick Setup", "url": "https://marvelcdb.com/deck/view/1091451", "deck_id": "1091451", "api_type": "deck"},
    ],
    "Spectrum": [
        {"name": "Honed Divebombs", "url": "https://marvelcdb.com/deck/view/1089748", "deck_id": "1089748", "api_type": "deck"},
    ],
    "Adam Warlock": [
        {"name": "Summon Strong Allies", "url": "https://marvelcdb.com/deck/view/847120", "deck_id": "847120", "api_type": "deck"},
    ],
    "Nebula": [
        {"name": "Ready For A Fight Techniques", "url": "https://marvelcdb.com/deck/view/1091455", "deck_id": "1091455", "api_type": "deck"},
    ],
    "War Machine": [
        {"name": "S.H.I.E.L.D. Leadership", "url": "https://marvelcdb.com/deck/view/1090911", "deck_id": "1090911", "api_type": "deck"},
    ],
    "Valkyrie": [
        {"name": "Minion Slaying", "url": "https://marvelcdb.com/deck/view/1092094", "deck_id": "1092094", "api_type": "deck"},
    ],
    "Vision": [
        {"name": "Basic Attack Readying", "url": "https://marvelcdb.com/deck/view/1090647", "deck_id": "1090647", "api_type": "deck"},
    ],
    "Ghost Spider": [
        {"name": "Perfect Defense", "url": "https://marvelcdb.com/deck/view/1087738", "deck_id": "1087738", "api_type": "deck"},
    ],
    "Spider-Man (Miles)": [
        {"name": "Draw Into Your Events", "url": "https://marvelcdb.com/deck/view/1090962", "deck_id": "1090962", "api_type": "deck"},
    ],
    "Nova": [
        {"name": "Side Kick Leadership", "url": "https://marvelcdb.com/deck/view/1091462", "deck_id": "1091462", "api_type": "deck"},
    ],
    "Ironheart": [
        {"name": "Beast Recursion", "url": "https://marvelcdb.com/deck/view/1086950", "deck_id": "1086950", "api_type": "deck"},
    ],
    "SP//dr": [
        {"name": "Repurpose", "url": "https://marvelcdb.com/deck/view/1092931", "deck_id": "1092931", "api_type": "deck"},
    ],
    "Spider-Ham": [
        {"name": "Webs and Money", "url": "https://marvelcdb.com/deck/view/1088112", "deck_id": "1088112", "api_type": "deck"},
    ],
    "Colossus": [
        {"name": "Ready For A Tough Fight", "url": "https://marvelcdb.com/deck/view/1093335", "deck_id": "1093335", "api_type": "deck"},
    ],
    "Shadowcat": [
        {"name": "Interrupt The Villain w/ Damage", "url": "https://marvelcdb.com/deck/view/1092027", "deck_id": "1092027", "api_type": "deck"},
    ],
    "Cyclops": [
        {"name": "Uncanny X-Men Leadership", "url": "https://marvelcdb.com/deck/view/1091530", "deck_id": "1091530", "api_type": "deck"},
        {"name": "Deck 2", "url": "https://marvelcdb.com/decklist/view/43776/cool-sloppy-c-8-ball-corner-pocket-1.0", "deck_id": "43776", "api_type": "decklist"},
    ],
    "Phoenix": [
        {"name": "Psychic Kicker", "url": "https://marvelcdb.com/decklist/view/49910/daring-lime-s-kick-a-1.0", "deck_id": "49910", "api_type": "decklist"},
        {"name": "Deck 2", "url": "https://marvelcdb.com/decklist/view/39227/daring-lime-s-unleash-the-phoenix-1.0", "deck_id": "39227", "api_type": "decklist"},
    ],
    "Wolverine": [
        {"name": "Ready and Heal", "url": "https://marvelcdb.com/deck/view/1090975", "deck_id": "1090975", "api_type": "deck"},
    ],
    "Storm": [
        {"name": "Cheap Ally Spam", "url": "https://marvelcdb.com/deck/view/1092060", "deck_id": "1092060", "api_type": "deck"},
    ],
    "Gambit": [
        {"name": "Enhanced Attack Events", "url": "https://marvelcdb.com/deck/view/1091538", "deck_id": "1091538", "api_type": "deck"},
    ],
    "Rogue": [
        {"name": "Ready and Heal", "url": "https://marvelcdb.com/deck/view/1092019", "deck_id": "1092019", "api_type": "deck"},
    ],
    "Cable": [
        {"name": "Side Scheme Maxing", "url": "https://marvelcdb.com/deck/view/1092927", "deck_id": "1092927", "api_type": "deck"},
    ],
    "Domino": [
        {"name": "Turbo Draw Set Up", "url": "https://marvelcdb.com/deck/view/1092919", "deck_id": "1092919", "api_type": "deck"},
    ],
    "Psylocke": [
        {"name": "Uncanny X-Force Leadership", "url": "https://marvelcdb.com/deck/view/1086983", "deck_id": "1086983", "api_type": "deck"},
    ],
    "Angel": [
        {"name": "Tempo Thwarting", "url": "https://marvelcdb.com/deck/view/1092421", "deck_id": "1092421", "api_type": "deck"},
    ],
    "X-23": [
        {"name": "Sidekick Readying", "url": "https://marvelcdb.com/deck/view/1087561", "deck_id": "1087561", "api_type": "deck"},
    ],
    "Deadpool": [
        {"name": "Immortal Support w/ Burst", "url": "https://marvelcdb.com/deck/view/1088131", "deck_id": "1088131", "api_type": "deck"},
    ],
    "Bishop": [
        {"name": "Discarding Leadership", "url": "https://marvelcdb.com/deck/view/1092937", "deck_id": "1092937", "api_type": "deck"},
    ],
    "Magik": [
        {"name": "Mystic Strength In Diversity", "url": "https://marvelcdb.com/deck/view/1091529", "deck_id": "1091529", "api_type": "deck"},
    ],
    "Iceman": [
        {"name": "Uncanny X-Men Readying", "url": "https://marvelcdb.com/deck/view/1089175", "deck_id": "1089175", "api_type": "deck"},
    ],
    "Jubilee": [
        {"name": "Solo/2 Player Control", "url": "https://marvelcdb.com/deck/view/1122830", "deck_id": "1122830", "api_type": "deck"},
    ],
    "Nightcrawler": [
        {"name": "Perfect Defense", "url": "https://marvelcdb.com/deck/view/1086985", "deck_id": "1086985", "api_type": "deck"},
        {"name": "Deck 2", "url": "https://marvelcdb.com/decklist/view/48357/daring-lime-s-daytripper-can-work-it-out-1.0", "deck_id": "48357", "api_type": "decklist"},
    ],
    "Magneto": [
        {"name": "Readying", "url": "https://marvelcdb.com/deck/view/1091453", "deck_id": "1091453", "api_type": "deck"},
        {"name": "Deck 2", "url": "https://marvelcdb.com/deck/view/1122833", "deck_id": "1122833", "api_type": "deck"},
    ],
    "Maria Hill": [
        {"name": "S.H.I.E.L.D. Supports", "url": "https://marvelcdb.com/deck/view/1091200", "deck_id": "1091200", "api_type": "deck"},
    ],
    "Nick Fury": [
        {"name": "Basic Thwart Preparation", "url": "https://marvelcdb.com/deck/view/1093278", "deck_id": "1093278", "api_type": "deck"},
    ],
    "Black Panther (Shuri)": [
        {"name": "Sidekick Leadership", "url": "https://marvelcdb.com/deck/view/1091545", "deck_id": "1091545", "api_type": "deck"},
    ],
    "Silk": [
        {"name": "Turbo Draw Setup", "url": "https://marvelcdb.com/deck/view/1091546", "deck_id": "1091546", "api_type": "deck"},
        {"name": "Deck 2", "url": "https://marvelcdb.com/decklist/view/49452/daring-lime-s-better-out-than-in-1.0", "deck_id": "49452", "api_type": "decklist"},
    ],
    "Falcon": [
        {"name": "Aerial Vigilance", "url": "https://marvelcdb.com/deck/view/1093355", "deck_id": "1093355", "api_type": "deck"},
    ],
    "Winter Soldier": [
        {"name": "Tempo Attack Events", "url": "https://marvelcdb.com/deck/view/1091548", "deck_id": "1091548", "api_type": "deck"},
    ],
    "Tigra": [
        {"name": "Minion Summoning", "url": "https://marvelcdb.com/deck/view/1097325", "deck_id": "1097325", "api_type": "deck"},
    ],
    "Hulkling": [
        {"name": "Strength In Diversity & Numbers", "url": "https://marvelcdb.com/deck/view/1097339", "deck_id": "1097339", "api_type": "deck"},
    ],
    "Wonder Man": [
        {"name": "CE: MCU", "url": "https://marvelcdb.com/decklist/view/60364/avoid-damage-and-tuck-1.0", "deck_id": "60364", "api_type": "decklist"},
    ],
    "Hercules": [
        {"name": "Current Environment Solo", "url": "https://marvelcdb.com/deck/view/1128874", "deck_id": "1128874", "api_type": "deck"},
    ],
}
