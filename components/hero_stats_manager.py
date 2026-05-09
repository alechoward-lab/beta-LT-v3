"""
Hero Stats Manager - Handles shared hero stats across pages using Streamlit session state.
This module provides functions to initialize, access, and modify hero stats that persist
across all pages in the Streamlit app.
"""

import streamlit as st
import numpy as np
import copy
from data.default_heroes import default_heroes
from data.help_tips import help_tips
from data.constants import STAT_NAMES


# Stat names in order (must match the stats arrays)
# (imported from data.constants)


def initialize_hero_stats():
    """
    Initialize hero stats in session state if not already present.
    This should be called once at the start of the app.
    """
    if "heroes" not in st.session_state:
        st.session_state.heroes = copy.deepcopy(default_heroes)
        st.session_state.default_heroes = copy.deepcopy(default_heroes)


def get_heroes():
    """
    Get the current hero stats from session state.
    Returns a dictionary of hero names to numpy arrays of stats.
    """
    initialize_hero_stats()
    return st.session_state.heroes


def get_hero_stats(hero_name):
    """
    Get stats for a specific hero.
    Returns a numpy array of stats.
    """
    heroes = get_heroes()
    return heroes.get(hero_name)


def update_hero_stats(hero_name, stats_array):
    """
    Update stats for a specific hero.
    stats_array should be a list or numpy array of 15 values.
    """
    initialize_hero_stats()
    st.session_state.heroes[hero_name] = np.array(stats_array)


def reset_hero_stats():
    """
    Reset all hero stats to defaults.
    """
    st.session_state.heroes = copy.deepcopy(st.session_state.default_heroes)


def render_hero_stats_editor(key_prefix=""):
    """
    Render the hero stats editor UI as an expander.
    This can be called from any page to allow editing hero stats.
    
    Args:
        key_prefix: A prefix to add to widget keys to avoid conflicts
                   when used on multiple pages
    """
    initialize_hero_stats()
    
    with st.expander("📊 Edit Hero Stats (click to expand)"):
        st.markdown("""
**How stats work:** Every hero has been rated on a scale of **−5 to 5** in each category. 
**6 is reserved for best-in-class** — only used when a hero is clearly the standout in that category. 
0 means average or neutral.

The inputs here go from **−10 to 10** so you can exaggerate the gaps between heroes if you want more separation in the tier list. 
For example, if you think two heroes are both "good" at Economy but one is clearly better, you could push one to 7 and the other to 3 rather than 4 and 3.

⚠️ **Changes here carry over to all pages in your session** (Hero Comparison, Pairings, etc.).
        """)
        
        # Select a hero to modify (searchable dropdown)
        hero_to_modify = st.selectbox(
            "Select a Hero to Modify",
            list(st.session_state.heroes.keys()),
            key=f"{key_prefix}_hero_choice"
        )
        
        # Display number inputs with help tips for each stat
        current_stats = st.session_state.heroes[hero_to_modify]
        
        # Create columns for better layout
        col1, col2 = st.columns(2)
        
        new_stats = []
        for i, stat in enumerate(STAT_NAMES):
            # Alternate between columns
            col = col1 if i % 2 == 0 else col2
            
            with col:
                value = st.number_input(
                    f"{stat}",
                    value=int(current_stats[i]),
                    min_value=-10,
                    max_value=10,
                    key=f"{key_prefix}_{hero_to_modify}_{stat}",
                    help=help_tips.get(stat, "")
                )
                new_stats.append(value)
        
        # Update hero stats if any changed
        if any(new_stats[i] != int(current_stats[i]) for i in range(len(STAT_NAMES))):
            st.session_state.heroes[hero_to_modify] = np.array(new_stats)
        
        # Button to reset this hero to default
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Reset This Hero to Default", key=f"{key_prefix}_reset_hero"):
                st.session_state.heroes[hero_to_modify] = copy.deepcopy(
                    st.session_state.default_heroes[hero_to_modify]
                )
                st.rerun()
        
        with col2:
            if st.button("Reset All Heroes to Default", key=f"{key_prefix}_reset_all"):
                st.session_state.heroes = copy.deepcopy(st.session_state.default_heroes)
                st.rerun()
