import streamlit as st
import numpy as np
import pandas as pd
from copy import deepcopy
from villain_weights import villain_weights
from default_heroes import default_heroes
from hero_image_urls import hero_image_urls

st.title("Tier List by Villain")
st.subheader("Choose a villain to see how heroes rank against them")

# Select villain
villain = st.selectbox("Select a Villain", list(villain_weights.keys()))

if villain not in villain_weights:
    st.error("Selected villain doesn't have weighting data yet.")
    st.stop()

weights = np.array(villain_weights[villain])

# Score heroes
heroes = deepcopy(default_heroes)
scored_heroes = []

for name, stats in heroes.items():
    score = float(np.dot(stats, weights))
    scored_heroes.append({
        "name": name,
        "score": score
    })

# Sort by score
sorted_heroes = sorted(scored_heroes, key=lambda h: h["score"], reverse=True)

# Output
st.markdown(f"### Hero Tier List vs. {villain}")
df = pd.DataFrame([
    {"Hero": h["name"], "Score": round(h["score"], 2)}
    for h in sorted_heroes
])
st.dataframe(df, use_container_width=True)

# Optional image display
with st.expander("Show Hero Images with Scores"):
    for hero in sorted_heroes:
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(hero_image_urls.get(hero["name"], ""), width=80)
        with col2:
            st.markdown(f"**{hero['name']}** — Score: {round(hero['score'], 2)}")
