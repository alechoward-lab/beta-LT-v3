
"""
The Living Marvel Champions Tier List
"""
#%%
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

socials_banner = st.markdown(
    """
    <style>
        .social-bar {
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: transparent; /* Transparent background */
            padding: 5px;
            border: 2px solid white; /* White border */
            border-radius: 8px;
            box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
        }
        .social-bar .left-content {
            display: flex;
            align-items: center;
            margin-right: auto; /* Aligns logo and text to the left */
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
            margin-right: 20px; /* Increased margin between logos */
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
# Define update_preset callback so that selecting a weighting preset updates slider values.
# ----------------------------------------
def update_preset():
    preset = st.session_state.preset_choice
    if preset != "Custom":
        preset_vals = preset_options[preset]
        st.session_state["economy"] = int(preset_vals[0])
        st.session_state["tempo"] = int(preset_vals[1])
        st.session_state["card_value"] = int(preset_vals[2])
        st.session_state["survivability"] = int(preset_vals[3])
        st.session_state["villain_damage"] = int(preset_vals[4])
        st.session_state["threat_removal"] = int(preset_vals[5])
        st.session_state["reliability"] = int(preset_vals[6])
        st.session_state["minion_control"] = int(preset_vals[7])
        st.session_state["control"] = int(preset_vals[8])
        st.session_state["support"] = int(preset_vals[9])
        st.session_state["unique_builds"] = int(preset_vals[10])
        st.session_state["late_game"] = int(preset_vals[11])
        st.session_state["simplicity"] = int(preset_vals[12])
        st.session_state["status_cards"] = int(preset_vals[13])
        st.session_state["multiplayer_consistency"] = int(preset_vals[14])

# ----------------------------------------
# Main App Content Header
# ----------------------------------------
st.title("The Living Tier List")
st.subheader("For Marvel Champions Heroes by Daring Lime")

st.markdown(
    "Adjust the weighting based on how much you value each aspect of hero strength. "
    "You can choose from preset weighting functions, adjust the sliders manually, or both! "
    "The weighting factors represent how much you personally value each stat, which is used to calculate "
    "a personalized hero tier list. After updating the hero stats and weighting factors to your liking, you can save your settings and upload them next time you return to the site. "
)
st.markdown(
    "For a video tutorial of how to use this, check out this YouTube video: [Daring Lime](https://youtu.be/TxU1NcryRS8). "
    "If you enjoy this tool, please consider subscribing to support more Marvel Champions content."
)

# ----------------------------------------
# Layout: Two columns side by side
# ----------------------------------------
col1, col2 = st.columns(2)
# ----------------------------------------
# Column 1: Weighting settings with separate upload expander
# ----------------------------------------
with col1:
    with st.expander("Upload Weighting Settings (click to expand)"):
        uploaded_weighting = st.file_uploader("Upload Weighting Settings", type="json", key="upload_weighting")
        if uploaded_weighting is not None:
            weighting_settings = json.load(uploaded_weighting)
            for key in ["preset_choice", "economy", "tempo", "card_value", "survivability",
                        "villain_damage", "threat_removal", "reliability", "minion_control",
                        "control", "support", "unique_builds", "late_game", "simplicity",
                        "status_cards", "multiplayer_consistency"]:
                if key in weighting_settings:
                    st.session_state[key] = weighting_settings[key]
            if "weighting" in weighting_settings:
                st.session_state.weighting = np.array(weighting_settings["weighting"])
            st.success("Weighting settings loaded successfully!")
    
    with st.expander("Edit Weighting Factors (click to expand)"):        
        # Select weighting preset and sliders
        preset_choice = st.selectbox(
            "Select Weighting Option", 
            list(preset_options.keys()) + ["Custom"],
            key="preset_choice",
            on_change=update_preset
        )
        
        economy = st.slider("Economy", min_value=-10, max_value=10,
                            value=st.session_state.get("economy", 4), key="economy")
        tempo = st.slider("Tempo", min_value=-10, max_value=10,
                          value=st.session_state.get("tempo", 2), key="tempo")
        card_value = st.slider("Card Value", min_value=-10, max_value=10,
                               value=st.session_state.get("card_value", 2), key="card_value")
        survivability = st.slider("Survivability", min_value=-10, max_value=10,
                                  value=st.session_state.get("survivability", 2), key="survivability")
        villain_damage = st.slider("Villain Damage", min_value=-10, max_value=10,
                                   value=st.session_state.get("villain_damage", 1), key="villain_damage")
        threat_removal = st.slider("Threat Removal", min_value=-10, max_value=10,
                                   value=st.session_state.get("threat_removal", 2), key="threat_removal")
        reliability = st.slider("Reliability", min_value=-10, max_value=10,
                                value=st.session_state.get("reliability", 3), key="reliability")
        minion_control = st.slider("Minion Control", min_value=-10, max_value=10,
                                   value=st.session_state.get("minion_control", 1), key="minion_control")
        control = st.slider("Control Boon", min_value=-10, max_value=10,
                            value=st.session_state.get("control", 2), key="control")
        support = st.slider("Support Boon", min_value=-10, max_value=10,
                            value=st.session_state.get("support", 2), key="support")
        unique_builds = st.slider("Unique Broken Builds Boon", min_value=-10, max_value=10,
                                  value=st.session_state.get("unique_builds", 1), key="unique_builds")
        late_game = st.slider("Late Game Power Boon", min_value=-10, max_value=10,
                              value=st.session_state.get("late_game", 1), key="late_game")
        simplicity = st.slider("Simplicity", min_value=-10, max_value=10,
                               value=st.session_state.get("simplicity", 0), key="simplicity")
        status_cards = st.slider("Stun/Confuse Boon", min_value=-10, max_value=10,
                                 value=st.session_state.get("status_cards", 0), key="status_cards")
        multiplayer_consistency = st.slider("Multiplayer Consistency Boon", min_value=-10, max_value=10,
                                             value=st.session_state.get("multiplayer_consistency", 0), key="multiplayer_consistency")
        
        # Create the weighting array from slider values
        weighting = np.array([
            st.session_state.get("economy", 4),
            st.session_state.get("tempo", 2),
            st.session_state.get("card_value", 2),
            st.session_state.get("survivability", 2),
            st.session_state.get("villain_damage", 1),
            st.session_state.get("threat_removal", 2),
            st.session_state.get("reliability", 3),
            st.session_state.get("minion_control", 1),
            st.session_state.get("control", 2),
            st.session_state.get("support", 2),
            st.session_state.get("unique_builds", 1),
            st.session_state.get("late_game", 1),
            st.session_state.get("simplicity", 0),
            st.session_state.get("status_cards", 0),
            st.session_state.get("multiplayer_consistency", 0)
        ])
        
        # Determine plot title from preset
        if preset_choice != "Custom":
            plot_title = f"{preset_choice}"
        else:
            plot_title = "Custom Weighting"
        
        # Download button to save weighting settings
        weighting_settings = {
            "preset_choice": st.session_state.preset_choice,
            "economy": st.session_state.economy,
            "tempo": st.session_state.tempo,
            "card_value": st.session_state.card_value,
            "survivability": st.session_state.survivability,
            "villain_damage": st.session_state.villain_damage,
            "threat_removal": st.session_state.threat_removal,
            "reliability": st.session_state.reliability,
            "minion_control": st.session_state.minion_control,
            "control": st.session_state.control,
            "support": st.session_state.support,
            "unique_builds": st.session_state.unique_builds,
            "late_game": st.session_state.late_game,
            "simplicity": st.session_state.simplicity,
            "status_cards": st.session_state.status_cards,
            "multiplayer_consistency": st.session_state.multiplayer_consistency,
            "weighting": weighting.tolist()
        }
        weighting_json = json.dumps(weighting_settings)
        st.download_button("Download Weighting Settings", weighting_json, "weighting_settings.json")

# ----------------------------------------
# Column 2: Hero Stats with separate upload expander
# ----------------------------------------
with col2:
    with st.expander("Upload Hero Stats (click to expand)"):
        uploaded_hero_stats = st.file_uploader("Upload Hero Stats", type="json", key="upload_hero_stats")
        if uploaded_hero_stats is not None:
            hero_stats_settings = json.load(uploaded_hero_stats)
            if "heroes" in hero_stats_settings:
                st.session_state.heroes = {hero: np.array(stats) for hero, stats in hero_stats_settings["heroes"].items()}
            if "default_heroes" in hero_stats_settings:
                st.session_state.default_heroes = {hero: np.array(stats) for hero, stats in hero_stats_settings["default_heroes"].items()}
            st.success("Hero stats loaded successfully!")
    
    with st.expander("Edit Hero Stats (click to expand)"):
        # Initialize hero stats if not set
        if "heroes" not in st.session_state:
            st.session_state.heroes = copy.deepcopy(default_heroes)
            st.session_state.default_heroes = copy.deepcopy(default_heroes)
        
        # List of stat names
        stat_names = ["Economy", "Tempo", "Card Value", "Survivability", "Villain Damage",
                      "Threat Removal", "Reliability", "Minion Control", "Control Boon", "Support Boon",
                      "Unique Broken Builds Boon", "Late Game Power Boon", "Simplicity", "Stun/Confuse Boon",
                      "Multiplayer Consistency Boon"]
        
        # Select a hero to modify (searchable dropdown)
        hero_to_modify = st.selectbox("Select a Hero to Modify", list(st.session_state.heroes.keys()), key="hero_choice")
        
        # Callback to update the current hero's stats automatically
        def update_current_hero_stats():
            new_stats = []
            for stat in stat_names:
                new_stats.append(st.session_state.get(f"{hero_to_modify}_{stat}", 0))
            st.session_state.heroes[hero_to_modify] = np.array(new_stats)
        
        # Display number inputs with automatic update on change
        current_stats = st.session_state.heroes[hero_to_modify]
        for i, stat in enumerate(stat_names):
            st.number_input(f"{hero_to_modify} - {stat}",
                            value=int(current_stats[i]),
                            min_value=-10, max_value=10,
                            key=f"{hero_to_modify}_{stat}",
                            on_change=update_current_hero_stats)
        
        # Button to update all heroes to match the selected hero's stats
        if st.button("Update All Heroes to These Stats"):
            new_stats = st.session_state.heroes[hero_to_modify]
            for hero in st.session_state.heroes.keys():
                st.session_state.heroes[hero] = np.array(new_stats)
            st.success("All hero stats updated to match the current hero.")
        
        # Button to reset all heroes to default
        if st.button("Reset All Heroes to Default"):
            st.session_state.heroes = copy.deepcopy(st.session_state.default_heroes)
            st.success("All heroes have been reset to their default stats.")
        
        # Download button to save hero stats settings
        hero_stats_to_save = {
            "heroes": {hero: stats.tolist() for hero, stats in st.session_state.heroes.items()},
            "default_heroes": {hero: stats.tolist() for hero, stats in st.session_state.default_heroes.items()}
        }
        hero_stats_json = json.dumps(hero_stats_to_save)
        st.download_button("Download Hero Stats", hero_stats_json, "hero_stats.json")

# ----------------------------------------
# Continue with Tier List Calculations & Display
# ----------------------------------------
heroes = st.session_state.heroes

# Define the path to hero images (update the path accordingly)
hero_images_path = "C:/Users/user/Desktop/MC_Code/MC_github/Marvel-Champions-Hero-Tier-List/images/heroes"
hero_images = {}
for hero in default_heroes.keys():
    image_path = os.path.join(hero_images_path, f"{hero.replace(' ', '_').replace('.', '').replace('(', '').replace(')', '').lower()}.png")
    if os.path.exists(image_path):
        hero_images[hero] = Image.open(image_path)
    else:
        hero_images[hero] = None

# ----------------------------------------
# Calculate Scores and Tiers using weighting and hero stats
# ----------------------------------------
def weight(hero_stats, weighting):
    return np.dot(hero_stats, weighting)

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

hero_to_tier = {}
for tier, heroes_list in tiers.items():
    for hero, _ in heroes_list:
        hero_to_tier[hero] = tier

# ----------------------------------------
# Add background image with custom CSS
# ----------------------------------------
background_image_url = "https://raw.githubusercontent.com/alechoward-lab/Marvel-Champions-Hero-Tier-List/refs/heads/main/images/background/marvel_champions_background_image.jpg"
st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url({background_image_url});
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        position: relative;
        padding: 40px;
        color: white;
    }}
    .stApp::before {{
        content: "";
        position: absolute;
        inset: 40px;
        background: rgba(0, 0, 0, 0.8);
        z-index: 1;
    }}
    .stApp > div {{
        position: relative;
        z-index: 2;
    }}
    .stApp, .stApp * {{
        color: white !important;
    }}
    .stApp .stSelectbox div[role="listbox"] * {{
        color: black !important;
    }}
    </style>
    """, 
    unsafe_allow_html=True
)

# ----------------------------------------
# Display Tier List with Images
# ----------------------------------------
st.header(f"{plot_title}")

tier_colors = {"S": "red", "A": "orange", "B": "green", "C": "blue", "D": "purple"}
for tier in ["S", "A", "B", "C", "D"]:
    st.markdown(f"<h2>{tier}</h2>", unsafe_allow_html=True)
    num_cols = 5
    rows = [tiers[tier][i:i + num_cols] for i in range(0, len(tiers[tier]), num_cols)]
    for row in rows:
        cols = st.columns(num_cols)
        for idx, (hero, score) in enumerate(row):
            with cols[idx]:
                if hero in hero_image_urls:
                    st.image(hero_image_urls[hero], width=150)

# ----------------------------------------
# Plotting
# ----------------------------------------
st.header("Hero Scores")
sorted_hero_names = list(sorted_scores.keys())
sorted_hero_scores = list(sorted_scores.values())
bar_colors = [tier_colors[hero_to_tier[hero]] for hero in sorted_hero_names]

fig, ax = plt.subplots(figsize=(14, 7), dpi=300)
bars = ax.bar(sorted_hero_names, sorted_hero_scores, color=bar_colors)
ax.set_ylabel("Scores", fontsize="x-large")
ax.set_title(plot_title, fontweight='bold', fontsize=18)
plt.xticks(rotation=45, ha='right')

for label in ax.get_xticklabels():
    hero = label.get_text()
    if hero in hero_to_tier:
        label.set_color(tier_colors[hero_to_tier[hero]])

legend_handles = [Patch(color=tier_colors[tier], label=f"Tier {tier}") for tier in tier_colors]
ax.legend(handles=legend_handles, title="Tier Colors", loc="upper left", fontsize='x-large', title_fontsize='x-large')
plt.tight_layout()
ax.grid(axis='y', linestyle='--', alpha=0.7)
st.pyplot(fig)
st.markdown("<hr>", unsafe_allow_html=True)

st.markdown(
    "The hero stats were determined by the merits of their identity-specific cards. You can modify any hero's stats "
    "along with the weighting sliders to create your own custom tier list. Upload your saved files to restore your settings."
)
st.markdown(
    "This tier list is living. If you want to have input on the future of this tier list, please join the [Daring Lime Discord](https://discord.gg/ReF5jDSHqV). "
    "I'll be updating the weighting factor presets and default hero stats based on community feedback."
)
st.markdown(
    "-Stay Zesty"
)
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("Most card images are from the Cerebro Discord bot developed by UnicornSnuggler. Thank you!")
