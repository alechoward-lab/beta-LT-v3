"""
Hero Recommender — Tell us what matters to you and we'll find the best hero for your playstyle.
"""

import streamlit as st
import numpy as np
from data.hero_image_urls import hero_image_urls
from data.hero_decks import hero_decks
from data.help_tips import help_tips
from data.constants import STAT_NAMES, HERO_ALTER_EGOS
from components.hero_stats_manager import get_heroes
from components.nav_banner import render_nav_banner, render_page_header, render_footer
from components.github_storage import load_json
from components.hero_card_viewer import show_hero_cards_button

render_nav_banner("hero-recommender")

render_page_header("Hero Recommender", "Tell us what you value and we'll find the best heroes for your playstyle")


# ─── Community-tier helper: bucket heroes by Hero Power community submissions ───
_TIER_PTS_RC = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1}

@st.cache_data(ttl=600, show_spinner=False)
def _community_hero_buckets():
    """Return ({hero: avg_tier_pts}, {bucket_name: set(heroes)}).

    Buckets by community Hero Power tier list:
      strong = A-S (avg >= 4.5)
      average = C-B (3.0 <= avg < 4.5)
      weak    = F-D (avg < 3.0)
    """
    try:
        data, _ = load_json("community_tier_lists.json", default={})
    except Exception:
        return {}, {"strong": set(), "average": set(), "weak": set()}
    subs = (data.get("hero_power", {}) or {}).get("submissions", []) or []
    if len(subs) < 2:
        return {}, {"strong": set(), "average": set(), "weak": set()}
    pts_by_hero = {}
    for sub in subs:
        for tier, hero_list in (sub or {}).items():
            pt = _TIER_PTS_RC.get(tier)
            if pt is None:
                continue
            for h in (hero_list or []):
                pts_by_hero.setdefault(h, []).append(pt)
    avg = {h: float(np.mean(v)) for h, v in pts_by_hero.items() if v}
    buckets = {"strong": set(), "average": set(), "weak": set()}
    for h, a in avg.items():
        if a >= 4.5:
            buckets["strong"].add(h)
        elif a >= 3.0:
            buckets["average"].add(h)
        else:
            buckets["weak"].add(h)
    return avg, buckets


_BUCKET_BY_PREF = {
    "Weak / Off-meta": "weak",
    "Average / Balanced": "average",
    "Strong / Top-tier": "strong",
}



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

    # ── Restrict candidate pool by community tier list bucket ──
    comm_avg, comm_buckets = _community_hero_buckets()
    target_bucket = _BUCKET_BY_PREF.get(hero_strength, "average")
    bucket_set = comm_buckets.get(target_bucket, set())
    bucket_filtered = False
    if bucket_set:
        filtered_pool = {h: s for h, s in heroes_pool.items() if h in bucket_set}
        # Only restrict if we have a reasonable number of candidates
        if len(filtered_pool) >= 3:
            heroes_pool = filtered_pool
            bucket_filtered = True

    # Compute raw stat sum for each hero to blend with strength preference
    raw_sums = {h: float(np.sum(s)) for h, s in heroes_pool.items()}
    sum_vals = np.array(list(raw_sums.values()))
    sum_mean, sum_std = sum_vals.mean(), max(sum_vals.std(), 1e-6)
    # z-score of each hero's total stats
    norm_sums = {h: (raw_sums[h] - sum_mean) / sum_std for h in heroes_pool}

    # When the community-tier bucket already constrains the pool, soften the
    # strength bias so we don't double-penalise inside the bucket.
    effective_bias = strength_bias * (0.4 if bucket_filtered else 1.0)
    scores = {
        hero: float(np.dot(stats, w)) + effective_bias * norm_sums[hero] * 10
        for hero, stats in heroes_pool.items()
    }
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    st.session_state.rec_results = ranked[:5]
    st.session_state.rec_weights = w.copy()
    st.session_state.rec_bucket = target_bucket if bucket_filtered else None
    st.session_state.rec_comm_avg = comm_avg

if st.session_state.get("rec_results"):
    top5 = st.session_state.rec_results
    st.markdown("---")
    st.markdown("### 🏆 Your Top 5 Recommended Heroes")

    _bucket_used = st.session_state.get("rec_bucket")
    if _bucket_used:
        _label = {"strong": "A–S (Strong / Top-tier)",
                  "average": "B–C (Average / Balanced)",
                  "weak": "D–F (Weak / Off-meta)"}.get(_bucket_used, _bucket_used)
        st.caption(f"🎯 Filtered to community tier {_label} based on your preference.")

    # Cropped hero card style (matches tier list builder)
    st.markdown(
        """<style>
        [data-testid="stVerticalBlock"]:has(.compact-cards) [data-testid="stImage"] {
            overflow: hidden !important;
            aspect-ratio: 1.153;
        }
        [data-testid="stVerticalBlock"]:has(.compact-cards) [data-testid="stImage"] img {
            width: 100% !important;
            height: auto !important;
        }
        </style>""",
        unsafe_allow_html=True,
    )

    _comm_avg = st.session_state.get("rec_comm_avg") or {}
    all_heroes = get_heroes()
    for rank, (hero, score) in enumerate(top5, 1):
        col_img, col_info = st.columns([1, 3])
        with col_img:
            st.markdown('<div class="compact-cards"></div>', unsafe_allow_html=True)
            img = hero_image_urls.get(hero)
            if img:
                st.image(img, width="stretch")
        with col_info:
            tier_badge = ""
            if hero in _comm_avg:
                _avg = _comm_avg[hero]
                _t = min(_TIER_PTS_RC.keys(), key=lambda t: abs(_TIER_PTS_RC[t] - _avg))
                tier_badge = f"  &nbsp;·&nbsp; Community Tier **{_t}**"
            st.markdown(f"**#{rank} — {hero}** &nbsp; (Score: {int(score)}){tier_badge}")

            stats = all_heroes.get(hero)
            if stats is not None:
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

            show_hero_cards_button(
                hero,
                alter_ego_hint=HERO_ALTER_EGOS.get(hero, ""),
                key=f"rec_cards_{rank}_{hero}",
                label="View Cards",
            )

        st.markdown("---")

    with st.expander("See the weighting generated from your answers"):
        saved_w = st.session_state.get("rec_weights", w)
        for i, f in enumerate(FACTORS):
            st.write(f"**{f}:** {int(saved_w[i])}")

render_footer()
