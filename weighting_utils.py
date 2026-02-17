"""
Shared weighting utilities for consistent stat management across all pages.
This module provides functions to initialize and manage hero stat weighting factors
in st.session_state so they are shared across all pages in a Streamlit session.
"""

import streamlit as st
import numpy as np
from help_tips import help_tips
from preset_options import preset_options


def initialize_weighting_stats():
    """Initialize all weighting stat keys in session_state if they don't exist."""
    stat_keys = [
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
    
    defaults = {
        "Economy": 4,
        "Tempo": 2,
        "Card Value": 2,
        "Survivability": 2,
        "Villain Damage": 1,
        "Threat Removal": 2,
        "Reliability": 3,
        "Minion Control": 1,
        "Control Boon": 2,
        "Support Boon": 2,
        "Unique Broken Builds Boon": 1,
        "Late Game Power Boon": 1,
        "Simplicity": 0,
        "Stun/Confuse Boon": 0,
        "Multiplayer Consistency Boon": 0,
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    # Initialize preset choice
    if "preset_choice" not in st.session_state:
        st.session_state["preset_choice"] = "General Power: 2 Player"


def get_weighting_array():
    """
    Get the current weighting array from session_state.
    Returns a numpy array of all 15 weighting factors.
    """
    stat_keys = [
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
    
    return np.array([st.session_state.get(key, 0) for key in stat_keys])


def update_preset():
    """Callback function to update slider values when a weighting preset is selected."""
    preset = st.session_state.preset_choice
    if preset != "Custom":
        preset_vals = preset_options[preset]
        st.session_state["Economy"] = int(preset_vals[0])
        st.session_state["Tempo"] = int(preset_vals[1])
        st.session_state["Card Value"] = int(preset_vals[2])
        st.session_state["Survivability"] = int(preset_vals[3])
        st.session_state["Villain Damage"] = int(preset_vals[4])
        st.session_state["Threat Removal"] = int(preset_vals[5])
        st.session_state["Reliability"] = int(preset_vals[6])
        st.session_state["Minion Control"] = int(preset_vals[7])
        st.session_state["Control Boon"] = int(preset_vals[8])
        st.session_state["Support Boon"] = int(preset_vals[9])
        st.session_state["Unique Broken Builds Boon"] = int(preset_vals[10])
        st.session_state["Late Game Power Boon"] = int(preset_vals[11])
        st.session_state["Simplicity"] = int(preset_vals[12])
        st.session_state["Stun/Confuse Boon"] = int(preset_vals[13])
        st.session_state["Multiplayer Consistency Boon"] = int(preset_vals[14])


def render_weighting_sliders(show_help=True):
    """
    Render all weighting stat sliders in the current context.
    These sliders update st.session_state directly.
    
    Parameters:
    -----------
    show_help : bool
        Whether to display help tooltips for each slider.
    """
    st.markdown(
        "If you don't want a category to affect the list, set it to 0. "
        "If you set something negative, the heroes with negative stats will go up, "
        "and the heroes with positive stats will go down."
    )
    
    # Select weighting preset
    preset_choice = st.selectbox(
        "Select Weighting Option", 
        list(preset_options.keys()) + ["Custom"],
        key="preset_choice",
        on_change=update_preset
    )
    
    # Economy
    st.slider(
        "Economy",
        min_value=-10,
        max_value=10,
        value=st.session_state.get("Economy", 4),
        key="Economy",
        help=help_tips.get("Economy") if show_help else None
    )
    
    # Tempo
    st.slider(
        "Tempo",
        min_value=-10,
        max_value=10,
        value=st.session_state.get("Tempo", 2),
        key="Tempo",
        help=help_tips.get("Tempo") if show_help else None
    )
    
    # Card Value
    st.slider(
        "Card Value",
        min_value=-10,
        max_value=10,
        value=st.session_state.get("Card Value", 2),
        key="Card Value",
        help=help_tips.get("Card Value") if show_help else None
    )
    
    # Survivability
    st.slider(
        "Survivability",
        min_value=-10,
        max_value=10,
        value=st.session_state.get("Survivability", 2),
        key="Survivability",
        help=help_tips.get("Survivability") if show_help else None
    )
    
    # Villain Damage
    st.slider(
        "Villain Damage",
        min_value=-10,
        max_value=10,
        value=st.session_state.get("Villain Damage", 1),
        key="Villain Damage",
        help=help_tips.get("Villain Damage") if show_help else None
    )
    
    # Threat Removal
    st.slider(
        "Threat Removal",
        min_value=-10,
        max_value=10,
        value=st.session_state.get("Threat Removal", 2),
        key="Threat Removal",
        help=help_tips.get("Threat Removal") if show_help else None
    )
    
    # Reliability
    st.slider(
        "Reliability",
        min_value=-10,
        max_value=10,
        value=st.session_state.get("Reliability", 3),
        key="Reliability",
        help=help_tips.get("Reliability") if show_help else None
    )
    
    # Minion Control
    st.slider(
        "Minion Control",
        min_value=-10,
        max_value=10,
        value=st.session_state.get("Minion Control", 1),
        key="Minion Control",
        help=help_tips.get("Minion Control") if show_help else None
    )
    
    # Control Boon
    st.slider(
        "Control Boon",
        min_value=-10,
        max_value=10,
        value=st.session_state.get("Control Boon", 2),
        key="Control Boon",
        help=help_tips.get("Control Boon") if show_help else None
    )
    
    # Support Boon
    st.slider(
        "Support Boon",
        min_value=-10,
        max_value=10,
        value=st.session_state.get("Support Boon", 2),
        key="Support Boon",
        help=help_tips.get("Support Boon") if show_help else None
    )
    
    # Unique Broken Builds Boon
    st.slider(
        "Unique Broken Builds Boon",
        min_value=-10,
        max_value=10,
        value=st.session_state.get("Unique Broken Builds Boon", 1),
        key="Unique Broken Builds Boon",
        help=help_tips.get("Unique Broken Builds Boon") if show_help else None
    )
    
    # Late Game Power Boon
    st.slider(
        "Late Game Power Boon",
        min_value=-10,
        max_value=10,
        value=st.session_state.get("Late Game Power Boon", 1),
        key="Late Game Power Boon",
        help=help_tips.get("Late Game Power Boon") if show_help else None
    )
    
    # Simplicity
    st.slider(
        "Simplicity",
        min_value=-10,
        max_value=10,
        value=st.session_state.get("Simplicity", 0),
        key="Simplicity",
        help=help_tips.get("Simplicity") if show_help else None
    )
    
    # Stun/Confuse Boon
    st.slider(
        "Stun/Confuse Boon",
        min_value=-10,
        max_value=10,
        value=st.session_state.get("Stun/Confuse Boon", 0),
        key="Stun/Confuse Boon",
        help=help_tips.get("Stun/Confuse Boon") if show_help else None
    )
    
    # Multiplayer Consistency Boon
    st.slider(
        "Multiplayer Consistency Boon",
        min_value=-10,
        max_value=10,
        value=st.session_state.get("Multiplayer Consistency Boon", 0),
        key="Multiplayer Consistency Boon",
        help=help_tips.get("Multiplayer Consistency Boon") if show_help else None
    )
