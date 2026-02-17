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

def get_preset_for_team_size(team_size):
    """Get the appropriate preset based on team size."""
    if team_size == 1:
        return np.array(preset_options["Solo (No Rush)"])
    elif team_size == 2:
        return np.array(preset_options["General Power: 2 Player"])
    elif team_size == 3:
        return np.array(preset_options["Multiplayer: 3 Player"])
    else:  # 4 player
        return np.array(preset_options["Multiplayer: 4 Player"])

def calculate_team_synergy(team_heroes, heroes_dict, team_size):
    """
    Calculate team synergy bonus (0-40% multiplier).
    Synergy is based on how well heroes complement each other's strengths and weaknesses.
    
    Returns: synergy_multiplier (0.0 to 0.4)
    """
    if len(team_heroes) == 1:
        return 0.0  # No synergy for solo teams
    
    team_stats = np.array([heroes_dict[hero] for hero in team_heroes])
    
    # 1. Support synergy: Support heroes pair well with late game heroes
    # Support heroes enable other heroes to scale into late game
    support_boon_idx = 9  # Support Boon index
    late_game_idx = 11  # Late Game Power Boon index
    
    support_levels = team_stats[:, support_boon_idx]
    late_game_levels = team_stats[:, late_game_idx]
    
    avg_support = np.mean(support_levels)
    avg_late_game = np.mean(late_game_levels)
    
    # Synergy bonus if team has both support AND late game power
    support_synergy = min((avg_support + avg_late_game) / 100 * 0.12, 0.12)  # Cap at 12%
    
    # 2. Reliability synergy: Consistent heroes boost team stability
    reliability_idx = 6
    reliability = team_stats[:, reliability_idx]
    avg_reliability = np.mean(reliability)
    reliability_synergy = (avg_reliability / 6.0) * 0.08  # Up to 8%
    
    # 3. Multiplayer consistency synergy: Bonus for teams designed for multi-player
    multiplayer_idx = 14
    multiplayer_stats = team_stats[:, multiplayer_idx]
    
    if team_size >= 3:
        multiplayer_synergy = np.mean(multiplayer_stats) * 0.01  # 1% per multiplayer point
        multiplayer_synergy = min(multiplayer_synergy, 0.12)  # Cap at 12%
    else:
        multiplayer_synergy = 0.0
    
    # 4. Balance synergy: Diverse stat profiles work better together
    stat_variance = np.std(team_stats[:, :8])  # Variance across core stats
    balance_synergy = min((stat_variance / 3.0) * 0.08, 0.08)  # Up to 8%
    
    # Combine all synergies (cap at 40%)
    total_synergy = min(
        support_synergy + reliability_synergy + multiplayer_synergy + balance_synergy,
        0.40
    )
    
    return total_synergy

st.title("👥 Team Builder")
st.markdown("Build a team of 1-4 heroes and analyze their combined strengths and weaknesses!")

# Hero stats editor
render_hero_stats_editor(key_prefix="team_builder")
st.markdown("---")

# Get heroes
heroes = get_heroes()
from default_heroes import default_heroes
hero_names = list(default_heroes.keys())

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
    weighting = None  # Will be set based on team size

st.markdown("---")

# Team building controls
st.subheader("🛠️ Build Your Team")
st.markdown(f"Current team size: {len(st.session_state.team)}/4")

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

st.markdown("---")

if len(st.session_state.team) == 0:
    st.info("Add heroes to your team to get started!")
    st.stop()

# Display team
st.subheader("📋 Your Team")

# Dynamic columns - always use 4 columns for consistent width across different team sizes
cols = st.columns(4)

for idx, hero in enumerate(st.session_state.team):
    with cols[idx % 4]:
        if hero in hero_image_urls:
            st.image(hero_image_urls[hero], use_container_width=True)
        st.markdown(f"**{hero}**")
        
        if st.button("❌ Remove", key=f"remove_{hero}_{idx}"):
            st.session_state.team.remove(hero)
            st.rerun()

# Clear team button in its own row
if st.session_state.team and st.button("🗑️ Clear Team", key="clear_team_button", use_container_width=True):
    st.session_state.team = []
    st.rerun()

st.markdown("---")

# Tier ranking button
if "show_tier" not in st.session_state:
    st.session_state.show_tier = False

if st.button("🏆 What tier is my team?", use_container_width=True, key="tier_button"):
    st.session_state.show_tier = True

if st.session_state.show_tier:
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

    # Apply appropriate preset based on team size if no villain selected
    if weighting is None:
        weighting = get_preset_for_team_size(len(st.session_state.team))
        st.info(f"📊 Using **{len(st.session_state.team)}-player** weighting preset")

    # Calculate team stats for scoring
    team_stats = []
    for hero in st.session_state.team:
        team_stats.append(heroes[hero])

    combined_stats = np.mean(team_stats, axis=0)
    base_team_score = float(np.dot(combined_stats, weighting))

    # Calculate synergy bonus
    synergy_multiplier = calculate_team_synergy(st.session_state.team, heroes, len(st.session_state.team))
    team_score = base_team_score * (1.0 + synergy_multiplier)

    # Calculate all possible team combinations and their scores
    all_combinations = []
    same_size_combinations = []

    for team_size in range(1, 5):
        for combo in combinations(hero_names, team_size):
            combo_stats = np.mean([heroes[hero] for hero in combo], axis=0)
            # Use preset weighting for this team size
            combo_weighting = get_preset_for_team_size(team_size)
            combo_base_score = float(np.dot(combo_stats, combo_weighting))
            combo_synergy = calculate_team_synergy(list(combo), heroes, team_size)
            combo_score = combo_base_score * (1.0 + combo_synergy)
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
        st.write(f"Base Score: {base_team_score:.1f}")
        st.write(f"Synergy Bonus: +{synergy_multiplier*100:.1f}%")
        st.write(f"**Final Score: {team_score:.1f}**")
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

    # Create radar chart for team stats
    st.markdown("---")
    st.subheader("🎯 Team Stat Profile")

    factor_names = [
        "Economy", "Tempo", "Survivability", "Villain Damage",
        "Threat Removal", "Reliability", "Minion Control"
    ]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'), facecolor='none')

    angles = np.linspace(0, 2 * np.pi, len(factor_names), endpoint=False).tolist()
    combined_stats_list = combined_stats[:len(factor_names)].tolist()

    angles += angles[:1]
    combined_stats_list += combined_stats_list[:1]

    # Add colored background regions for strength levels
    angles_fill = np.linspace(0, 2 * np.pi, 100)
    ax.fill_between(angles_fill, -10, 0, alpha=0.12, color='#FF1744')
    ax.fill_between(angles_fill, 0, 1, alpha=0.12, color='#FFB300')
    ax.fill_between(angles_fill, 1, 3, alpha=0.12, color='#00D4FF')
    ax.fill_between(angles_fill, 3, 6, alpha=0.12, color='#39FF14')

    ax.plot(angles, combined_stats_list, 'o-', linewidth=2.5, color=tier_color)
    ax.fill(angles, combined_stats_list, alpha=0.2, color=tier_color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(factor_names, size=9, color='white')
    ax.set_ylim(-6, 6)
    ax.set_yticks([-5, 0, 5])
    ax.tick_params(colors='white')
    ax.grid(True, alpha=0.3, color='white')
    ax.set_title("Team Stat Profile", size=14, weight='bold', pad=20, color='white')
    ax.patch.set_alpha(0)

    st.pyplot(fig, transparent=True)

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
