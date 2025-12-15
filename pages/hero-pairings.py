"""
Need to add extra wweight to high tempo being paired with low tempo characters.

Need to add the  background from the home page.
"""
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from copy import deepcopy

from default_heroes import default_heroes
from hero_image_urls import hero_image_urls

# ----------------------------------------
# Page header
# ----------------------------------------
st.title("Hero Pairings (2-Player Synergy)")
st.subheader(
    "Select a hero to see which other heroes best cover their weaknesses in multiplayer."
)

st.markdown(
    "This is a **beta build**. These pairings are not to be taken as good at this point. Also, it doesn't currently account for specific syergies. "
)

# ----------------------------------------
# Load hero data
# ----------------------------------------
heroes = deepcopy(default_heroes)
hero_names = list(heroes.keys())

# ----------------------------------------
# Select primary hero
# ----------------------------------------
hero_A = st.selectbox("Select Primary Hero", hero_names)
stats_A = heroes[hero_A]

# ----------------------------------------
# Define weakness threshold
# ----------------------------------------
TARGET = 2  # anything below this is a weakness

# Compute Hero A weaknesses (needs)
needs = np.maximum(0, TARGET - stats_A)

# ----------------------------------------
# Score partner heroes (TRUE SYNERGY)
# ----------------------------------------
scores = {}

for hero_B, stats_B in heroes.items():
    if hero_B == hero_A:
        continue

    # Partner can only contribute where Hero A is weak
    usable_strengths = np.minimum(
        np.maximum(0, stats_B),  # partner must be positive
        needs                     # and actually needed
    )

    # Core synergy score
    score = np.dot(needs, usable_strengths)

    # Normalize so heroes with many weaknesses don't inflate scores
    score /= (np.sum(needs) + 1e-6)

    scores[hero_B] = score

# ----------------------------------------
# Sort scores
# ----------------------------------------
sorted_scores = dict(sorted(scores.items(), key=lambda kv: kv[1]))

# ----------------------------------------
# Tier thresholds (dynamic)
# ----------------------------------------
vals = np.array(list(scores.values()))
mean, std = vals.mean(), vals.std()

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
        for idx, (hero, score) in enumerate(row):
            with cols[idx]:
                img = hero_image_urls.get(hero)
                if img:
                    st.image(img, use_container_width=True)
                #st.markdown(f"**Synergy Score:** {score:.2f}")

# ----------------------------------------
# Bar chart of synergy scores
# ----------------------------------------
st.header("Synergy Scores")

names = list(sorted_scores.keys())
vals = list(sorted_scores.values())
colors = [tier_colors[hero_to_tier[h]] for h in names]

fig, ax = plt.subplots(figsize=(14, 7), dpi=200)
ax.bar(names, vals, color=colors)
ax.set_ylabel("Synergy Score")
ax.set_title(
    f"Hero Pairing Synergy with {hero_A}",
    fontsize=18,
    fontweight="bold"
)
plt.xticks(rotation=45, ha="right")

for lbl in ax.get_xticklabels():
    lbl.set_color(tier_colors[hero_to_tier[lbl.get_text()]])

handles = [Patch(color=c, label=f"Tier {t}") for t, c in tier_colors.items()]


background_image_path = "images/background/marvel_champions_background_image_v2.jpg"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("{background_image_path}");
        background-repeat: no-repeat;
        background-position: center;
        background-attachment: fixed;
        background-size: cover;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

ax.legend(handles=handles, title="Tiers", loc="upper left")
st.pyplot(fig)
