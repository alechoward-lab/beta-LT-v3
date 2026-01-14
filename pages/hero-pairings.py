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

PRIMARY_WEIGHT = 0.6
SECONDARY_WEIGHT = 0.4

MIN_RECIPROCITY_RATIO = 0.35
S_TIER_RECIPROCITY_BOOST = 0.15

# Baseline stat indices
ECONOMY_INDEX = 0
TEMPO_INDEX = 1
CARD_VALUE_INDEX = 2
SURVIVABILITY_INDEX = 3
VILLAIN_DAMAGE_INDEX = 4
THWART_INDEX = 5
RELIABILITY_INDEX = 6
MINION_CONTROL_INDEX = 7

# Boon indices
CONTROL_INDEX = 8
SUPPORT_INDEX = 9
LATE_GAME_INDEX = 11

LATE_GAME_TRIGGER = 1.0

TEMPO_PAIR_BONUS = 0.25
LATE_GAME_THWART_BONUS = 0.20
BLOCKING_SUPPORT_BONUS = 0.25

POWER_DISINCENTIVE = 0.3
WEAK_PAIR_DISINCENTIVE = 0.5

# UI-only text thresholds
WEAK_TEXT_THRESHOLD = 2
STRONG_TEXT_THRESHOLD = 3


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

    # ----------------------------------
    # 1. Weakness coverage
    # ----------------------------------
    needs = np.maximum(0, TARGET - base_A)
    usable_strengths = np.minimum(np.maximum(0, base_B), needs)

    if np.sum(needs) > 0:
        score += np.dot(needs, usable_strengths) / np.sum(needs)

    # ----------------------------------
    # 2. Tempo contrast
    # ----------------------------------
    score += TEMPO_PAIR_BONUS * abs(
        base_A[TEMPO_INDEX] - base_B[TEMPO_INDEX]
    )

    # ----------------------------------
    # 3. Late-game hero + high thwart
    # ----------------------------------
    if stats_A[LATE_GAME_INDEX] >= LATE_GAME_TRIGGER:
        if base_B[THWART_INDEX] > TARGET:
            score += LATE_GAME_THWART_BONUS * base_B[THWART_INDEX]

    # ----------------------------------
    # 4. Low survivability + support
    # ----------------------------------
    if base_A[SURVIVABILITY_INDEX] < TARGET:
        blocking_value = (
            max(0, base_B[SURVIVABILITY_INDEX]) +
            max(0, stats_B[SUPPORT_INDEX])
        )
        score += BLOCKING_SUPPORT_BONUS * blocking_value

    # ----------------------------------
    # 5. Power disincentives
    # ----------------------------------
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
        return "b_helps_a"
    else:
        return "a_helps_b"


# ----------------------------------------
# Select hero
# ----------------------------------------
hero_A = st.selectbox("Select a hero to view pairings:", hero_names)


# ----------------------------------------
# Selected hero visual + dynamic blurb
# ----------------------------------------
st.markdown("---")

hero_cols = st.columns([1, 3])

hero_power = general_scores[hero_A]
hero_stats = heroes[hero_A][:BASE_STAT_COUNT]
support_stat = heroes[hero_A][SUPPORT_INDEX]

BASELINE_LABELS = [
    "Economy",
    "Tempo",
    "Card Value",
    "Survivability",
    "Villain Damage",
    "Threat Removal",
    "Reliability",
    "Minion Control",
]

with hero_cols[0]:
    hero_img = hero_image_urls.get(hero_A)
    if hero_img:
        st.image(hero_img, use_container_width=True)

with hero_cols[1]:
    st.markdown(
        f"<h1 style='margin-bottom:0;'>Best Partners for {hero_A}</h1>",
        unsafe_allow_html=True
    )

    weaknesses = [
        name for name, val in zip(BASELINE_LABELS, hero_stats)
        if val < WEAK_TEXT_THRESHOLD
    ]

    strengths = [
        name for name, val in zip(BASELINE_LABELS, hero_stats)
        if val > STRONG_TEXT_THRESHOLD
    ]

    if support_stat < 0:
        blurb = (
            f"<p><strong>{hero_A}</strong> needs "
            f"<strong>significant help from their teammate</strong> "
            f"to be reliably strong. Pair them with "
            f"<strong>strong support heroes</strong>.</p>"
        )

    elif hero_power <= WEAK_HERO_THRESHOLD:
        blurb = (
            f"<p><strong>{hero_A}</strong> benefits greatly from a "
            f"<strong>strong, stabilizing partner</strong>. "
            f"These pairings focus on covering weaknesses "
            f"in <em>{', '.join(weaknesses[:2]) if weaknesses else 'key areas'}</em>.</p>"
        )

    elif hero_power >= STRONG_HERO_THRESHOLD:
        blurb = (
            f"<p><strong>{hero_A}</strong> is a powerful hero who can "
            f"<strong>support weaker or more specialized partners</strong>, "
            f"especially in <em>{', '.join(strengths[:2]) if strengths else 'multiple areas'}</em>.</p>"
        )

    else:
        blurb = (
            f"<p><strong>{hero_A}</strong> is a flexible, well-rounded hero. "
            f"These pairings emphasize <strong>balanced, mutually beneficial partnerships</strong>.</p>"
        )

    st.markdown(blurb, unsafe_allow_html=True)

st.markdown("---")


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

    blended = PRIMARY_WEIGHT * a_to_b + SECONDARY_WEIGHT * b_to_a

    pairing_type = classify_pairing(a_to_b, b_to_a)

    if pairing_type == "mutual":
        blended *= (1 + S_TIER_RECIPROCITY_BOOST)

    scores[hero_B] = blended
    details[hero_B] = {"type": pairing_type}


# ----------------------------------------
# Tiering
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
# Display tiers
# ----------------------------------------
tier_colors = {
    "S": "#FF69B4",
    "A": "purple",
    "B": "#3CB371",
    "C": "#FF8C00",
    "D": "red",
}

num_cols = 5

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

                t = details[hero]["type"]
                if t == "mutual":
                    st.caption("🤝 Mutual synergy")
                elif t == "b_helps_a":
                    st.caption("⬆️ Supports you")
                elif t == "a_helps_b":
                    st.caption("⬇️ You support them")
                else:
                    st.caption("—")
