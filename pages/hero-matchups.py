
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from copy import deepcopy
import io

from villain_weights import villain_weights
from villain_image_urls import villain_image_urls
from default_heroes import default_heroes
from hero_image_urls import hero_image_urls
from villain_strategies import villain_strategies
from hero_stats_manager import initialize_hero_stats, get_heroes, render_hero_stats_editor

# Initialize hero stats in session state
initialize_hero_stats()

st.markdown("**Watch the video tutorial here:** [Video Tutorial](https://youtu.be/9eEMPnSwVLw)")
st.markdown("**Join the Discord to ask questions or give feedback:** [Discord Invite](https://discord.gg/ReF5jDSHqV)")

# Hero stats editor
render_hero_stats_editor(key_prefix="hero_matchups")
st.markdown("---")

# ----------------------------------------
# Page header
# ----------------------------------------
plot_title = "Hero Villain Matchup Tier List"
st.title(plot_title)
st.subheader("Choose a hero from the dropdown menu to see which villains are easiest or hardest for them!")

# ----------------------------------------
# Factor names (ORDER MATTERS)
# ----------------------------------------
factor_names = [
    "Economy",
    "Tempo",
    "Card Value",
    "Survivability",
    "Villain Damage",
    "Threat Removal",
    "Reliability",
    "Minion Control",
    "Control Boon",
    "Support Boon",
    "Unique Broken Builds Boon",
    "Late Game Power Boon",
    "Simplicity",
    "Stun/Confuse Boon",
    "Multiplayer Consistency Boon",
]

# ----------------------------------------
# Get heroes
# ----------------------------------------
heroes = get_heroes()
hero_names = sorted(list(default_heroes.keys()))

# ----------------------------------------
# Hero selector
# ----------------------------------------
selected_hero = st.selectbox("Select a Hero", hero_names)

if selected_hero not in heroes:
    st.error("Hero not found.")
    st.stop()

# ----------------------------------------
# Layout
# ----------------------------------------
col_img, col_content = st.columns(2)

with col_img:
    if selected_hero in hero_image_urls:
        st.image(hero_image_urls[selected_hero], use_container_width=True)
    else:
        st.write("No image available for this hero.")

with col_content:
    st.markdown(f"### {selected_hero}")
    st.markdown("This page shows how this hero matches up against each villain.")

# ----------------------------------------
# Get hero stats
# ----------------------------------------
hero_stats = heroes[selected_hero]

# ----------------------------------------
# Score villains against this hero
# ----------------------------------------
villain_names = sorted(list(villain_weights.keys()))
scores = {}

for villain_name in villain_names:
    villain_weights_array = np.array(villain_weights[villain_name])
    # Score is how well the hero performs against this villain
    score = float(np.dot(hero_stats, villain_weights_array))
    scores[villain_name] = score

sorted_scores = dict(sorted(scores.items(), key=lambda kv: kv[1], reverse=True))

# ----------------------------------------
# Tier thresholds
# ----------------------------------------
all_scores = np.array(list(scores.values()))
mean, std = all_scores.mean(), all_scores.std()

thr_S = mean + 1.5 * std
thr_A = mean + 0.5 * std
thr_B = mean - 0.5 * std
thr_C = mean - 1.5 * std

# Tier naming: S = Easy, A = Moderate, B = Challenging, C = Difficult, D = Very Difficult
tier_names = {
    "S": "Easy",
    "A": "Moderate",
    "B": "Challenging",
    "C": "Difficult",
    "D": "Very Difficult"
}

tiers = {"S": [], "A": [], "B": [], "C": [], "D": []}
for villain_name, sc in scores.items():
    if sc >= thr_S:
        tiers["S"].append((villain_name, sc))
    elif sc >= thr_A:
        tiers["A"].append((villain_name, sc))
    elif sc >= thr_B:
        tiers["B"].append((villain_name, sc))
    elif sc >= thr_C:
        tiers["C"].append((villain_name, sc))
    else:
        tiers["D"].append((villain_name, sc))

for tier in tiers:
    tiers[tier].sort(key=lambda x: x[1], reverse=True)

villain_to_tier = {v: t for t, lst in tiers.items() for v, _ in lst}

# ----------------------------------------
# Background CSS
# ----------------------------------------
bg = (
    "https://github.com/alechoward-lab/"
    "Marvel-Champions-Hero-Tier-List/blob/main/"
    "images/background/marvel_champions_background_image_v4.jpg?raw=true"
)

st.markdown(
    f"""
    <style>
      .stApp {{
        background: url({bg}) no-repeat center center fixed;
        background-size: cover;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------
# Tier grid
# ----------------------------------------
tier_colors = {
    "S": "#90EE90",  # Light green - Easy
    "A": "#87CEEB",  # Sky blue - Moderate
    "B": "#FFD700",  # Gold - Challenging
    "C": "#FF8C00",  # Dark orange - Difficult
    "D": "#FF4500",  # Red orange - Very Difficult
}

num_cols = 5

st.markdown("---")

for tier in ["S", "A", "B", "C", "D"]:
    members = tiers[tier]
    if not members:
        continue

    st.markdown(
        f"<h2 style='text-align: center; color: {tier_colors[tier]};'>"
        f"{tier_names[tier]}</h2>",
        unsafe_allow_html=True,
    )

    cols = st.columns(num_cols)

    for idx, (villain_name, score) in enumerate(members):
        col = cols[idx % num_cols]
        with col:
            # Villain image
            if villain_name in villain_image_urls:
                st.image(villain_image_urls[villain_name], use_container_width=True)
            else:
                st.write("No image")

            # Villain name and score
            st.markdown(
                f"<div style='text-align: center;'>"
                f"<b>{villain_name}</b><br>"
                f"<span style='color: {tier_colors[tier]}; font-size: 14px;'>"
                f"Score: {score:.1f}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")

# ----------------------------------------
# Summary statistics
# ----------------------------------------
st.subheader("📊 Matchup Summary")

summary_text = f"""
**{selected_hero}** has the following matchup spread:
- **Easy** villains: {len(tiers['S'])}
- **Moderate** villains: {len(tiers['A'])}
- **Challenging** villains: {len(tiers['B'])}
- **Difficult** villains: {len(tiers['C'])}
- **Very Difficult** villains: {len(tiers['D'])}

**Average Matchup Score:** {mean:.1f}
"""

st.markdown(summary_text)
