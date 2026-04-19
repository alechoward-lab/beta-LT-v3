import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from copy import deepcopy

from data.villain_weights import villain_weights
from data.villain_image_urls import villain_image_urls
from data.default_heroes import default_heroes
from data.hero_image_urls import hero_image_urls
from data.villain_strategies import villain_strategies
from data.hero_decks import hero_decks
from data.constants import STAT_NAMES, TIER_COLORS
import re
from components.collection_filter import render_collection_filter
from components.nav_banner import render_nav_banner, render_page_header, render_footer
from data.hero_release_order import HERO_WAVE, WAVE_ORDER, HERO_LEGACY, LEGACY_WAVE_ORDER

render_nav_banner("villain-tier-list")
render_collection_filter()

def format_strategy(text):
    """Format a strategy paragraph into bulleted markdown with bold keywords."""
    keywords = [
        "Stalwart", "Steady", "Surge", "Overkill", "Retaliate", "Piercing",
        "Guard", "Quickstrike", "Patrol", "Toughness", "Tough", "Crisis",
        "Amplify", "Hazard", "Incite",
    ]
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    lines = []
    for s in sentences:
        for kw in keywords:
            s = re.sub(rf'\b({kw})\b', rf'**\1**', s, flags=re.IGNORECASE)
        lines.append(f"- {s}")
    return "\n".join(lines)

render_page_header("Villain Tier List", "Choose a villain to see a custom hero tier list for defeating them")

st.markdown("**Video tutorial:** [Watch here](https://youtu.be/9eEMPnSwVLw) &nbsp;|&nbsp; **Discord:** [Join here](https://discord.gg/ReF5jDSHqV)")

plot_title = "Villain Specific Hero Tier List"

# ----------------------------------------
# Factor names (ORDER MATTERS)
# ----------------------------------------
factor_names = STAT_NAMES

# ----------------------------------------
# Villain selector
# ----------------------------------------
villain = st.selectbox("Select a Villain", list(villain_weights.keys()))

if villain not in villain_weights:
    st.error("No weighting defined for that villain yet.")
    st.stop()

# ----------------------------------------
# Load villain preset ON CHANGE
# ----------------------------------------
if st.session_state.get("loaded_villain") != villain:
    preset_array = villain_weights[villain]

    if len(preset_array) != len(factor_names):
        st.error(
            f"villain_weights['{villain}'] has length {len(preset_array)}, "
            f"but factor_names has length {len(factor_names)}."
        )
        st.stop()

    for idx, name in enumerate(factor_names):
        st.session_state[f"villain_{name}"] = int(preset_array[idx])

    st.session_state["loaded_villain"] = villain

# ----------------------------------------
# Layout
# ----------------------------------------
col_img, col_content = st.columns(2)

with col_img:
    if villain in villain_image_urls:
        st.image(villain_image_urls[villain], width="stretch")
    else:
        st.write("No image available for this villain.")

with col_content:
    with st.expander("Edit Weighting Factors"):
        st.markdown(
            "Use these sliders to adjust how much you value each factor. "
            "Defaults come from this villain's preset."
        )

        for name in factor_names:
            st.slider(
                label=name,
                min_value=-10,
                max_value=10,
                value=st.session_state.get(f"villain_{name}", 0),
                key=f"villain_{name}",
            )

    st.markdown("### Strategy Tips")
    raw_strategy = villain_strategies.get(villain, "No strategy tips written yet.")
    st.markdown(format_strategy(raw_strategy))

# ----------------------------------------
# Gather villain weights
# ----------------------------------------
weights = np.array([st.session_state.get(f"villain_{name}", 0) for name in factor_names])

# ----------------------------------------
# Score heroes
# ----------------------------------------
heroes = deepcopy(default_heroes)

# Apply collection filter
owned = st.session_state.get("owned_heroes")
if owned is not None:
    heroes = {h: s for h, s in heroes.items() if h in owned}

# Compute raw dot products once for the current villain weighting.
raw_scores = {name: float(np.dot(stats, weights)) for name, stats in heroes.items()}

# Format filter (primary) + Wave filter (secondary — Legacy-aware)
fmt_col, wave_col, _ = st.columns([1, 1, 1])
with fmt_col:
    villain_fmt_filter = st.selectbox(
        "Format",
        ["Current", "Legacy"],
        index=1,
        key="villain_fmt_filter",
        label_visibility="collapsed",
    )
if villain_fmt_filter == "Current":
    heroes = {h: s for h, s in heroes.items() if not HERO_LEGACY.get(h, False)}
else:
    # Legacy includes ALL heroes (current + legacy)
    with wave_col:
        villain_wave_filter = st.multiselect(
            "Filter by waves",
            WAVE_ORDER,
            key="villain_wave_filter",
            placeholder="All Waves",
        )
    if villain_wave_filter:
        heroes = {h: s for h, s in heroes.items() if HERO_WAVE.get(h) in villain_wave_filter}

scores = {name: raw_scores[name] for name in heroes}
sorted_scores = dict(sorted(scores.items(), key=lambda kv: (kv[1], kv[0])))

# ----------------------------------------
# Tier thresholds
# ----------------------------------------
all_scores = np.array(list(scores.values()), dtype=float)
mean, std = all_scores.mean(), all_scores.std()

thr_S = mean + 1.5 * std
thr_A = mean + 0.5 * std
thr_B = mean - 0.5 * std
thr_C = mean - 1.5 * std

tiers = {"S": [], "A": [], "B": [], "C": [], "D": []}
for hero, sc in scores.items():
    if sc >= thr_S:
        tiers["S"].append((hero, sc))
    elif sc >= thr_A:
        tiers["A"].append((hero, sc))
    elif sc >= thr_B:
        tiers["B"].append((hero, sc))
    elif sc >= thr_C:
        tiers["C"].append((hero, sc))
    else:
        tiers["D"].append((hero, sc))

for tier in tiers:
    tiers[tier].sort(key=lambda x: (-x[1], x[0]))

hero_to_tier = {h: t for t, lst in tiers.items() for h, _ in lst}



# ----------------------------------------
# Tier grid
# ----------------------------------------
tier_colors = TIER_COLORS

# Tiermaker block style CSS
st.markdown("""
<style>
.villain-tier-section .tier-label-block {
    background: var(--tier-color);
    color: #fff;
    font-weight: 900;
    font-size: 26px;
    text-align: center;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    aspect-ratio: 0.715;
}
.villain-tier-section [data-testid="stHorizontalBlock"] {
    gap: 2px !important;
    margin-bottom: 0 !important;
}
.villain-tier-section [data-testid="stColumn"] {
    padding: 0 !important;
}
.villain-tier-section [data-testid="stVerticalBlockBorderWrapper"],
.villain-tier-section [data-testid="stVerticalBlock"] {
    gap: 2px !important;
}
.villain-tier-section .stMarkdown,
.villain-tier-section [data-testid="stImage"],
.villain-tier-section [data-testid="stCaptionContainer"] {
    margin: 0 !important;
    padding: 0 !important;
}
</style>
""", unsafe_allow_html=True)

tier_hero_cols = 10
st.markdown('<div class="villain-tier-section">', unsafe_allow_html=True)
card_index = 0
for tier in ["S", "A", "B", "C", "D"]:
    members = tiers[tier]
    if not members:
        continue
    for row_start in range(0, max(len(members), 1), tier_hero_cols):
        row = members[row_start:row_start + tier_hero_cols] if members else []
        col_widths = [0.6] + [1] * tier_hero_cols
        cols = st.columns(col_widths, gap="small")
        with cols[0]:
            if row_start == 0:
                st.markdown(
                    f'<div class="tier-label-block" style="--tier-color:{tier_colors[tier]};">{tier}</div>',
                    unsafe_allow_html=True,
                )
        for k, (hero, score) in enumerate(row):
            with cols[k + 1]:
                img_url = hero_image_urls.get(hero)
                if img_url:
                    st.image(img_url, width="stretch")
                    card_index += 1
st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------
# Recommended Decks for Top Heroes
# ----------------------------------------
top_heroes = tiers["S"] + tiers["A"]
if top_heroes:
    with st.expander(f"📋 Recommended Decks for Top Heroes vs {villain}"):
        for hero, score in top_heroes:
            deck_entries = hero_decks.get(hero, [])
            if deck_entries:
                links = " · ".join(f"[{e['name']}]({e['url']})" for e in deck_entries)
                tier_label = "S" if (hero, score) in tiers["S"] else "A"
                st.markdown(f"**{hero}** ({tier_label}) — {links}")

# ----------------------------------------
# Bar chart
# ----------------------------------------
st.header("Villain Specific Hero Scores")

names = list(sorted_scores.keys())
vals = list(sorted_scores.values())
colors = [tier_colors[hero_to_tier[h]] for h in names]

fig, ax = plt.subplots(figsize=(14, 7), dpi=200)
ax.bar(names, vals, color=colors)
ax.set_title(f"Hero Scores Against {villain}", fontsize=18, fontweight="bold")
ax.set_ylabel("Score", fontsize=14)
plt.xticks(rotation=45, ha="right")

for lbl in ax.get_xticklabels():
    hero_label = lbl.get_text()
    lbl.set_color(tier_colors.get(hero_to_tier.get(hero_label, ""), "black"))

handles = [Patch(color=c, label=f"Tier {t}") for t, c in tier_colors.items()]
ax.legend(handles=handles, title="Tiers", loc="upper left", fontsize=12, title_fontsize=12)

st.pyplot(fig)
plt.close(fig)

render_footer(show_card_credits=True)


