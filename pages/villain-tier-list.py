import streamlit as st
import numpy as np
import pandas as pd
import json
from copy import deepcopy
from villain_weights import villain_weights
from default_heroes import default_heroes
from hero_image_urls import hero_image_urls

st.title("Tier List by Villain")
st.subheader("Choose a villain to see how heroes rank against them")

# ----------------------------------------
# Step 1: Villain Selection
# ----------------------------------------
villain = st.selectbox("Select a Villain", list(villain_weights.keys()))

if villain not in villain_weights:
    st.error("Selected villain doesn't have weighting data yet.")
    st.stop()

weights = np.array(villain_weights[villain])

# ----------------------------------------
# Step 2: Score Heroes Based on Villain Weights
# ----------------------------------------
heroes = deepcopy(default_heroes)

for hero in heroes:
    stats = np.array(hero["stats"])  # assuming 'stats' is a 15-element list
    score = float(np.dot(stats, weights))
    hero["score"] = score

# Sort heroes by score descending
sorted_heroes = sorted(heroes, key=lambda h: h["score"], reverse=True)

# ----------------------------------------
# Step 3: Output Tier List Table
# ----------------------------------------
st.markdown(f"### Results: Hero Tier List vs. {villain}")
df = pd.DataFrame([
    {
        "Hero": hero["name"],
        "Score": round(hero["score"], 2)
    } for hero in sorted_heroes
])
st.dataframe(df, use_container_width=True)

# Optional: Display hero images with scores
with st.expander("Show Hero Images with Scores"):
    for hero in sorted_heroes:
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(hero_image_urls.get(hero["name"], ""), width=80)
        with col2:
            st.markdown(f"**{hero['name']}** — Score: {round(hero['score'], 2)}")
