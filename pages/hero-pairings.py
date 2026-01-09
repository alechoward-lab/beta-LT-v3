"""
Hero Pairings — Mutually Aware, Direction-Aware UX Version

Design goals:
- Fix each other’s weaknesses
- Encourage balanced, mutually beneficial partnerships
- Clearly distinguish who is helping whom
- Avoid misleading one-sided S-tier pairings
- Remain explainable, heuristic, and aspect-agnostic
"""

# ----------------------------------------
# Tuning Variables
# ----------------------------------------
TARGET = 2
BASE_STAT_COUNT = 8

# Mutual awareness blending
PRIMARY_WEIGHT = 0.6
SECONDARY_WEIGHT = 0.4

# Reciprocity guardrails
MIN_RECIPROCITY_RATIO = 0.35
S_TIER_RECIPROCITY_BOOST = 0.15

# Global stat indices
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

st.markdown(
    """
    These pairings focus on **balanced, mutually beneficial partnerships**.
    Some heroes *support you*, some are *supported by you*, and the best
    partnerships benefit **both heroes**.
    """
)


# ----------------------------------------
# Load hero data
# ----------------------------------------
heroes = deepcopy(default_heroes)
hero_names = list(heroes.keys())


# ----------------------------------------
# Compute GENERAL POWER (boons included)
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

    score = 0.0

    # 1. Weakness coverage
    needs = np.maximum(0, TARGET - base_A)
    usable_strengths = np.minimum(
        np.maximum(0, base_B),
        needs
    )

    if np.sum(needs) > 0:
        score += np.dot(needs, usable_strengths) / np.sum(needs)

    # 2. Tempo contrast
    score += TEMPO_PAIR_BONUS * abs(
        base_A[TEMPO_INDEX] - base_B[TEMPO_INDEX]
    )

    # 3. Late-game hero + high thwart partner
    if stats_A[LATE_GAME_INDEX] >= LATE_GAME_TRIGGER:
        if base_B[THWART_INDEX] > TARGET:
            score += LATE_GAME_THWART_BONUS * base_B[THWART_INDEX]

    # 4. Low survivability + blocker/support
    if base_A[SURVIVABILITY_INDEX] < TARGET:
        blocking_value = (
            max(0, base_B[SURVIVABILITY_INDEX]) +
            max(0, stats_B[SUPPORT_INDEX])
        )
        score += BLOCKING_SUPPORT_BONUS * blocking_value

    # 5. Power disincentives
    if power_A >= STRONG_HERO_THRESHOLD and power_B >= STRONG_HERO_THRESHOLD:
        score *= POWER_DISINCENTIVE

    if power_A <= WEAK_HERO_THRESHOLD and power_B <= WEAK_HERO_THRESHOLD:
        score *= WEAK_PAIR_DISINCENTIVE

    return score


# ----------------------------------------
# Pairing classification
# ----------------------------------------
def classify_pairing(a_to_b, b_to_a):
    if max(a_to_b, b_to_a) == 0:
        return "neutral"

    ratio = min(a_to_b, b_to_a) / max(a_to_b, b_to_a)

    if ratio >= MIN_RECIPROCITY_RATIO:
        return "mutual"
    elif a_to_b > b_to_a:
        return "b_helps_a"   # partner supports selected hero
    else:
        return "a_helps_b"   # selected hero supports partner


# ----------------------------------------
# Select primary hero
# ----------------------------------------
hero_A = st.selectbox("Select a hero to view pairings:", hero_names)


# ----------------------------------------
# Score partner heroes (mutually aware)
# ----------------------------------------
scores = {}
details = {}

for hero_B in hero_names:
    if hero_B == hero_A:
        continue

    a_to_b = directional_synergy(hero_A, hero_B)
    b_to_a = directional_synergy(hero_B, hero_A)

    blended_score = (
        PRIMARY_WEIGHT * a_to_b +
        SECONDARY_WEIGHT * b_to_a
    )

    pairing_type = classify_pairing(a_to_b, b_to_a)

    # Slight reward for genuine mutuality
    if pairing_type == "mutual":
        blended_score *= (1 + S_TIER_RECIPROCITY_BOOST)

    scores[hero_B] = blended_score
    details[hero_B] = {
        "a_to_b": a_to_b,
        "b_to_a": b_to_a,
        "type": pairing_type
    }


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
# Tiering (stabilized)
# ----------------------------------------
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
        unsafe_allow_html=True
    )

    rows = [members[i:i + num_cols] for i in range(0, len(members), num_cols)]
    for row in rows:
        cols = st.columns(num_cols)
        for idx, hero in enumerate(row):
            with cols[idx]:
                img = hero_image_urls.get(hero)
                if img:
                    st.image(img, use_container_width=True)

                pairing_type = details[hero]["type"]

                if pairing_type == "mutual":
                    st.caption("🤝 Mutual synergy")
                elif pairing_type == "b_helps_a":
                    st.caption("⬆️ Supports you")
                elif pairing_type == "a_helps_b":
                    st.caption("⬇️ You support them")
                else:
                    st.caption("—")


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
