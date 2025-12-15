"""
Hero Pairings – 2 Player Synergy
This page focuses on complementary strength, not raw power.
"""

# ----------------------------------------
# Tuning Variables
# ----------------------------------------
TARGET = 2                  # anything below this is a weakness
TEMPO_INDEX = 1              # index of Tempo in hero stat arrays
TEMPO_PAIR_BONUS = 0.2     # weight for high-tempo <-> low-tempo pairing
POWER_DISINCENTIVE = 0.5     # penalty for strong+strong pairings

# ----------------------------------------
# Imports
# ----------------------------------------
import streamlit as st
import numpy as np
from copy import deepcopy

from default_heroes import default_heroes
from hero_image_urls import hero_image_urls
from preset_options import preset_options

# ----------------------------------------
# Page header
# ----------------------------------------
st.title("Hero Pairings (2-Player Synergy)")

st.markdown("""
**This tool evaluates hero pairings based on complementary strengths, not raw power.**

**Pairings are influenced by:**
- Fixing each other’s weaknesses
- Pairing strong heroes with weaker heroes
- Pairing low-tempo heroes with high-tempo heroes
- Avoiding redundant high-power combinations
""")

# ----------------------------------------
# Assumptions / explanation section
# ----------------------------------------

st.markdown("""
**Strengths and Shortcomings of The List:**
- Good for matching heroes to have a balanced experience
- Good for getting ideas of heroes to try together
- Does not account for specific synergies such as traits and card interactions
- Does not account for aspects -- But that also means good pairings are aspect agnostic
""")

st.text_area(
    "Assumptions, Shortcomings, and Intended Use",
    key="pairing_notes",
    height=160
)

# ----------------------------------------
# Load hero data
# ----------------------------------------
heroes = deepcopy(default_heroes)
hero_names = list(heroes.keys())

# ----------------------------------------
# Compute GENERAL POWER (2 Player preset)
# ----------------------------------------
general_weights = np.array(preset_options["General Power: 2 Player"])
general_scores = {
    hero: float(np.dot(stats, general_weights))
    for hero, stats in heroes.items()
}

gp_values = np.array(list(general_scores.values()))
gp_mean = gp_values.mean()
gp_std = gp_values.std()

# Define "strong hero" cutoff (A tier and above)
STRONG_HERO_THRESHOLD = gp_mean + 0.5 * gp_std

# ----------------------------------------
# Select primary hero
# ----------------------------------------
hero_A = st.selectbox("Select Primary Hero", hero_names)
stats_A = heroes[hero_A]
power_A = general_scores[hero_A]

# ----------------------------------------
# Compute Hero A weaknesses
# ----------------------------------------
needs = np.maximum(0, TARGET - stats_A)

# ----------------------------------------
# Score partner heroes (SYNERGY, NOT POWER)
# ----------------------------------------
scores = {}

for hero_B, stats_B in heroes.items():
    if hero_B == hero_A:
        continue

    # ----------------------------------
    # 1. Weakness coverage
    # ----------------------------------
    usable_strengths = np.minimum(
        np.maximum(0, stats_B),
        needs
    )

    synergy_score = np.dot(needs, usable_strengths)
    synergy_score /= (np.sum(needs) + 1e-6)

    # ----------------------------------
    # 2. Tempo pairing bonus
    # ----------------------------------
    tempo_A = stats_A[TEMPO_INDEX]
    tempo_B = stats_B[TEMPO_INDEX]

    tempo_mismatch = abs(tempo_A - tempo_B)
    tempo_bonus = TEMPO_PAIR_BONUS * tempo_mismatch

    synergy_score += tempo_bonus

    # ----------------------------------
    # 3. Power-based disincentive
    # ----------------------------------
    power_B = general_scores[hero_B]

    if power_A >= STRONG_HERO_THRESHOLD and power_B >= STRONG_HERO_THRESHOLD:
        synergy_score *= POWER_DISINCENTIVE

    scores[hero_B] = synergy_score

# ----------------------------------------
# Sort scores
# ----------------------------------------
sorted_scores = dict(sorted(scores.items(), key=lambda kv: kv[1]))

# ----------------------------------------
# Tier thresholds
# ----------------------------------------
vals = np.array(list(scores.values()))
mean, std = vals.mean(), vals.std()

thr_S = mean + 1.5 * std
thr_A = mean + 0.5 * std
thr_B = mean - 0.5 * std
thr_C = mean - 1.5 * std

tiers = {"S": [], "A": [], "B": [], "C": [], "D": []}

for hero, sc in scores.items():
    if sc >= thr_S:
        tiers["S"].append(hero)
    elif sc >= thr_A:
        tiers["A"].append(hero)
    elif sc >= thr_B:
        tiers["B"].append(hero)
    elif sc >= thr_C:
        tiers["C"].append(hero)
    else:
        tiers["D"].append(hero)

# ----------------------------------------
# Display tiered hero grid
# ----------------------------------------
tier_colors = {
    "S": "#FF69B4",
    "A": "purple",
    "B": "#3CB371",
    "C": "#FF8C00",
    "D": "red",
}

num_cols = 5
st.header(f"Best Partners for {hero_A}")

for tier in ["S", "A", "B", "C", "D"]:
    members = tiers[tier]
    if not members:
        continue

    st.markdown(
        f"<h2 style='color:{tier_colors[tier]};'>{tier} Tier</h2>",
        unsafe_allow_html=True,
    )

    rows = [members[i:i + num_cols] for i in range(0, len(members), num_cols)]
    for row in rows:
        cols = st.columns(num_cols)
        for idx, hero in enumerate(row):
            with cols[idx]:
                img = hero_image_urls.get(hero)
                if img:
                    st.image(img, use_container_width=True)

# ----------------------------------------
# Background image (same as home page)
# ----------------------------------------
background_image_url = (
    "https://github.com/alechoward-lab/"
    "Marvel-Champions-Hero-Tier-List/blob/main/"
    "images/background/marvel_champions_background_image_v4.jpg?raw=true"
)

st.markdown(
    f"""
    <style>
    .stApp {{
        background: url({background_image_url}) no-repeat center center fixed;
        background-size: cover;
    }}
    </style>
    """,
    unsafe_allow_html=True
)
