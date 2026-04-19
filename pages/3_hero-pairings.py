"""
Hero Pairings — Mutually Aware, Direction-Aware UX Version
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

# Baseline indices
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

WEAK_TEXT_THRESHOLD = 2
STRONG_TEXT_THRESHOLD = 3


# ----------------------------------------
# Imports
# ----------------------------------------
import streamlit as st
import numpy as np
import random
from copy import deepcopy

from data.default_heroes import default_heroes
from data.hero_image_urls import hero_image_urls
from data.constants import TIER_COLORS
from components.weighting_utils import initialize_weighting_stats, get_weighting_array, render_weighting_sliders
from components.collection_filter import render_collection_filter
from components.nav_banner import render_nav_banner, render_page_header, render_footer
from data.hero_release_order import HERO_WAVE, WAVE_ORDER, HERO_LEGACY, LEGACY_WAVE_ORDER

render_nav_banner("hero-pairings")
render_collection_filter()


# ----------------------------------------
# Initialize Weighting Stats
# ----------------------------------------
initialize_weighting_stats()

render_page_header("Hero Pairings", "Find balanced, mutually beneficial partnerships where both heroes succeed")

# ----------------------------------------
# Weighting Controls
# ----------------------------------------
with st.expander("Adjust Weighting Factors (click to expand)", expanded=False):
    render_weighting_sliders(show_help=st.session_state.get("show_help", True))

# ----------------------------------------
# Load Data
# ----------------------------------------
heroes = deepcopy(default_heroes)
hero_names = list(heroes.keys())


# ----------------------------------------
# Compute General Power
# ----------------------------------------
general_weights = get_weighting_array()

general_scores = {
    hero: float(np.dot(stats, general_weights))
    for hero, stats in heroes.items()
}

gp_vals = np.array(list(general_scores.values()))
gp_mean = gp_vals.mean()
gp_std = gp_vals.std()

STRONG_HERO_THRESHOLD = gp_mean + 0.5 * gp_std
WEAK_HERO_THRESHOLD = gp_mean - 0.5 * gp_std


# ----------------------------------------
# Directional Synergy
# ----------------------------------------
def directional_synergy(hero_A, hero_B):
    stats_A = heroes[hero_A]
    stats_B = heroes[hero_B]

    base_A = stats_A[:BASE_STAT_COUNT]
    base_B = stats_B[:BASE_STAT_COUNT]

    power_A = general_scores[hero_A]
    power_B = general_scores[hero_B]

    score = 0.0

    # Weakness coverage
    needs = np.maximum(0, TARGET - base_A)
    usable = np.minimum(np.maximum(0, base_B), needs)

    if np.sum(needs) > 0:
        score += np.dot(needs, usable) / np.sum(needs)

    # Tempo contrast
    score += TEMPO_PAIR_BONUS * abs(
        base_A[TEMPO_INDEX] - base_B[TEMPO_INDEX]
    )

    # Late game + thwart
    if stats_A[LATE_GAME_INDEX] >= LATE_GAME_TRIGGER:
        if base_B[THWART_INDEX] > TARGET:
            score += LATE_GAME_THWART_BONUS * base_B[THWART_INDEX]

    # Survivability + support
    if base_A[SURVIVABILITY_INDEX] < TARGET:
        score += BLOCKING_SUPPORT_BONUS * (
            max(0, base_B[SURVIVABILITY_INDEX]) +
            max(0, stats_B[SUPPORT_INDEX])
        )

    # Power disincentives
    if power_A >= STRONG_HERO_THRESHOLD and power_B >= STRONG_HERO_THRESHOLD:
        score *= POWER_DISINCENTIVE

    if power_A <= WEAK_HERO_THRESHOLD and power_B <= WEAK_HERO_THRESHOLD:
        score *= WEAK_PAIR_DISINCENTIVE

    return score


# ----------------------------------------
# Pairing Classification
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
# Select Hero (image grid)
# ----------------------------------------
if "pairings_hero" not in st.session_state:
    st.session_state.pairings_hero = random.choice(hero_names)

hero_A = st.session_state.pairings_hero

with st.expander(f"▸ {hero_A} — tap to change hero", expanded=False):
    fmt_col, wave_col, _ = st.columns([1, 1, 1])
    with fmt_col:
        picker_fmt = st.selectbox(
            "Format",
            ["Current", "Legacy"],
            index=1,
            key="pairings_fmt_filter",
            label_visibility="collapsed",
        )
    if picker_fmt == "Current":
        picker_heroes = [h for h in hero_names if not HERO_LEGACY.get(h, False)]
    else:
        # Legacy includes ALL heroes (current + legacy)
        picker_heroes = hero_names[:]
        with wave_col:
            picker_wave = st.multiselect(
                "Filter by waves",
                WAVE_ORDER,
                key="pairings_wave_filter",
                placeholder="All Waves",
            )
        if picker_wave:
            picker_heroes = [h for h in picker_heroes if HERO_WAVE.get(h) in picker_wave]
    cols_per_row = 6
    for i in range(0, len(picker_heroes), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(picker_heroes):
                break
            hero = picker_heroes[idx]
            with col:
                img_path = hero_image_urls.get(hero, "")
                if img_path:
                    st.image(img_path, width="stretch")
                if st.button(hero, key=f"pair_btn_{hero}", width="stretch"):
                    st.session_state.pairings_hero = hero
                    st.rerun()


# ----------------------------------------
# Score Partners
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
# Pick Random Recommended Partner (A/S) — persist in session state
# ----------------------------------------
top_partners = tiers["S"] + tiers["A"]
_partner_key = f"_rec_partner_{hero_A}"
if top_partners and (st.session_state.get(_partner_key) not in top_partners):
    st.session_state[_partner_key] = random.choice(top_partners)
recommended_partner = st.session_state.get(_partner_key) if top_partners else None


# ----------------------------------------
# Hero Display + Blurb + Recommendation
# ----------------------------------------
st.markdown("---")

left, middle, right = st.columns([1, 2, 1])

hero_stats = heroes[hero_A][:BASE_STAT_COUNT]
support_stat = heroes[hero_A][SUPPORT_INDEX]
hero_power = general_scores[hero_A]

BLURB_STATS = [
    ("Tempo", TEMPO_INDEX),
    ("Villain Damage", VILLAIN_DAMAGE_INDEX),
    ("Threat Removal", THWART_INDEX),
    ("Reliability", RELIABILITY_INDEX),
    ("Minion Control", MINION_CONTROL_INDEX),
]

with left:
    img = hero_image_urls.get(hero_A)
    if img:
        st.image(img, width="stretch")

with middle:
    st.markdown(
        f"<h2 style='margin-bottom:0;'>Best Partners for {hero_A}</h2>",
        unsafe_allow_html=True
    )

    weaknesses = [
        name for name, idx in BLURB_STATS
        if hero_stats[idx] < WEAK_TEXT_THRESHOLD
    ]

    strengths = [
        name for name, idx in BLURB_STATS
        if hero_stats[idx] > STRONG_TEXT_THRESHOLD
    ]

    if support_stat < 0:
        blurb = (
            f"<p><strong>{hero_A}</strong> needs significant help from their "
            f"teammate to be reliably strong. Pair them with "
            f"<strong>strong support heroes</strong>.</p>"
        )
    elif hero_power <= WEAK_HERO_THRESHOLD:
        blurb = (
            f"<p><strong>{hero_A}</strong> benefits greatly from a strong, "
            f"stabilizing partner that can help cover weaknesses in "
            f"<em>{', '.join(weaknesses[:2]) if weaknesses else 'key areas'}</em>.</p>"
        )
    elif hero_power >= STRONG_HERO_THRESHOLD:
        blurb = (
            f"<p><strong>{hero_A}</strong> is a powerful hero who can support "
            f"weaker or more specialized partners, especially through "
            f"<em>{', '.join(strengths[:2]) if strengths else 'multiple roles'}</em>.</p>"
        )
    else:
        blurb = (
            f"<p><strong>{hero_A}</strong> is a flexible, well-rounded hero. "
            f"These pairings emphasize balanced, mutually beneficial play.</p>"
        )

    if recommended_partner:
        blurb += (
            f"<p><strong>Try playing {hero_A} with "
            f"{recommended_partner}!</strong></p>"
        )

    st.markdown(blurb, unsafe_allow_html=True)

with right:
    if recommended_partner:
        img = hero_image_urls.get(recommended_partner)
        if img:
            st.image(img, width="stretch")


# ----------------------------------------
# Display Tiers
# ----------------------------------------
tier_colors = TIER_COLORS

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
                    st.image(img, width="stretch")

                t = details[hero]["type"]
                if t == "mutual":
                    st.caption("🤝 Mutual synergy")
                elif t == "b_helps_a":
                    st.caption("⬆️ Supports you")
                elif t == "a_helps_b":
                    st.caption("⬇️ You support them")
                else:
                    st.caption("—")

render_footer()
