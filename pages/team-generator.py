"""
Team Generator - Generate random teams from specific tiers with optional hero locks
"""

import streamlit as st
import numpy as np
from itertools import combinations
import random
import matplotlib.pyplot as plt

from hero_image_urls import hero_image_urls
from villain_image_urls import villain_image_urls
from hero_stats_manager import initialize_hero_stats, get_heroes, render_hero_stats_editor
from villain_weights import villain_weights
from villain_strategies import villain_strategies

# Initialize hero stats in session state
initialize_hero_stats()

st.title("🎲 Team Generator")
st.markdown("Generate random teams from specific tiers! Optionally lock heroes and choose villain difficulty.")

# Hero stats editor
render_hero_stats_editor(key_prefix="team_generator")
st.markdown("---")

# Get heroes
heroes = get_heroes()
hero_names = sorted(list(heroes.keys()))

# Settings section
st.subheader("⚙️ Settings")

col1, col2 = st.columns(2)

with col1:
    # Villain selection
    st.markdown("**Step 1: Choose Villain (Optional)**")
    villain_names = sorted(list(villain_weights.keys()))
    villain_choice = st.selectbox(
        "Select a villain",
        ["No villain selected"] + villain_names,
        key="generator_villain_choice"
    )
    
    if villain_choice != "No villain selected":
        weighting = np.array(villain_weights[villain_choice])
        if villain_choice in villain_image_urls:
            st.image(villain_image_urls[villain_choice], use_container_width=True)
    else:
        weighting = np.ones(15)

with col2:
    # Player count
    st.markdown("**Step 2: Choose Team Size**")
    team_size = st.selectbox(
        "Team size",
        [1, 2, 3, 4],
        key="generator_team_size"
    )

st.markdown("---")

# Hero locks section
st.subheader("🔒 Hero Locks (Optional)")
st.markdown("Lock in heroes that MUST be on the generated team (0-3 heroes):")

locked_heroes = []
col1, col2, col3 = st.columns(3)

with col1:
    hero1 = st.selectbox(
        "Lock hero 1 (optional)",
        ["None"] + hero_names,
        key="lock_hero_1"
    )
    if hero1 != "None":
        locked_heroes.append(hero1)

with col2:
    available_for_2 = [h for h in hero_names if h not in locked_heroes]
    hero2 = st.selectbox(
        "Lock hero 2 (optional)",
        ["None"] + available_for_2,
        key="lock_hero_2"
    )
    if hero2 != "None":
        locked_heroes.append(hero2)

with col3:
    available_for_3 = [h for h in hero_names if h not in locked_heroes]
    hero3 = st.selectbox(
        "Lock hero 3 (optional)",
        ["None"] + available_for_3,
        key="lock_hero_3"
    )
    if hero3 != "None":
        locked_heroes.append(hero3)

if len(locked_heroes) > team_size - 1:
    st.error(f"❌ Too many locked heroes! You can lock max {team_size - 1} for a {team_size}-player team.")
    st.stop()

st.markdown("---")

# Tier selection
st.subheader("🏆 Choose Tier")
tier_choice = st.selectbox(
    "Select tier",
    ["S", "A", "B", "C", "D"],
    key="generator_tier_choice"
)

st.markdown("---")

# Generate button
if st.button("🎲 Generate Random Team", use_container_width=True, key="generate_button"):
    # Calculate all possible team combinations
    available_heroes = [h for h in hero_names if h not in locked_heroes]
    
    # Determine how many more heroes we need
    remaining_slots = team_size - len(locked_heroes)
    
    # Generate all combinations of remaining slots
    valid_teams = []
    
    for combo in combinations(available_heroes, remaining_slots):
        team = list(locked_heroes) + list(combo)
        
        # Calculate team score
        team_stats = [heroes[hero] for hero in team]
        combined_stats = np.mean(team_stats, axis=0)
        team_score = float(np.dot(combined_stats, weighting))
        
        valid_teams.append((team, team_score))
    
    # Calculate mean and std for tier determination
    all_scores = [score for _, score in valid_teams]
    mean_score = np.mean(all_scores)
    std_score = np.std(all_scores)
    
    # Filter teams by tier
    tier_teams = []
    for team, score in valid_teams:
        if tier_choice == "S":
            if score >= mean_score + 1.5 * std_score:
                tier_teams.append(team)
        elif tier_choice == "A":
            if mean_score + 0.5 * std_score <= score < mean_score + 1.5 * std_score:
                tier_teams.append(team)
        elif tier_choice == "B":
            if mean_score - 0.5 * std_score <= score < mean_score + 0.5 * std_score:
                tier_teams.append(team)
        elif tier_choice == "C":
            if mean_score - 1.5 * std_score <= score < mean_score - 0.5 * std_score:
                tier_teams.append(team)
        elif tier_choice == "D":
            if score < mean_score - 1.5 * std_score:
                tier_teams.append(team)
    
    if not tier_teams:
        st.error(f"❌ No {tier_choice} tier teams found with those constraints! Try a different tier or fewer locked heroes.")
        st.stop()
    
    # Pick random team from tier
    random_team = random.choice(tier_teams)
    
    st.session_state.generated_team = list(random_team)
    st.success(f"✅ Generated {tier_choice} tier team! ({len(tier_teams)} total teams in this tier)")

# Display generated team if one exists
if "generated_team" in st.session_state:
    st.markdown("---")
    st.subheader("🎉 Your Generated Team")
    
    team = st.session_state.generated_team
    
    # Calculate stats for display
    team_stats = [heroes[hero] for hero in team]
    combined_stats = np.mean(team_stats, axis=0)
    team_score = float(np.dot(combined_stats, weighting))
    
    # Display team
    cols_per_row = 5
    for row_start in range(0, len(team), cols_per_row):
        row_end = min(row_start + cols_per_row, len(team))
        team_row = team[row_start:row_end]
        cols = st.columns(len(team_row))
        
        for col, hero in zip(cols, team_row):
            with col:
                if hero in hero_image_urls:
                    st.image(hero_image_urls[hero], use_container_width=True)
                st.markdown(f"**{hero}**")
    
    # Display score
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Team Size", len(team))
    with col2:
        st.metric("Team Score", f"{team_score:.1f}")
    with col3:
        st.metric("Tier", tier_choice)
    
    st.markdown("---")
    
    # Create radar chart for team stats
    st.subheader("🎯 Team Stat Profile")
    
    # Map tier to color
    tier_colors = {"S": "red", "A": "orange", "B": "green", "C": "blue", "D": "purple"}
    tier_color = tier_colors[tier_choice]
    
    factor_names = [
        "Economy", "Tempo", "Card Value", "Survivability", "Villain Damage",
        "Threat Removal", "Reliability", "Minion Control", "Control Boon", "Support Boon",
        "Unique Broken Builds Boon", "Late Game Power Boon", "Simplicity", "Stun/Confuse Boon",
        "Multiplayer Consistency Boon"
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
