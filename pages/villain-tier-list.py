import streamlit as st
import numpy as np
import os
from PIL import Image
from copy import deepcopy
from villain_weights import villain_weights
from default_heroes import default_heroes

# ----------------------------------------
# Page Title and Villain Selection
# ----------------------------------------
st.title("Tier List by Villain")
st.subheader("Choose a villain to see how heroes rank against them")

villain = st.selectbox("Select a Villain", list(villain_weights.keys()))
if villain not in villain_weights:
    st.error("Selected villain doesn't have weighting data yet.")
    st.stop()

weighting = np.array(villain_weights[villain])
heroes = deepcopy(default_heroes)

# ----------------------------------------
# Hero Image Loading (Local Path)
# ----------------------------------------
hero_images_path = "images/heroes"  # Adjust if needed for your repo layout
hero_images = {}
for hero in heroes:
    image_name = hero.replace(' ', '_').replace('.', '').replace('(', '').replace(')', '').lower() + ".png"
    image_path = os.path.join(hero_images_path, image_name)
    if os.path.exists(image_path):
        hero_images[hero] = Image.open(image_path)
    else:
        hero_images[hero] = None

# ----------------------------------------
# Calculate Scores & Assign Tiers (mean ± stddev)
# ----------------------------------------
def weight(stats, weighting):
    return np.dot(stats, weighting)

scores = {hero: weight(stats, weighting) for hero, stats in heroes.items()}
sorted_scores = dict(sorted(scores.items(), key=lambda item: item[1]))

hero_scores = np.array(list(scores.values()))
mean_score = np.mean(hero_scores)
std_score = np.std(hero_scores)
threshold_S = mean_score + 1.5 * std_score
threshold_A = mean_score + 0.5 * std_score
threshold_B_lower = mean_score - 0.5 * std_score
threshold_C = mean_score - 1.5 * std_score

tiers = {"S": [], "A": [], "B": [], "C": [], "D": []}
for hero, score in scores.items():
    if score >= threshold_S:
        tiers["S"].append((hero, score))
    elif score >= threshold_A:
        tiers["A"].append((hero, score))
    elif score >= threshold_B_lower:
        tiers["B"].append((hero, score))
    elif score >= threshold_C:
        tiers["C"].append((hero, score))
    else:
        tiers["D"].append((hero, score))

for tier in tiers:
    tiers[tier] = sorted(tiers[tier], key=lambda x: x[1], reverse=True)

# ----------------------------------------
# Background Styling
# ----------------------------------------
background_image_url = "https://github.com/alechoward-lab/Marvel-Champions-Hero-Tier-List/blob/main/images/background/marvel_champions_background_image_v4.jpg?raw=true"
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

# ----------------------------------------
# Display Tiered Hero List
# ----------------------------------------
st.markdown(f"### Hero Tiers vs. **{villain}**")

for tier in ["S", "A", "B", "C", "D"]:
    if not tiers[tier]:
        continue

    st.markdown(f"#### {tier} Tier")
    tier_cols = st.columns(len(tiers[tier]))
    for col, (hero, score) in zip(tier_cols, tiers[tier]):
        with col:
            if hero_images[hero] is not None:
                st.image(hero_images[hero], width=120)
            st.markdown(f"**{hero}**  \nScore: {round(score, 2)}")
