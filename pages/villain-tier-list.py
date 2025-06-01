import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
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
# Callback: load the selected villain's default weights into session_state
# ----------------------------------------
def load_villain_weights():
    v = st.session_state.villain_select
    vals = villain_weights[v]
    if len(vals) != len(factor_names):
        st.error(
            f"villain_weights for '{v}' has length {len(vals)}, but factor_names has length {len(factor_names)}."
        )
        st.stop()
    for name, w in zip(factor_names, vals):
        st.session_state[name] = int(w)
    st.session_state["loaded_villain"] = v

# ----------------------------------------
# Villain selector (with callback)
# ----------------------------------------
villain = st.selectbox(
    "Select a Villain",
    list(villain_weights.keys()),
    key="villain_select",
    on_change=load_villain_weights
)

# Ensure session_state is initialized on first run or when villain changes
if st.session_state.get("loaded_villain") != villain:
    load_villain_weights()

# ----------------------------------------
# Layout: two equal-width columns
# ----------------------------------------
col_img, col_weights = st.columns([1, 1])

with col_img:
    if villain in villain_image_urls:
        st.image(villain_image_urls[villain], width=200, caption=villain)
    else:
        st.write("No image available for this villain.")

with col_weights:
    # Expander for sliders
    with st.expander("Edit Weighting Factors"):
        st.markdown(
            "Use these sliders to tweak how much you value each factor. "
            "The default values come from this villain’s preset."
        )
        for name in factor_names:
            st.session_state[name] = st.slider(
                label=name,
                min_value=-10,
                max_value=10,
                value=st.session_state.get(name, 0),
                key=name
            )

    # Build HTML for a scrollable display of current weights
    lines = []
    for name in factor_names:
        val = st.session_state[name]
        lines.append(f"<strong>{name}:</strong> {val}")
    weights_html = "<br>".join(lines)

    # Scrollable container: fixed width=200px to match the villain image
    st.markdown(
        f"""
        <div style="
            width: 200px;
            height: 200px;
            overflow-y: auto;
            border: 1px solid #fff;
            border-radius: 8px;
            padding: 8px;
            background: rgba(255,255,255,0.8);
        ">
            {weights_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----------------------------------------
# Gather the (possibly edited) weights into a numpy array
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
                st.markdown(
                    f"Score: {int(score)}", unsafe_allow_html=True
                )

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
    hero_label = lbl.get_text()
    lbl.set_color(tier_colors.get(hero_to_tier.get(hero_label, ""), "black"))

handles = [Patch(color=c, label=f"Tier {t}") for t, c in tier_colors.items()]
ax.legend(handles=handles, title="Tiers", loc="upper left", fontsize=12, title_fontsize=12)

st.pyplot(fig)
