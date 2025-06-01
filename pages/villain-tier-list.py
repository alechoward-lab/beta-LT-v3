Skip to content
You said:
IN this code, I want to display the weighting factors in a scrollable element that's the same width as the villain card image next to the villain card.

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
st.subheader("Choose a villain from the dropdown menu to see a custom hero tier list for defeating them!")

# ----------------------------------------
# Villain selector & portrait
# ----------------------------------------
villain = st.selectbox("Select a Villain", list(villain_weights.keys()))
if villain in villain_image_urls:
    st.image(villain_image_urls[villain], width=200, caption=villain)

if villain not in villain_weights:
    st.error("No weighting defined for that villain yet.")
    st.stop()

weighting = np.array(villain_weights[villain])

# ----------------------------------------
# Score heroes
# ----------------------------------------
heroes = deepcopy(default_heroes)  # dict of {name: np.array([...])}
scores = {name: float(np.dot(stats, weighting)) for name, stats in heroes.items()}
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
    if   sc >= thr_S:        tiers["S"].append((hero, sc))
    elif sc >= thr_A:        tiers["A"].append((hero, sc))
    elif sc >= thr_B:        tiers["B"].append((hero, sc))
    elif sc >= thr_C:        tiers["C"].append((hero, sc))
    else:                    tiers["D"].append((hero, sc))

for tier in tiers:
    tiers[tier].sort(key=lambda x: x[1], reverse=True)

# Map each hero to its tier (for coloring)
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

    st.markdown(f"<h2 style='color:{tier_colors[tier]};'>Tier {tier}</h2>", unsafe_allow_html=True)

    # break into rows of num_cols
    rows = [members[i : i + num_cols] for i in range(0, len(members), num_cols)]
    for row in rows:
        cols = st.columns(num_cols)
        for idx, (hero, score) in enumerate(row):
            with cols[idx]:
                # hero portrait
                img_url = hero_image_urls.get(hero)
                if img_url:
                    st.image(img_url, use_container_width=True)
                # hero name, tier letter, and score
                st.markdown(
                    f"Score: {int(score)}",
                    unsafe_allow_html=True
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

# color-code the x-labels
for lbl in ax.get_xticklabels():
    hero = lbl.get_text()
    lbl.set_color(tier_colors.get(hero_to_tier.get(hero, ""), "black"))

# legend
handles = [Patch(color=c, label=f"Tier {t}") for t, c in tier_colors.items()]
ax.legend(handles=handles, title="Tiers", loc="upper left", fontsize=12, title_fontsize=12)

st.pyplot(fig)
ChatGPT said:

Thought for 6 seconds
Below is one way to show the weighting‐factor array in a scrollable box right beside the villain’s portrait. The trick is to use st.columns so that the image and the weights live in two side‐by‐side columns of the same “fractional” width, and then render the weights inside a st.text_area (which becomes scrollable once the text exceeds the given height). For example:

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
# Villain selector & portrait + weights box
# ----------------------------------------
villain = st.selectbox("Select a Villain", list(villain_weights.keys()))

if villain not in villain_weights:
    st.error("No weighting defined for that villain yet.")
    st.stop()

# Get the raw weighting array for this villain
weights = np.array(villain_weights[villain])

# Create two equal‐width columns so that the image and the scrollable area line up.
col_img, col_weights = st.columns([1, 1])

with col_img:
    # If there’s an image URL, show it at width=200px
    if villain in villain_image_urls:
        st.image(villain_image_urls[villain], width=200, caption=villain)

with col_weights:
    # Convert the weights array into a newline‐separated string (or however you like)
    weights_str = "\n".join(f"{w:.3f}" for w in weights)
    # st.text_area becomes scrollable if content > height
    st.text_area(
        label="Weighting Factors",
        value=weights_str,
        height=200,    # adjust height (in px) until the scroll‐bar appears
        help="These are the raw weights used to score each hero."
    )

# ----------------------------------------
# Score heroes (unchanged)
# ----------------------------------------
heroes = deepcopy(default_heroes)  # dict of {name: np.array([...])}
scores = {name: float(np.dot(stats, weights)) for name, stats in heroes.items()}
sorted_scores = dict(sorted(scores.items(), key=lambda kv: kv[1]))

# ----------------------------------------
# Compute dynamic tier thresholds (unchanged)
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
# Display Tiered Grid of Hero Portraits (unchanged)
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

    # break into rows of `num_cols`
    rows = [members[i : i + num_cols] for i in range(0, len(members), num_cols)]
    for row in rows:
        cols = st.columns(num_cols)
        for idx, (hero, score) in enumerate(row):
            with cols[idx]:
                img_url = hero_image_urls.get(hero)
                if img_url:
                    st.image(img_url, use_container_width=True)
                st.markdown(
                    f"Score: {int(score)}",
                    unsafe_allow_html=True,
                )

# ----------------------------------------
# Bar Chart of Scores (unchanged)
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

# color‐code x‐labels
for lbl in ax.get_xticklabels():
    hero = lbl.get_text()
    lbl.set_color(tier_colors.get(hero_to_tier.get(hero, ""), "black"))

# legend
handles = [Patch(color=c, label=f"Tier {t}") for t, c in tier_colors.items()]
ax.legend(handles=handles, title="Tiers", loc="upper left", fontsize=12, title_fontsize=12)

st.pyplot(fig)
Why this works
st.columns([1, 1]):
By passing [1, 1], you create two side‐by‐side columns of equal “fractional” width. In practice, Streamlit will split the available horizontal space evenly. Because the villain image is shown at a fixed width of 200 px, the left column will “shrink” around it, and the right column will be the same width by definition of the fractional layout.

st.text_area(..., height=200):
A text_area widget will automatically add a vertical scrollbar whenever the text inside exceeds the given height. Since we put all of the numerical weights (one per line) in a single string, it will scroll once it overflows its 200 px height. You can tweak the height= argument (e.g. 150, 250, etc.) to taste.

String formatting of weights:
In the example above, we do "\n".join(f"{w:.3f}" for w in weights) so that each weight lives on its own line with three decimals. Feel free to format however you like (commas, decimals, labels, etc.).

If you’d rather have a custom‐styled HTML box instead of a text_area, you can do something like:

with col_weights:
    weights_html = "<br>".join(f"{w:.3f}" for w in weights)
    st.markdown(
        f"""
        <div style="
            width: 200px;
            height: 200px;
            overflow-y: auto;
            border: 1px solid #ccc;
            padding: 8px;
            background: rgba(255,255,255,0.8);
        ">
            {weights_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
In that alternative block:

We wrap the numbers in a <div> with overflow-y: auto; plus fixed width and height, so it scrolls once the content is larger than 200 px tall.

Because the image above is fixed at width=200, the <div> can also be set to width: 200px and line up perfectly.

Either approach will give you a scrollable “weights panel” that matches the villain portrait’s width.

You said:
make it integer values and display the name of each weighting factor as well. 
ChatGPT said:

Thought for 6 seconds
Below is the same pattern as before, except now each weight is cast to an integer and paired with its “factor name.” In this example I’ve assumed you have a list called factor_names whose order matches the entries in each villain_weights[villain] array. Simply replace factor_names = [...] with whatever labels your weights correspond to.

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
# Example: if each weight corresponds to [Strength, Defense, Willpower, Attack, Health]
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
# Villain selector & portrait + weights box
# ----------------------------------------
villain = st.selectbox("Select a Villain", list(villain_weights.keys()))

if villain not in villain_weights:
    st.error("No weighting defined for that villain yet.")
    st.stop()

# Raw weighting array for this villain
weights = np.array(villain_weights[villain])

# Make sure our labels match the length of the weights array
if len(factor_names) != len(weights):
    st.error(
        f"Number of factor names ({len(factor_names)}) does not match number of weights ({len(weights)})."
    )
    st.stop()

# Two equal-width columns: left for portrait, right for scrollable weight list
col_img, col_weights = st.columns([1, 1])

with col_img:
    if villain in villain_image_urls:
        st.image(villain_image_urls[villain], width=200, caption=villain)

with col_weights:
    # Build a newline-separated string of "Name: IntegerValue"
    weights_str = "\n".join(
        f"{name}: {int(w)}" for name, w in zip(factor_names, weights)
    )
    st.text_area(
        label="Weighting Factors (integers)",
        value=weights_str,
        height=200,  # adjust so that a scrollbar appears when there are many lines
        help="Each line shows a factor name and its integer weight.",
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

# --------------------------------------



No file chosenNo file chosen
ChatGPT can make mistakes. Check important info.
ChatGPT is still generating a response...
