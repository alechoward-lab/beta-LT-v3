"""
Hero Pairings — Mutually Aware Version

Pairings are influenced by:
- Fixing each other’s weaknesses
- Tempo balance (early ↔ late)
- Survivability and support
- Late-game heroes with high-thwart partners
- Avoiding strong + strong and weak + weak
"""

# ----------------------------------------
# Tuning Variables
# ----------------------------------------
TARGET = 2
BASE_STAT_COUNT = 8

# Mutual-awareness blending
PRIMARY_WEIGHT = 0.6        # weight for selected hero's perspective
SECONDARY_WEIGHT = 0.4      # weight for partner's perspective

# Global stat indices
ECONOMY_INDEX = 0
TEMPO_INDEX = 1
SURVIVABILITY_INDEX = 3
THWART_INDEX = 5
SUPPORT_INDEX = 9
LATE_GAME_INDEX = 11

# Boon thresholds
LATE_GAME_TRIGGER = 1.0

# Synergy weights
TEMPO_PAIR_BONUS = 0.25
LATE_GAME_THWART_BONUS = 0.20
BLOCKING_SUPPORT_BONUS = 0.25

POWER_DISINCENTIVE = 0.3
WEAK_PAIR_DISINCENTIVE = 0.5


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
    - Late-game heroes with high-thwart and support partners
    - Low survivability heroes with blockers / support heroes
    - Tempo balance (early ↔ late game)
    """)

with col2:
    st.markdown("""
    **Strengths and Limitations:**
    - Aspect-agnostic by design
    - Ignores card-level and trait synergies
    - Good for creating balanced games
    - Quickly choose hero combinations
    - Encourages fair, mutual pairings
    """)


# ----------------------------------------
# Load hero data
# ----------------------------------------
heroes = deepcopy(default_heroes)
hero_names = list(heroes.keys())


# ----------------------------------------
# Compute GENERAL POWER (boons INCLUDED)
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
# Directional synergy function
# ----------------------------------------
def directional_synergy(hero_A, hero_B):
    stats_A = heroes[hero_A]
    stats_B = heroes[hero_B]

    base_A = stats_A[:BASE_STAT_COUNT]
    base_B = stats_B[:BASE_STAT_COUNT]

    power_A = general_scores[hero_A]
    power_B = general_scores[hero_B]

    synergy_score = 0.0

    # ----------------------------------
    # 1. Weakness coverage
    # ----------------------------------
    needs = np.maximum(0, TARGET - base_A)

    usable_strengths = np.minimum(
        np.maximum(0, base_B),
        needs
    )

    if np.sum(needs) > 0:
        synergy_score += np.dot(needs, usable_strengths) / np.sum(needs)

    # ----------------------------------
    # 2. Tempo pairing
    # ----------------------------------
    tempo_mismatch = abs(
        base_A[TEMPO_INDEX] - base_B[TEMPO_INDEX]
    )
    synergy_score += TEMPO_PAIR_BONUS * tempo_mismatch

    # ----------------------------------
    # 3. Late-game hero + high thwart partner
    # ----------------------------------
    if stats_A[LATE_GAME_INDEX] >= LATE_GAME_TRIGGER:
        if base_B[THWART_INDEX] > TARGET:
            synergy_score += (
                LATE_GAME_THWART_BONUS * base_B[THWART_INDEX]
            )

    # ----------------------------------
    # 4. Low survivability + blocker/support
    # ----------------------------------
    if base_A[SURVIVABILITY_INDEX] < TARGET:
        blocking_value = (
            max(0, base_B[SURVIVABILITY_INDEX]) +
            max(0, stats_B[SUPPORT_INDEX])
        )
        synergy_score += BLOCKING_SUPPORT_BONUS * blocking_value

    # ----------------------------------
    # 5. Strong + strong disincentive
    # ----------------------------------
    if (
        power_A >= STRONG_HERO_THRESHOLD
        and power_B >= STRONG_HERO_THRESHOLD
    ):
        synergy_score *= POWER_DISINCENTIVE

    # ----------------------------------
    # 6. Weak + weak disincentive
    # ----------------------------------
    if (
        power_A <= WEAK_HERO_THRESHOLD
        and power_B <= WEAK_HERO_THRESHOLD
    ):
        synergy_score *= WEAK_PAIR_DISINCENTIVE

    return synergy_score


# ----------------------------------------
# Select primary hero
# ----------------------------------------
hero_A = st.selectbox("Select a hero to view pairings:", hero_names)


# ----------------------------------------
# Score partner heroes (mutually aware)
# ----------------------------------------
scores = {}

for hero_B in hero_names:
    if hero_B == hero_A:
        continue

    score_A_to_B = directional_synergy(hero_A, hero_B)
    score_B_to_A = directional_synergy(hero_B, hero_A)

    final_score = (
        PRIMARY_WEIGHT * score_A_to_B +
        SECONDARY_WEIGHT * score_B_to_A
    )

    scores[hero_B] = final_score


# ----------------------------------------
# Safety: prevent zero-variance tiering
# ----------------------------------------
vals = np.array(list(scores.values()))

if np.allclose(vals, 0):
    st.warning(
        "No meaningful synergy differences detected for this hero "
        "(all partners score similarly)."
    )
    st.stop()


# ----------------------------------------
# Tiering
# ----------------------------------------
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
                    st.image(img, width="stretch")


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
