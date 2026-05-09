"""
Shared weighting utilities for consistent stat management across all pages.
This module provides functions to initialize and manage hero stat weighting factors
in st.session_state so they are shared across all pages in a Streamlit session.
"""

import streamlit as st
import numpy as np
from data.constants import STAT_NAMES, DEFAULT_WEIGHTS
from data.help_tips import help_tips
from data.preset_options import preset_options


def initialize_weighting_stats():
    """Initialize all weighting stat keys in session_state if they don't exist."""
    for key, default_value in DEFAULT_WEIGHTS.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    if "preset_choice" not in st.session_state:
        st.session_state["preset_choice"] = "General Power: 2 Player"


def get_weighting_array():
    """
    Get the current weighting array from session_state.
    Returns a numpy array of all 15 weighting factors.
    """
    return np.array([st.session_state.get(key, 0) for key in STAT_NAMES])


def update_preset():
    """Callback function to update slider values when a weighting preset is selected."""
    preset = st.session_state.preset_choice
    if preset != "Custom":
        preset_vals = preset_options[preset]
        for i, key in enumerate(STAT_NAMES):
            st.session_state[key] = int(preset_vals[i])


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
    
    for stat_name in STAT_NAMES:
        st.slider(
            stat_name,
            min_value=-10,
            max_value=10,
            value=st.session_state.get(stat_name, DEFAULT_WEIGHTS.get(stat_name, 0)),
            key=stat_name,
            help=help_tips.get(stat_name) if show_help else None,
        )
