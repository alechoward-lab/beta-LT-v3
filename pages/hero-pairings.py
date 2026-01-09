"""
Hero Pairings — UX-Refined Mutually Aware Version

Design goals:
- Fix each other’s weaknesses
- Encourage balanced, mutual partnerships
- Avoid misleading one-sided S-tier pairings
- Remain explainable and intuitive
"""

# ----------------------------------------
# Tuning Variables
# ----------------------------------------
TARGET = 2
BASE_STAT_COUNT = 8

# Mutual awareness
PRIMARY_WEIGHT = 0.6
SECONDARY_WEIGHT = 0.4

# Reciprocity guardrails
MIN_RECIPROCITY_RATIO = 0.35     # prevents one-sided S tiers
S_TIER_RECIPROCITY_BOOST = 0.15  # rewards genuinely mutual pairings

# Global stat indices
TEMPO_INDEX = 1
SURVIVABILITY_INDEX = 3
THWART_INDEX = 5
SUPPORT_INDEX = 9
LATE_GAME_INDEX = 11

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

st.markdown(
    """
    These pairings focus on **balanced, mutually beneficial partnerships**.
    A strong pairing should help *both* heroes succeed — not just one.
    """
)


# ----------------------------------------
# Load hero data
# ----------------------------------------
heroes = deepcopy(default_heroes)
hero_names = list(heroes.keys())


# ----------------------------------------
# Compute GENERAL POWER
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
# Directional synergy
# ----------------------------------------
def directional_synergy(hero_A, hero_B):
    stats_A = heroes[hero_A]
    stats_B = heroes[hero_B]

    base_A = stats_A[:BASE_STAT_COUNT]
    base_B = stats_B[:BASE_STAT_COUNT]

    power_A = general_scores[hero_A]
    power_B = general_scores[hero_B]

    score = 0.0

    # 1. Weakness coverage
    needs = np.maximum(0, TARGET - base_A)
    usable = np.minimum(np.maximum(0, base_B), needs)

    if np.sum(needs) > 0:
        score += np.dot(needs, usable) / np.sum(needs)

    # 2. Tempo contrast
    score += TEMPO_PAIR_BONUS * abs(
        base_A[TEMPO_INDEX] - base_B[TEMPO_INDEX]
    )

    # 3. Late-game support
    if stats_A[LATE_GAME_INDEX] >= LATE_GAME_TRIGGER:
        if base_B[THWART_INDEX] > TARGET:
            score += LATE_GAME_THWART_BONUS * base_B[THWART_INDEX]

    # 4. Fragile hero protection
    if base_A[SURVIVABILITY_INDEX] < TARGET:
        blocking = (
            max(0, base_B[SURVIVABILITY_INDEX]) +
            max(0, stats_B[SUPPORT_INDEX])
        )
        score += BLOCKING_SUPPORT_BONUS * blocking

    # 5. Power disincentives
    if power_A >= STRONG_HERO_THRESHOLD and power_B >= STRONG_HERO_THRESHOLD:
        score *= POWER_DISINCENTIVE

    if power_A <= WEAK_HERO_THRESHOLD and power_B <= WEAK_HERO_THRESHOLD:
        score *= WEAK_PAIR_DISINCENTIVE

    return score


# ----------------------------------------
# Select hero
# ----------------------------------------
hero_A = st.selectbox("Select a hero:", hero_names)


# ----------------------------------------
# Score partners
# ----------------------------------------
scores = {}
details = {}

for hero_B in hero_names:
    if hero_B == hero_A:
        continue

    a_to_b = directional_synergy(hero_A, hero_B)
    b_to_a = directional_synergy(hero_B, hero_A)

    blended = (
        PRIMARY_WEIGHT * a_to_b +
        SECONDARY_WEIGHT * b_to_a
    )

    # Reciprocity logic
    min_score = min(a_to_b, b_to_a)
    max_score = max(a_to_b, b_to_a)

    reciprocity_ratio = (
        min_score / max_score if max_score > 0 else 0
    )

    if reciprocity_ratio >= MIN_RECIPROCITY_RATIO:
        blended *= (1 + S_TIER_RECIPROCITY_BOOST)

    scores[hero_B] = blended
    details[hero_B] = {
        "a_to_b": a_to_b,
        "b_to_a": b_to_a,
        "reciprocal": reciprocity_ratio >= MIN_RECIPROCITY_RATIO
    }


# ----------------------------------------
# Tiering (slightly stabilized)
# ----------------------------------------
vals = np.array(list(scores.values()))
mean, std = vals.mean(), vals.std()

thr_S = mean + 1.25 * std
thr_A = mean + 0.4 * std
thr_B = mean - 0.4 * std
thr_C = mean - 1.25 * std

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
# Display
# ----------------------------------------
tier_colors = {
    "S": "#FF69B4",
    "A": "purple",
    "B": "#3CB371",
    "C": "#FF8C00",
    "D": "red",
}

st.header(f"Best Partners for {hero_A}")

for tier in ["S", "A", "B", "C", "D"]:
    members = tiers[tier]
    if not members:
        continue

    st.markdown(
        f"<h2 style='color:{tier_colors[tier]};'>{tier} Tier</h2>",
        unsafe_allow_html=True
    )

    cols = st.columns(5)
    for i, hero in enumerate(members):
        with cols[i % 5]:
            img = hero_image_urls.get(hero)
            if img:
                st.image(img, use_container_width=True)

            if details[hero]["reciprocal"]:
                st.caption("🤝 Mutual synergy")
            else:
                st.caption("⚠️ One-sided pairing")


# ----------------------------------------
# Background
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
