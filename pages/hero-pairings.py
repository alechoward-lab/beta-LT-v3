"""
Hero Pairings – 2 Player Synergy
Pairings are based on baseline stats only (indices 0–9).
Boons and conditional bonuses are excluded from synergy calculations.
"""

# ----------------------------------------
# Tuning Variables
# ----------------------------------------
TARGET = 2                      # anything below this is a weakness
BASE_STAT_COUNT = 8            # indices 0–7 are baseline stats
#              e, t, cv,s, d, th,re,mi,c, s, br,lg,si,sc,mu
TEMPO_INDEX = 1                 # Tempo stat index
THWART_INDEX = 5                # Thwart stat index
SURVIVABILITY_INDEX = 3         # Survivability stat index
SUPPORT_INDEX = 9               # Support stat index

TEMPO_PAIR_BONUS = 0.25         # high-tempo <-> low-tempo pairing
LATE_GAME_THWART_BONUS = 0.20   # late-game + high thwart bonus
BLOCKING_SUPPORT_BONUS = 0.25   # low survivability + support/survivability partner

POWER_DISINCENTIVE = 0.65       # strong + strong penalty
WEAK_PAIR_DISINCENTIVE = 0.75   # weak + weak penalty

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
st.title("Hero Pairings")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Pairings are influenced by:**
    - Fixing each other’s weaknesses
    - Pairing strong heroes with weaker heroes
    - Avoiding weak + weak pairings
    - Late-game heroes with high-thwart partners
    - Low survivability heroes with blockers / support heroes
    - Tempo balance (early ↔ late game)
    """)

with col2:
    st.markdown("""
    **Strengths and Shortcomings of This List:**
    - Helps find balanced and comfortable 2-player pairings
    - Encourages role diversity instead of raw power
    - Does not model card-level synergies or traits
    - Aspect-agnostic by design
    - Inherits assumptions from the General Power tier list
    """)

# ----------------------------------------
# Load hero data
# ----------------------------------------
heroes = deepcopy(default_heroes)
hero_names = list(heroes.keys())

# ----------------------------------------
# Compute GENERAL POWER (2 Player preset)
# NOTE: Power intentionally includes boons
# ----------------------------------------
general_weights = np.array(preset_options["General Power: 2 Player"])
general_scores = {
    hero: float(np.dot(stats, general_weights))
    for hero, stats in heroes.items()
}

gp_values = np.array(list(general_scores.values()))
gp_mean = gp_values.mean()
gp_std = gp_values.std()

STRONG_HERO_THRESHOLD = gp_mean + 0.5 * gp_std
WEAK_HERO_THRESHOLD = gp_mean - 0.5 * gp_std

# ----------------------------------------
# Select primary hero
# ----------------------------------------
hero_A = st.selectbox("Select a hero to view pairings:", hero_names)
stats_A = heroes[hero_A]
base_stats_A = stats_A[:BASE_STAT_COUNT]
power_A = general_scores[hero_A]

# ----------------------------------------
# Compute Hero A weaknesses (baseline only)
# ----------------------------------------
needs = np.maximum(0, TARGET - base_stats_A)

# ----------------------------------------
# Score partner heroes
# ----------------------------------------
scores = {}

for hero_B, stats_B in heroes.items():
    if hero_B == hero_A:
        continue

    base_stats_B = stats_B[:BASE_STAT_COUNT]
    power_B = general_scores[hero_B]

    # ----------------------------------
    # 1. Weakness coverage (core synergy)
    # ----------------------------------
    usable_strengths = np.minimum(
        np.maximum(0, base_stats_B),
        needs
    )

    synergy_score = np.dot(needs, usable_strengths)
    synergy_score /= (np.sum(needs) + 1e-6)

    # ----------------------------------
    # 2. Tempo pairing (early ↔ late)
    # ----------------------------------
    tempo_A = base_stats_A[TEMPO_INDEX]
    tempo_B = base_stats_B[TEMPO_INDEX]

    tempo_mismatch = abs(tempo_A - tempo_B)
    synergy_score += TEMPO_PAIR_BONUS * tempo_mismatch

    # ----------------------------------
    # 3. Late-game hero + high thwart bonus
    # ----------------------------------
    if tempo_A < TARGET and base_stats_B[THWART_INDEX] > TARGET:
        synergy_score += LATE_GAME_THWART_BONUS * base_stats_B[THWART_INDEX]

    # ----------------------------------
    # 4. Low survivability + blocker/support bonus
    # ----------------------------------
    if base_stats_A[SURVIVABILITY_INDEX] < TARGET:
        blocking_value = (
            max(0, base_stats_B[SURVIVABILITY_INDEX]) +
            max(0, base_stats_B[SUPPORT_INDEX])
        )
        synergy_score += BLOCKING_SUPPORT_BONUS * blocking_value

    # ----------------------------------
    # 5. Strong + strong disincentive
    # ----------------------------------
    if power_A >= STRONG_HERO_THRESHOLD and power_B >= STRONG_HERO_THRESHOLD:
        synergy_score *= POWER_DISINCENTIVE

    # ----------------------------------
    # 6. Weak + weak disincentive
    # ----------------------------------
    if power_A <= WEAK_HERO_THRESHOLD and power_B <= WEAK_HERO_THRESHOLD:
        synergy_score *= WEAK_PAIR_DISINCENTIVE

    scores[hero_B] = synergy_score

# ----------------------------------------
# Tiering
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
# Background image
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
