import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import pandas as pd
import copy
import os
from PIL import Image
import json
from hero_image_urls import hero_image_urls
from default_heroes import default_heroes
from preset_options import preset_options
from help_tips import help_tips

# ----------------------------------------
# Socials banner (unchanged)
# ----------------------------------------
socials_banner = st.markdown(
    """
    <style>
        .social-bar {
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: transparent;
            padding: 5px;
            border: 2px solid white;
            border-radius: 8px;
            box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
        }
        .social-bar .left-content {
            display: flex;
            align-items: center;
            margin-right: auto;
        }
        .social-bar .left-content .logo {
            height: 40px;
            margin-right: 10px;
        }
        .social-bar .social-links {
            display: flex;
            justify-content: center;
        }
        .social-links a {
            margin-right: 20px;
            transition: opacity 0.3s ease-in-out;
        }
        .social-links a:hover {
            opacity: 0.7;
        }
        .social-text {
            font-family: Arial, sans-serif;
            font-size: 16px;
            font-weight: bold;
            margin-right: 15px;
            color: white;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);
        }
    </style>
    <div class="social-bar">
        <div class="left-content">
            <img class="logo" src="https://github.com/alechoward-lab/Marvel-Champions-Hero-Tier-List/blob/main/images/logo/Daring_Lime_Logo.png?raw=true" alt="Your Logo">
            <span class="social-text">Click the icons to see my YouTube channel and Discord:</span>
        </div>
        <div class="social-links">
            <a href="https://www.youtube.com/channel/UCpV2UWmBTAeIKUso1LkeU2A" target="_blank">
                <img src="https://github.com/alechoward-lab/Marvel-Champions-Hero-Tier-List/blob/main/images/logo/youtube_logo.png?raw=true" alt="YouTube" style="height: 30px;">
            </a>
            <a href="https://discord.gg/ReF5jDSHqV" target="_blank">
                <img src="https://github.com/alechoward-lab/Marvel-Champions-Hero-Tier-List/blob/main/images/logo/Discord-Logo.png?raw=true" alt="Discord" style="height: 30px;">
            </a>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------------------------------
# Preset update callback (unchanged)
# ----------------------------------------
def update_preset():
    preset = st.session_state.preset_choice
    if preset != "Custom":
        preset_vals = preset_options[preset]
        for i, key in enumerate(["Economy","Tempo","Card Value","Survivability","Villain Damage","Threat Removal","Reliability","Minion Control","Control Boon","Support Boon","Unique Broken Builds Boon","Late Game Power Boon","Simplicity","Stun/Confuse Boon","Multiplayer Consistency Boon"]):
            st.session_state[key] = int(preset_vals[i])

# ----------------------------------------
# Main App Content Header
# ----------------------------------------
st.title("The Living Tier List")
st.subheader("For Marvel Champions Heroes by Daring Lime")

st.markdown(
    "Adjust the weighting based on how much you value each aspect of hero strength. "
    "You can choose from preset weighting functions, adjust the sliders manually, or both! "
    "The weighting factors represent how much you personally value each stat, which is used to calculate "
    "a personalized hero tier list. After updating the hero stats and weighting factors to your liking, you can save your settings and upload them next time you return to the site."
)
st.markdown(
    "For a video tutorial of how to use this, check out this YouTube video: [Daring Lime](https://youtu.be/TxU1NcryRS8). "
    "If you enjoy this tool, please consider subscribing to support more Marvel Champions content."
)

# ----------------------------------------
# Layout: Two columns side by side
# ----------------------------------------
col1, col2 = st.columns(2)
with col1:
    with st.expander("Upload Weighting Settings (click to expand)"):
        uploaded_weighting = st.file_uploader("Upload Weighting Settings", type="json", key="upload_weighting")
        if uploaded_weighting:
            weighting_settings = json.load(uploaded_weighting)
            key_map = {"preset_choice":"preset_choice","economy":"Economy","tempo":"Tempo","card_value":"Card Value","survivability":"Survivability","villain_damage":"Villain Damage","threat_removal":"Threat Removal","reliability":"Reliability","minion_control":"Minion Control","control":"Control Boon","support":"Support Boon","unique_builds":"Unique Broken Builds Boon","late_game":"Late Game Power Boon","simplicity":"Simplicity","status_cards":"Stun/Confuse Boon","multiplayer_consistency":"Multiplayer Consistency Boon","weighting":"weighting"}
            for file_key, value in weighting_settings.items():
                mapped = key_map.get(file_key, file_key)
                st.session_state[mapped] = value
            if "weighting" in weighting_settings:
                st.session_state.weighting = np.array(weighting_settings["weighting"])
            st.success("Weighting settings loaded successfully!")
    with st.expander("Edit Weighting Factors (click to expand)"):
        st.markdown(
        "If you don't want a category to affect the list, set it to 0. If you set something negative, the heroes with negative stats will go up, and the heroes with positive stats will go down."
    )
        preset_choice = st.selectbox(
            "Select Weighting Option", 
            list(preset_options.keys()) + ["Custom"],
            key="preset_choice",
            on_change=update_preset
        )
        sliders = [st.slider(label, -10, 10, st.session_state.get(label, preset_options[preset_choice][i] if preset_choice!="Custom" else 0), key=label, help=help_tips[label]) for i, label in enumerate(["Economy","Tempo","Card Value","Survivability","Villain Damage","Threat Removal","Reliability","Minion Control","Control Boon","Support Boon","Unique Broken Builds Boon","Late Game Power Boon","Simplicity","Stun/Confuse Boon","Multiplayer Consistency Boon"])]

# ----------------------------------------
# Compute scores & tiers
# ----------------------------------------
weighting = np.array(sliders)

scores = {hero: float(np.dot(stats, weighting)) for hero, stats in default_heroes.items()}
sorted_scores = dict(sorted(scores.items(), key=lambda kv: kv[1]))
all_scores = np.array(list(scores.values()))
mean, std = all_scores.mean(), all_scores.std()
thr_S = mean + 1.5 * std
thr_A = mean + 0.5 * std
thr_B = mean - 0.5 * std
thr_C = mean - 1.5 * std

tiers = {"S":[],"A":[],"B":[],"C":[],"D":[]}
for h, sc in scores.items():
    if sc>=thr_S: tiers["S"].append((h,sc))
    elif sc>=thr_A: tiers["A"].append((h,sc))
    elif sc>=thr_B: tiers["B"].append((h,sc))
    elif sc>=thr_C: tiers["C"].append((h,sc))
    else: tiers["D"].append((h,sc))
for t in tiers: tiers[t].sort(key=lambda x: x[1], reverse=True)
hero_to_tier = {hero:t for t,l in tiers.items() for hero,_ in l}

# ----------------------------------------
# Background CSS
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
# Tiered Grid Display
# ----------------------------------------
st.markdown("### Tier List")
tier_colors = {"S":"red","A":"orange","B":"green","C":"blue","D":"purple"}
num_cols = 5
for tier in ["S","A","B","C","D"]:
    members = tiers[tier]
    if not members: continue
    st.markdown(f"<h2 style='color:{tier_colors[tier]};'>Tier {tier}</h2>", unsafe_allow_html=True)
    rows = [members[i:i+num_cols] for i in range(0, len(members), num_cols)]
    for row in rows:
        cols = st.columns(num_cols)
        for idx, (hero, score) in enumerate(row):
            with cols[idx]:
                img_url = hero_image_urls.get(hero)
                if img_url: st.image(img_url, use_container_width=True)
                st.markdown(f"**{hero}**  \nScore: {round(score,1)}")

# ----------------------------------------
# Bar Chart of Scores
# ----------------------------------------
st.header("Hero Scores (Bar Chart)")
names = list(sorted_scores.keys())
vals  = list(sorted_scores.values())
colors = [tier_colors[hero_to_tier[h]] for h in names]

fig, ax = plt.subplots(figsize=(14,7), dpi=200)
bars = ax.bar(names, vals, color=colors)
ax.set_title("Hero Tier List", fontsize=18, fontweight="bold")
ax.set_ylabel("Score", fontsize=14)
plt.xticks(rotation=45, ha="right")
for lbl in ax.get_xticklabels():
    lbl.set_color(tier_colors.get(hero_to_tier.get(lbl.get_text()), "black"))
handles = [Patch(color=c, label=f"Tier {t}") for t,c in tier_colors.items()]
ax.legend(handles=handles, title="Tiers", loc="upper left", fontsize=12, title_fontsize=12)
st.pyplot(fig)
