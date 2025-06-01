import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import os
from copy import deepcopy
from villain_weights import villain_weights
from villain_image_urls import villain_image_urls
from default_heroes import default_heroes
from hero_image_urls import hero_image_urls

# ----------------------------------------
# Page header
# ----------------------------------------
plot_title = "Hero Tier List by Villain"
st.title(plot_title)
st.subheader(
    "Choose a villain from the dropdown menu to see a custom hero tier list for defeating them!"
)

# ----------------------------------------
# Define your factor names (must match length/order of each weighting array)
# ----------------------------------------
# Example: if each weight corresponds to [Economy, Tempo, Card Value, …]
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
    "Multiplayer Consistency Boon"
]

# ----------------------------------------
# Villain selector
# ----------------------------------------
villain = st.selectbox("Select a Villain", list(villain_weights.keys()))

if villain not in villain_weights:
    st.error("No weighting defined for that villain yet.")
    st.stop()

weights = np.array(villain_weights[villain])

if len(factor_names) != len(weights):
    st.error(
        f"Number of factor names ({len(factor_names)}) does not match number of weights ({len(weights)})."
    )
    st.stop()

# ----------------------------------------
# Two‐column layout: portrait (left) + scrollable weights (right)
# ----------------------------------------
col_img, col_weights = st.columns([1, 1])

with col_img:
    if villain in villain_image_urls:
        st.image(villain_image_urls[villain], width=200, caption=villain)

with col_weights:
    # Build a block of HTML containing each "Factor: IntegerValue" on its own line.
    items_html = "<br>".join(
        f"<strong>{name}:</strong> {int(w)}" for name, w in zip(factor_names, weights)
    )

    # Wrap in a styled <div> that matches your site’s aesthetic.
    st.markdown(
        f"""
        <div style="
            width: 200px;
            max-height: 240px;
            overflow-y: auto;
            border: 2px solid white;
            border-radius: 8px;
            padding: 8px;
            background-color: rgba(255, 255, 255, 0.85);
            box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
            font-family: Arial, sans-serif;
            color: #333;
        ">
            {items_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----------------------------------------
# Score heroes
# ----------------------------------------
heroes = deepcopy(default_heroes)  # dict of {name: np.array([...])}
scores = {name: float(np.dot(stats, weights)) for name, stats in heroes.items()}
sorted_scores = dict(sorted(scores.items(), key=lambda kv: kv[1]))

# ----------------------------------------
# Compute dynamic tier thresholds
# ----------------------------------------
all_scores = np.array(list(scores.values()))
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
    tiers[tier].sort(key=lambda x: x[1], reverse=True)

hero_to_tier = {h: t for t, lst in tiers.items() for h, _ in lst}

# ----------------------------------------
# Background CSS (unchanged)
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
# Display Tiered Grid of Hero Portraits
# ----------------------------------------
st.markdown(f"### Results: **{villain}** Preset → Tier List")

tier_colors = {"S": "purple", "A": "green", "B": "blue", "C": "orange", "D": "red"}
num_cols = 5

for tier in ["S", "A", "B", "C", "D"]:
    members = tiers[tier]
    if not members:
        continue

    st.markdown(
        f"<h2 style='color:{tier_colors[tier]};'>Tier {tier}</h2>",
        unsafe_allow_html=True,
    )

    rows = [members[i : i + num_cols] for i in range(0, len(members), num_cols)]
    for row in rows:
        cols = st.columns(num_cols)
        for idx, (hero, score) in enumerate(row):
            with cols[idx]:
                img_url = hero_image_urls.get(hero)
                if img_url:
                    st.image(img_url, use_container_width=True)
                st.markdown(f"Score: {int(score)}", unsafe_allow_html=True)

# ----------------------------------------
# Bar Chart of Scores
# ----------------------------------------
st.header("Hero Scores (Bar Chart)")
names = list(sorted_scores.keys())
vals = list(sorted_scores.values())
colors = [tier_colors[hero_to_tier[h]] for h in names]

fig, ax = plt.subplots(figsize=(14, 7), dpi=200)
bars = ax.bar(names, vals, color=colors)
ax.set_title(plot_title, fontsize=18, fontweight="bold")
ax.set_ylabel("Score", fontsize=14)
plt.xticks(rotation=45, ha="right")

for lbl in ax.get_xticklabels():
    hero = lbl.get_text()
    lbl.set_color(tier_colors.get(hero_to_tier.get(hero, ""), "black"))

handles = [Patch(color=c, label=f"Tier {t}") for t, c in tier_colors.items()]
ax.legend(handles=handles, title="Tiers", loc="upper left", fontsize=12, title_fontsize=12)

st.pyplot(fig)
