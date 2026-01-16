"""
Team Builder - Build a team of 1-4 heroes and analyze their combined strengths/weaknesses
"""

import streamlit as st
import numpy as np
import pandas as pd
from itertools import combinations
import matplotlib.pyplot as plt
from hero_image_urls import hero_image_urls
from villain_image_urls import villain_image_urls
from hero_stats_manager import initialize_hero_stats, get_heroes, render_hero_stats_editor
from preset_options import preset_options
from help_tips import help_tips
from villain_weights import villain_weights
from villain_strategies import villain_strategies

# Initialize hero stats in session state
initialize_hero_stats()

st.title("👥 Team Builder")
st.markdown("Build a team of 1-4 heroes and analyze their combined strengths and weaknesses!")

# Hero stats editor
render_hero_stats_editor(key_prefix="team_builder")
st.markdown("---")

# Get heroes
heroes = get_heroes()
hero_names = sorted(list(heroes.keys()))

# Initialize team in session state
if "team" not in st.session_state:
    st.session_state.team = []

# Villain selection (optional)
st.subheader("🦹 Villain Selection (Optional)")
st.markdown("Select a villain to rank teams specifically against their challenges:")

villain_names = sorted(list(villain_weights.keys()))
villain_choice = st.selectbox(
    "Choose a villain",
    ["No villain selected"] + villain_names,
    key="team_villain_choice"
)

if villain_choice != "No villain selected":
    weighting = np.array(villain_weights[villain_choice])
    
    # Display villain image and strategy
    col1, col2 = st.columns([1, 2])
    with col1:
        if villain_choice in villain_image_urls:
            st.image(villain_image_urls[villain_choice], use_container_width=True)
    with col2:
        st.info(f"🎯 Team strength is being evaluated against {villain_choice}")
        st.markdown("### Strategy Tips")
        st.markdown(villain_strategies.get(villain_choice, "No strategy tips written yet."))
else:
    weighting = np.ones(15)

st.markdown("---")

# Team building controls
st.subheader("🛠️ Build Your Team")
st.markdown(f"Current team size: {len(st.session_state.team)}/4")

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("**Click a hero card to add to team:**")
    available_heroes = [h for h in hero_names if h not in st.session_state.team]
    
    # Display heroes in rows of 5 images
    cols_per_row = 5
    for row_start in range(0, len(available_heroes), cols_per_row):
        row_end = min(row_start + cols_per_row, len(available_heroes))
        hero_row = available_heroes[row_start:row_end]
        cols = st.columns(cols_per_row)  # Always 5 columns
        
        for idx, hero in enumerate(hero_row):
            with cols[idx]:
                if hero in hero_image_urls:
                    st.image(hero_image_urls[hero], use_container_width=True)
                    if st.button("➕", key=f"add_{hero}", use_container_width=True):
                        if len(st.session_state.team) < 4:
                            st.session_state.team.append(hero)
                            st.rerun()
                        else:
                            st.error("Team is full! Maximum 4 heroes.")
                else:
                    st.write(f"**{hero}**")
                    if st.button("➕", key=f"add_{hero}", use_container_width=True):
                        if len(st.session_state.team) < 4:
                            st.session_state.team.append(hero)
                            st.rerun()
                        else:
                            st.error("Team is full! Maximum 4 heroes.")

with col2:
    st.write("")
    st.write("")
    if st.session_state.team and st.button("🗑️ Clear Team", key="clear_team_button", use_container_width=True):
        st.session_state.team = []
        st.rerun()

st.markdown("---")

if len(st.session_state.team) == 0:
    st.info("Add heroes to your team to get started!")
    st.stop()

# Display team
st.subheader("📋 Your Team")

# Dynamic columns based on team size
if len(st.session_state.team) == 1:
    cols = st.columns(1)
elif len(st.session_state.team) == 2:
    cols = st.columns(2)
elif len(st.session_state.team) == 3:
    cols = st.columns(3)
else:  # 4 or more
    cols = st.columns(min(4, len(st.session_state.team)))

for idx, hero in enumerate(st.session_state.team):
    with cols[idx % len(cols)]:
        if hero in hero_image_urls:
            st.image(hero_image_urls[hero], use_container_width=True)
        st.markdown(f"**{hero}**")
        
        if st.button("❌ Remove", key=f"remove_{hero}_{idx}"):
            st.session_state.team.remove(hero)
            st.rerun()

st.markdown("---")

# Balanced team analysis
st.subheader("⚖️ Team Balance Check")

balance_factors = {
    0: "Economy",
    1: "Tempo", 
    3: "Survivability",
    4: "Villain Damage",
    5: "Threat Removal",
    6: "Reliability",
    7: "Minion Control"
}

balance_stats = {}
for idx, name in balance_factors.items():
    avg_stat = np.mean([heroes[hero][idx] for hero in st.session_state.team])
    balance_stats[name] = avg_stat

# Display balance analysis
col1, col2, col3, col4 = st.columns(4)
columns = [col1, col2, col3, col4]

for idx, (name, avg_stat) in enumerate(balance_stats.items()):
    with columns[idx % 4]:
        if avg_stat > 2:
            st.success(f"{name}\n✅ {avg_stat:.1f} (Strong)")
        elif avg_stat >= 1:
            st.info(f"{name}\n🟢 {avg_stat:.1f} (Balanced)")
        else:
            st.error(f"{name}\n❌ {avg_stat:.1f} (Weak)")

st.markdown("---")

# Team tier ranking
st.subheader("🏆 Team Tier Ranking")

# Calculate team stats for scoring
team_stats = []
for hero in st.session_state.team:
    team_stats.append(heroes[hero])

combined_stats = np.mean(team_stats, axis=0)
team_score = float(np.dot(combined_stats, weighting))

# Calculate all possible team combinations and their scores
all_combinations = []
same_size_combinations = []

for team_size in range(1, 5):
    for combo in combinations(hero_names, team_size):
        combo_stats = np.mean([heroes[hero] for hero in combo], axis=0)
        combo_score = float(np.dot(combo_stats, weighting))
        all_combinations.append(combo_score)
        
        # Also track combinations of the same size for comparison
        if team_size == len(st.session_state.team):
            same_size_combinations.append(combo_score)

all_combinations = np.array(all_combinations)
mean_score = np.mean(all_combinations)
std_score = np.std(all_combinations)

# Also calculate stats for same-size teams for percentile ranking
if same_size_combinations:
    same_size_combinations = np.array(same_size_combinations)
    # Calculate rank: teams with higher score + 1 (since rank 1 is the best)
    teams_with_higher_score = np.sum(same_size_combinations > team_score)
    team_rank = teams_with_higher_score + 1
    total_teams = len(same_size_combinations)
else:
    team_rank = 1
    total_teams = 1

# Determine tier based on standard deviations
if team_score >= mean_score + 1.5 * std_score:
    tier = "S"
    tier_color = "red"
    tier_text = "Exceptional - Top 5%"
elif team_score >= mean_score + 0.5 * std_score:
    tier = "A"
    tier_color = "orange"
    tier_text = "Excellent - Top 25%"
elif team_score >= mean_score - 0.5 * std_score:
    tier = "B"
    tier_color = "green"
    tier_text = "Good - Average"
elif team_score >= mean_score - 1.5 * std_score:
    tier = "C"
    tier_color = "blue"
    tier_text = "Below Average - Bottom 25%"
else:
    tier = "D"
    tier_color = "purple"
    tier_text = "Weak - Bottom 5%"

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown(f"<h1 style='text-align: center; color: {tier_color};'>{tier}</h1>", unsafe_allow_html=True)

with col2:
    st.write("")
    st.write(tier_text)
    st.write(f"Score: {team_score:.1f}")
    st.write(f"Rank: {team_rank}/{total_teams} {len(st.session_state.team)}-player teams")

st.markdown("---")

# Individual hero scores
st.subheader("⚡ Individual Hero Scores")

hero_scores = []
for hero in st.session_state.team:
    score = float(np.dot(heroes[hero], weighting))
    hero_scores.append({"Hero": hero, "Score": f"{score:.1f}"})

df_scores = pd.DataFrame(hero_scores)
st.dataframe(df_scores, use_container_width=True, hide_index=True)

# Create bar chart for individual hero scores
fig, ax = plt.subplots(figsize=(18, 8), dpi=300)
hero_names_list = [item["Hero"] for item in hero_scores]
hero_scores_list = [float(item["Score"]) for item in hero_scores]
ax.bar(hero_names_list, hero_scores_list, color='steelblue')
ax.set_ylabel("Score", fontsize="x-large")
ax.set_title("Individual Hero Scores", fontweight='bold', fontsize=18)
plt.xticks(rotation=90, ha='right', fontsize='small')
plt.tight_layout()
ax.grid(axis='y', linestyle='--', alpha=0.7)
st.pyplot(fig)

st.markdown("---")

# Strengths and weaknesses
st.subheader("💪 Team Strengths & Weaknesses")

factor_names = [
    "Economy", "Tempo", "Card Value", "Survivability", "Villain Damage",
    "Threat Removal", "Reliability", "Minion Control", "Control Boon", "Support Boon",
    "Unique Broken Builds Boon", "Late Game Power Boon", "Simplicity", "Stun/Confuse Boon",
    "Multiplayer Consistency Boon"
]

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Top Strengths:**")
    strengths = []
    for i, factor in enumerate(factor_names):
        if combined_stats[i] >= 2:
            strengths.append((factor, combined_stats[i]))
    
    if strengths:
        for factor, val in sorted(strengths, key=lambda x: x[1], reverse=True)[:5]:
            st.write(f"- {factor}: {val:+.1f}")
    else:
        st.write("No major strengths")

with col2:
    st.markdown("**Main Weaknesses:**")
    weaknesses = []
    for i, factor in enumerate(factor_names):
        if combined_stats[i] <= -2:
            weaknesses.append((factor, combined_stats[i]))
    
    if weaknesses:
        for factor, val in sorted(weaknesses, key=lambda x: x[1])[:5]:
            st.write(f"- {factor}: {val:+.1f}")
    else:
        st.write("No major weaknesses")
