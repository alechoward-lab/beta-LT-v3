import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from copy import deepcopy

from villain_weights import villain_weights
from villain_image_urls import villain_image_urls
from default_heroes import default_heroes
from hero_image_urls import hero_image_urls
from villain_strategies import villain_strategies

st.markdown("**Watch the video tutorial here:** [Video Tutorial](https://youtu.be/9eEMPnSwVLw)")
st.markdown("**Join the Discord to ask questions or give feedback:** [Discord Invite](https://discord.gg/ReF5jDSHqV)")


# ----------------------------------------
# Page header
# ----------------------------------------
plot_title = "Villain Specific Hero Tier List"
st.title(plot_title)
st.subheader("Choose a villain from the dropdown menu to see a custom hero tier list for defeating them!")

# ----------------------------------------
# Factor names must match order/length of each villain_weights[villain] array
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
# Initialize any missing session_state keys to Rhino’s preset (prevents KeyError when returning)
# ----------------------------------------
rhino_preset = villain_weights.get("Rhino", [0] * len(factor_names))
for idx, name in enumerate(factor_names):
    if name not in st.session_state:
        st.session_state[name] = int(rhino_preset[idx])

# ----------------------------------------
# Villain selector
# ----------------------------------------
villain = st.selectbox("Select a Villain", list(villain_weights.keys()))
if villain not in villain_weights:
    st.error("No weighting defined for that villain yet.")
    st.stop()

# ----------------------------------------
# If the villain just changed (or on first load), load its preset into session_state
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
        st.session_state[name] = int(preset_array[idx])
    st.session_state["loaded_villain"] = villain

# ----------------------------------------
# Layout: two responsive columns for portrait + sliders/strategy
# ----------------------------------------
col_img, col_content = st.columns(2)

with col_img:
    if villain in villain_image_urls:
        st.image(villain_image_urls[villain], use_container_width=True)
    else:
        st.write("No image available for this villain.")

with col_content:
    # Expander containing all sliders
    with st.expander("Edit Weighting Factors"):
        st.markdown(
            "Use these sliders to adjust how much you value each factor. "
            "Defaults come from this villain’s preset."
        )
        for name in factor_names:
            st.slider(
                label=name,
                min_value=-10,
                max_value=10,
                value=st.session_state[name],
                key=name
            )

    # Section for strategy explanation
    st.markdown("### Strategy Tips")
    st.markdown(villain_strategies.get(villain, "No strategy tips written yet."))

# ----------------------------------------
# After sliders, gather the (possibly edited) weights
# ----------------------------------------
weights = np.array([st.session_state[name] for name in factor_names])

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
tier_colors = {
    "S": "#FF69B4",     # Hot Pink
    "A": "purple",
    "B": "#3CB371",     # MediumSeaGreen
    "C": "#FF8C00",     # DarkOrange
    "D": "red",
}
num_cols = 5

for tier in ["S", "A", "B", "C", "D"]:
    members = tiers[tier]
    if not members:
        continue

    st.markdown(
        f"<h2 style='color:{tier_colors[tier]};'>{tier} Tier</h2>",
        unsafe_allow_html=True,
    )

    # Break into rows of num_cols each
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
# Bar Chart of Hero Scores (with dynamic title)
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

# Color the x-axis labels based on tier
for lbl in ax.get_xticklabels():
    hero_label = lbl.get_text()
    lbl.set_color(tier_colors.get(hero_to_tier.get(hero_label, ""), "black"))

# Add legend for tiers
handles = [Patch(color=c, label=f"Tier {t}") for t, c in tier_colors.items()]
ax.legend(handles=handles, title="Tiers", loc="upper left", fontsize=12, title_fontsize=12)

st.pyplot(fig)
