"""
Hero Recommender — Tell us what matters to you and we'll find the best hero for your playstyle.
"""

import streamlit as st
import numpy as np
from data.hero_image_urls import hero_image_urls
from data.hero_decks import hero_decks
from data.help_tips import help_tips
from data.constants import STAT_NAMES
from components.hero_stats_manager import get_heroes
from components.nav_banner import render_nav_banner, render_page_header, render_footer

render_nav_banner("hero-recommender")

render_page_header("Hero Recommender", "Tell us what you value and we'll find the best heroes for your playstyle")



# ─── Factor names (from shared constants) ───
FACTORS = STAT_NAMES

# Factors actually shown in the questionnaire (no boons, no simplicity)
ASKED_FACTORS = [
    "Economy", "Tempo", "Card Value", "Survivability", "Villain Damage",
    "Threat Removal", "Reliability", "Minion Control",
]

IMPORTANCE_OPTIONS = ["Not important", "Somewhat important", "Very important"]
IMPORTANCE_WEIGHTS = {"Not important": 0, "Somewhat important": 3, "Very important": 6}

# ─── Meta preferences ───
st.markdown("---")
st.markdown("#### Quick Preferences")
hero_strength = st.radio(
    "**What kind of hero are you looking for?**",
    ["Weak / Off-meta", "Average / Balanced", "Strong / Top-tier"],
    index=2,
    horizontal=True,
    help="This adjusts whether the recommender favours heroes with high overall stats or more niche picks.",
)

simplicity_pref = st.radio(
    "**How simple do you want the hero to be?**",
    ["Complex is fine", "No preference", "Keep it simple"],
    index=1,
    horizontal=True,
    help="Simple heroes have fewer moving parts and are easier to pick up.",
)

player_count = st.radio(
    "**How many players do you usually play with?**",
    ["Solo", "2 Players", "3–4 Players"],
    horizontal=True,
)

# ─── Per-stat importance radios (core stats only) ───
st.markdown("---")
st.markdown("**How important is each of the following to you?**")

stat_importance = {}
for factor in ASKED_FACTORS:
    tip = help_tips.get(factor, "")
    stat_importance[factor] = st.radio(
        f"**{factor}**" + (f"  \n*{tip}*" if tip else ""),
        IMPORTANCE_OPTIONS,
        index=1,
        horizontal=True,
        key=f"rec_{factor}",
    )

# ─── Build weighting from answers ───
# Start with zeros for all 15 factors
w = np.zeros(len(FACTORS), dtype=float)
for i, f in enumerate(FACTORS):
    if f in stat_importance:
        w[i] = IMPORTANCE_WEIGHTS[stat_importance[f]]

# Apply simplicity preference (index 12)
if simplicity_pref == "Keep it simple":
    w[12] = 6.0
elif simplicity_pref == "Complex is fine":
    w[12] = -3.0
# else: stays 0

# Layer on player-count modifier
if player_count == "Solo":
    w += np.array([2, 1, 0, 1, 0, 1, 1, 0, 0, -2, 0, 0, 0, 1, -3])
elif player_count == "2 Players":
    w += np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0])
else:  # 3-4
    w += np.array([0, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 1, 0, 0, 3])

# ─── Apply hero strength filter ───
if hero_strength == "Weak / Off-meta":
    # Penalise heroes whose raw stat sum is high, favouring niche picks
    strength_bias = -1.0
elif hero_strength == "Average / Balanced":
    strength_bias = 0.0
else:  # Strong / Top-tier
    strength_bias = 1.0

# ─── Score heroes ───
if st.button("🔍 Find My Heroes!", type="primary", width="stretch"):
    all_heroes = get_heroes()
    heroes_pool = dict(all_heroes)

    # Compute raw stat sum for each hero to blend with strength preference
    raw_sums = {h: float(np.sum(s)) for h, s in heroes_pool.items()}
    sum_vals = np.array(list(raw_sums.values()))
    sum_mean, sum_std = sum_vals.mean(), max(sum_vals.std(), 1e-6)
    # z-score of each hero's total stats
    norm_sums = {h: (raw_sums[h] - sum_mean) / sum_std for h in heroes_pool}

    scores = {
        hero: float(np.dot(stats, w)) + strength_bias * norm_sums[hero] * 10
        for hero, stats in heroes_pool.items()
    }
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    st.session_state.rec_results = ranked[:5]
    st.session_state.rec_weights = w.copy()

if st.session_state.get("rec_results"):
    top5 = st.session_state.rec_results
    st.markdown("---")
    st.markdown("### 🏆 Your Top 5 Recommended Heroes")

    for rank, (hero, score) in enumerate(top5, 1):
        col_img, col_info = st.columns([1, 3])
        with col_img:
            img = hero_image_urls.get(hero)
            if img:
                st.image(img, width="stretch")
        with col_info:
            st.markdown(f"**#{rank} — {hero}** &nbsp; (Score: {int(score)})")

            stats = all_heroes.get(hero, get_heroes()[hero])
            top_stats = sorted(
                [(FACTORS[i], int(stats[i])) for i in range(len(FACTORS)) if stats[i] > 0],
                key=lambda x: x[1], reverse=True,
            )[:3]
            strengths = ", ".join(f"{name} ({val:+d})" for name, val in top_stats)
            st.markdown(f"*Strengths:* {strengths}")

            deck_entries = hero_decks.get(hero, [])
            if deck_entries:
                links = " · ".join(f"[{e['name']}]({e['url']})" for e in deck_entries)
                st.markdown(f"📋 Decks: {links}")

        st.markdown("---")

    with st.expander("See the weighting generated from your answers"):
        saved_w = st.session_state.get("rec_weights", w)
        for i, f in enumerate(FACTORS):
            st.write(f"**{f}:** {int(saved_w[i])}")

render_footer()
