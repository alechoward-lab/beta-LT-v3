"""
The Living Marvel Champions Tier List
"""
#%%
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import copy
import os
from PIL import Image
import json
from hero_image_urls import hero_image_urls
from default_heroes import default_heroes
from preset_options import preset_options
from help_tips import help_tips

# ----------------------------------------
# App Header and Socials Banner
# ----------------------------------------
st.title("The Living Tier List")
st.subheader("For Marvel Champions Heroes by Daring Lime")
st.markdown(
    "Adjust the weighting based on how much you value each aspect of hero strength. "
    "You can choose from preset weighting functions, adjust the sliders manually, or both! "
    "After updating the hero stats and weighting factors to your liking, you can save your settings and upload them next time you return to the site."
)
st.markdown(
    "For a video tutorial of how to use this, check out this YouTube video: [Daring Lime](https://youtu.be/TxU1NcryRS8). "
    "If you enjoy this tool, please consider subscribing to support more Marvel Champions content."
)

socials_banner = st.markdown(
    """
    <style>...YOUR CSS HERE...</style>
    <div class="social-bar">...YOUR HTML HERE...</div>
    """, unsafe_allow_html=True
)

# ----------------------------------------
# Weighting Presets and Sliders
# ----------------------------------------
stat_keys = [
    "Economy","Tempo","Card Value","Survivability","Villain Damage",
    "Threat Removal","Reliability","Minion Control","Control Boon","Support Boon",
    "Unique Broken Builds Boon","Late Game Power Boon","Simplicity","Stun/Confuse Boon",
    "Multiplayer Consistency Boon"
]

# Callback to load preset values
def update_preset():
    preset = st.session_state.preset_choice
    if preset != "Custom":
        vals = preset_options[preset]
        for i, key in enumerate(stat_keys):
            st.session_state[key] = int(vals[i])

with st.expander("Edit Weighting Factors"):
    preset_choice = st.selectbox(
        "Select Weighting Option", list(preset_options.keys()) + ["Custom"],
        key="preset_choice", on_change=update_preset
    )
    # sliders
    for key in stat_keys:
        st.slider(
            key, min_value=-10, max_value=10,
            value=st.session_state.get(key, int(preset_options[preset_choice][stat_keys.index(key)] if preset_choice != "Custom" else 0)),
            key=key,
            help=help_tips.get(key, "")
        )
    # build weighting array
    weighting = np.array([st.session_state[key] for key in stat_keys])
    # Download button omitted for brevity

# ----------------------------------------
# Hero Stats Initialization
# ----------------------------------------
if "heroes" not in st.session_state:
    st.session_state.heroes = copy.deepcopy(default_heroes)

heroes = st.session_state.heroes

# ----------------------------------------
# Calculate Scores and Tiers
# ----------------------------------------
def compute_score(stats, w):
    return np.dot(stats, w)

# Ensure weighting defined
if 'weighting' not in locals():
    weighting = np.array([st.session_state[key] for key in stat_keys])

scores = {h: compute_score(stats, weighting) for h, stats in heroes.items()}
sorted_scores = dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))

arr = np.array(list(scores.values()))
m, s = arr.mean(), arr.std()
thresholds = {'S': m+1.5*s, 'A': m+0.5*s, 'B': m-0.5*s, 'C': m-1.5*s}

tiers = {k: [] for k in ['S','A','B','C','D']}
for hero, sc in scores.items():
    if sc >= thresholds['S']:
        tiers['S'].append((hero, sc))
    elif sc >= thresholds['A']:
        tiers['A'].append((hero, sc))
    elif sc >= thresholds['B']:
        tiers['B'].append((hero, sc))
    elif sc >= thresholds['C']:
        tiers['C'].append((hero, sc))
    else:
        tiers['D'].append((hero, sc))
for t in tiers: tiers[t].sort(key=lambda x: x[1], reverse=True)

# ----------------------------------------
# Display Tier List with Images
# ----------------------------------------
plot_title = st.session_state.get('preset_choice', 'Custom')
st.header(plot_title)
colors = {'S':'red','A':'orange','B':'green','C':'blue','D':'purple'}
for level in ['S','A','B','C','D']:
    st.markdown(f"<h2>{level}</h2>", unsafe_allow_html=True)
    rows = [tiers[level][i:i+5] for i in range(0, len(tiers[level]), 5)]
    for row in rows:
        cols = st.columns(5)
        for idx, (hero, _) in enumerate(row):
            with cols[idx]:
                path = hero_image_urls.get(hero)
                if path and os.path.exists(path):
                    st.image(Image.open(path), caption=hero, use_container_width=True)
                else:
                    st.write(f"Image for {hero} not found.")

# ----------------------------------------
# Plot Hero Scores
# ----------------------------------------
fig, ax = plt.subplots(figsize=(14,7), dpi=300)
names, vals = zip(*sorted_scores.items())
bars = ax.bar(names, vals, color=[colors[next(t for t in tiers if hero in dict(tiers[t]))] for hero in names])
ax.set_ylabel("Scores", fontsize="x-large")
ax.set_title(plot_title, fontsize=18, fontweight='bold')
plt.xticks(rotation=45, ha='right')
legend_handles = [Patch(color=c, label=f"Tier {t}") for t, c in colors.items()]
ax.legend(handles=legend_handles, loc='upper left', fontsize='x-large', title="Tier")
ax.grid(axis='y', linestyle='--', alpha=0.7)
st.pyplot(fig)

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("-Stay Zesty")
st.markdown("Thank you for using this tool!")
