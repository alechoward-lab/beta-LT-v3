"""
Hero Comparison Tool - Compare two heroes side-by-side
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from data.hero_image_urls import hero_image_urls
from components.hero_stats_manager import initialize_hero_stats, get_heroes, render_hero_stats_editor
from data.preset_options import preset_options
from data.hero_decks import hero_decks
from data.constants import STAT_NAMES
from components.nav_banner import render_nav_banner, render_page_header, render_footer
from data.hero_release_order import HERO_WAVE, WAVE_ORDER, HERO_LEGACY, LEGACY_WAVE_ORDER

render_nav_banner("hero-comparison")

# Initialize hero stats in session state
initialize_hero_stats()

render_page_header("Hero Comparison Tool", "Compare two heroes side-by-side to see their stat differences and synergy")

# Get heroes first
heroes = get_heroes()
hero_names = list(heroes.keys())

# Weighting selection at the top
st.markdown("### 👆 Click here to choose what you value")
st.markdown("Select a preset weighting or customize your own to see how heroes compare:")

col1, col2 = st.columns(2)

with col1:
    # Build preset options list including custom presets
    preset_options_list = list(preset_options.keys()) + ["Custom"]
    if "custom_presets" in st.session_state:
        preset_options_list.extend(list(st.session_state.custom_presets.keys()))
    
    preset_choice = st.selectbox(
        "Weighting Preset",
        preset_options_list,
        key="comparison_weighting_preset"
    )

# Get weighting based on preset choice
from data.help_tips import help_tips

if "custom_presets" in st.session_state and preset_choice in st.session_state.custom_presets:
    weighting = np.array(st.session_state.custom_presets[preset_choice])
elif preset_choice != "Custom" and preset_choice in preset_options:
    weighting = np.array(preset_options[preset_choice])
else:
    # Custom weighting - show sliders
    factor_names = STAT_NAMES
    
    weights = []
    col_a, col_b = st.columns(2)
    
    for i, factor in enumerate(factor_names):
        col = col_a if i % 2 == 0 else col_b
        with col:
            weight = st.slider(
                factor,
                min_value=-10,
                max_value=10,
                value=st.session_state.get(f"comparison_weight_{factor}", 0),
                key=f"comparison_weight_{factor}",
                help=help_tips.get(factor, "")
            )
            weights.append(weight)
    
    weighting = np.array(weights)

st.markdown("---")

# Hero stats editor
render_hero_stats_editor(key_prefix="hero_comparison")
st.markdown("---")

# Select two heroes
st.subheader("Select Heroes to Compare")

# Format filter (primary) + Wave filter (secondary — Legacy-aware)
fmt_col, wave_col, _ = st.columns([1, 1, 1])
with fmt_col:
    cmp_fmt_filter = st.selectbox(
        "Format",
        ["Current", "Legacy"],
        index=1,
        key="comparison_fmt_filter",
        label_visibility="collapsed",
    )
if cmp_fmt_filter == "Current":
    cmp_hero_names = [h for h in hero_names if not HERO_LEGACY.get(h, False)]
else:
    # Legacy includes ALL heroes (current + legacy)
    cmp_hero_names = hero_names[:]
    with wave_col:
        cmp_wave_filter = st.multiselect(
            "Filter by waves",
            WAVE_ORDER,
            key="comparison_wave_filter",
            placeholder="All Waves",
        )
    if cmp_wave_filter:
        cmp_hero_names = [h for h in cmp_hero_names if HERO_WAVE.get(h) in cmp_wave_filter]

# ── Hero 1 grid selector ──
if "comparison_hero_1" not in st.session_state:
    st.session_state.comparison_hero_1 = hero_names[0]

hero_1 = st.session_state.comparison_hero_1

with st.expander(f"Hero 1: {hero_1} — tap to change", expanded=False):
    cols_per_row = 6
    for i in range(0, len(cmp_hero_names), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(cmp_hero_names):
                break
            hero = cmp_hero_names[idx]
            with col:
                img_path = hero_image_urls.get(hero, "")
                if img_path:
                    st.image(img_path, width="stretch")
                if st.button(hero, key=f"cmp1_btn_{hero}", width="stretch"):
                    st.session_state.comparison_hero_1 = hero
                    st.rerun()

# ── Hero 2 grid selector ──
if "comparison_hero_2" not in st.session_state:
    st.session_state.comparison_hero_2 = hero_names[1] if len(hero_names) > 1 else hero_names[0]

hero_2 = st.session_state.comparison_hero_2

with st.expander(f"Hero 2: {hero_2} — tap to change", expanded=False):
    cols_per_row = 6
    for i in range(0, len(cmp_hero_names), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(cmp_hero_names):
                break
            hero = cmp_hero_names[idx]
            with col:
                img_path = hero_image_urls.get(hero, "")
                if img_path:
                    st.image(img_path, width="stretch")
                if st.button(hero, key=f"cmp2_btn_{hero}", width="stretch"):
                    st.session_state.comparison_hero_2 = hero
                    st.rerun()

if hero_1 == hero_2:
    st.warning("Please select two different heroes")
    st.stop()

# Factor names
factor_names = STAT_NAMES

# Get stats
stats_1 = heroes[hero_1]
stats_2 = heroes[hero_2]

st.markdown("---")

# Display hero images and basic info
col1, col2 = st.columns(2)

with col1:
    if hero_1 in hero_image_urls:
        st.image(hero_image_urls[hero_1], width="stretch")
    st.markdown(f"### {hero_1}")
    for entry in hero_decks.get(hero_1, []):
        st.markdown(f"📋 [{entry['name']}]({entry['url']})")

with col2:
    if hero_2 in hero_image_urls:
        st.image(hero_image_urls[hero_2], width="stretch")
    st.markdown(f"### {hero_2}")
    for entry in hero_decks.get(hero_2, []):
        st.markdown(f"📋 [{entry['name']}]({entry['url']})")

st.markdown("---")

# Stat comparison table
st.subheader("📊 Stat Comparison")

comparison_data = []
for i, factor in enumerate(factor_names):
    val1 = int(stats_1[i])
    val2 = int(stats_2[i])
    diff = val2 - val1
    comparison_data.append({
        "Stat": factor,
        f"{hero_1}": val1,
        f"{hero_2}": val2,
        "Difference": diff
    })

import pandas as pd
df = pd.DataFrame(comparison_data)

# Color code the difference column
def color_diff(val):
    if val > 0:
        return f"🟢 +{val}"
    elif val < 0:
        return f"🔴 {val}"
    else:
        return "⚪ 0"

st.dataframe(
    df.style.format({
        "Difference": color_diff
    }),
    width="stretch"
)

st.markdown("---")

# Radar chart comparison
st.subheader("🎯 Stat Profile Comparison")

_bg_color = "#0e1117"
_text_color = "#c8cdd5"

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'),
                       facecolor=_bg_color)
ax.set_facecolor(_bg_color)

angles = np.linspace(0, 2 * np.pi, len(factor_names), endpoint=False).tolist()
stats_1_list = stats_1[:len(factor_names)].tolist()
stats_2_list = stats_2[:len(factor_names)].tolist()

angles += angles[:1]
stats_1_list += stats_1_list[:1]
stats_2_list += stats_2_list[:1]

ax.plot(angles, stats_1_list, 'o-', linewidth=2, label=hero_1, color='#FF6B9D', markersize=5)
ax.fill(angles, stats_1_list, alpha=0.20, color='#FF6B9D')

ax.plot(angles, stats_2_list, 'o-', linewidth=2, label=hero_2, color='#4ECDC4', markersize=5)
ax.fill(angles, stats_2_list, alpha=0.20, color='#4ECDC4')

ax.set_xticks(angles[:-1])
ax.set_xticklabels(factor_names, size=8, color=_text_color)
ax.set_ylim(-6, 6)
ax.set_yticks([-5, 0, 5])
ax.set_yticklabels(["-5", "0", "5"], size=8, color=_text_color)
ax.tick_params(colors=_text_color)
ax.spines['polar'].set_color((1, 1, 1, 0.2))
for gl in ax.yaxis.get_gridlines():
    gl.set_color((1, 1, 1, 0.12))
    gl.set_linestyle('--')
for gl in ax.xaxis.get_gridlines():
    gl.set_color((1, 1, 1, 0.12))
    gl.set_linestyle('--')
ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1.1),
          facecolor='#1a1a2e', edgecolor=(1, 1, 1, 0.2),
          labelcolor=_text_color, fontsize=10)
ax.set_title("Hero Stat Profiles", size=14, weight='bold', pad=20, color='white')

st.pyplot(fig)
plt.close(fig)

st.markdown("---")

# Overall power comparison
st.subheader("⚡ Overall Power Analysis")

# Calculate scores with selected weighting
power_1 = float(np.dot(stats_1, weighting))
power_2 = float(np.dot(stats_2, weighting))

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(hero_1, f"{power_1:.1f}")

with col2:
    st.write("")
    st.write("")
    if power_1 > power_2:
        st.success(f"✅ {hero_1} Wins\n(+{power_1 - power_2:.1f})")
    elif power_2 > power_1:
        st.error(f"❌ {hero_2} Wins\n(+{power_2 - power_1:.1f})")
    else:
        st.info(f"🟰 Tied")

with col3:
    st.metric(hero_2, f"{power_2:.1f}")

st.markdown("---")
st.subheader("💪 Strengths & Weaknesses")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**{hero_1}**")
    strengths_1 = [(factor_names[i], int(stats_1[i])) for i in range(len(factor_names)) if stats_1[i] >= 3]
    weaknesses_1 = [(factor_names[i], int(stats_1[i])) for i in range(len(factor_names)) if stats_1[i] <= -3]
    
    if strengths_1:
        st.markdown("**Top Strengths:**")
        for stat, val in sorted(strengths_1, key=lambda x: x[1], reverse=True)[:3]:
            st.write(f"- {stat}: {val:+d}")
    
    if weaknesses_1:
        st.markdown("**Main Weaknesses:**")
        for stat, val in sorted(weaknesses_1, key=lambda x: x[1])[:3]:
            st.write(f"- {stat}: {val:+d}")

with col2:
    st.markdown(f"**{hero_2}**")
    strengths_2 = [(factor_names[i], int(stats_2[i])) for i in range(len(factor_names)) if stats_2[i] >= 3]
    weaknesses_2 = [(factor_names[i], int(stats_2[i])) for i in range(len(factor_names)) if stats_2[i] <= -3]
    
    if strengths_2:
        st.markdown("**Top Strengths:**")
        for stat, val in sorted(strengths_2, key=lambda x: x[1], reverse=True)[:3]:
            st.write(f"- {stat}: {val:+d}")
    
    if weaknesses_2:
        st.markdown("**Main Weaknesses:**")
        for stat, val in sorted(weaknesses_2, key=lambda x: x[1])[:3]:
            st.write(f"- {stat}: {val:+d}")

st.markdown("---")

# Synergy check
st.subheader("🤝 Pairing Analysis")

# Base stats comparison
base_stats_1 = stats_1[:8]
base_stats_2 = stats_2[:8]

# Coverage analysis
needs_1 = np.maximum(0, 2 - base_stats_1)
coverage_1 = np.minimum(np.maximum(0, base_stats_2), needs_1).sum()
total_needs_1 = needs_1.sum()

needs_2 = np.maximum(0, 2 - base_stats_2)
coverage_2 = np.minimum(np.maximum(0, base_stats_1), needs_2).sum()
total_needs_2 = needs_2.sum()

if total_needs_1 > 0:
    coverage_pct_1 = (coverage_1 / total_needs_1) * 100
else:
    coverage_pct_1 = 100

if total_needs_2 > 0:
    coverage_pct_2 = (coverage_2 / total_needs_2) * 100
else:
    coverage_pct_2 = 100

col1, col2 = st.columns(2)

with col1:
    st.metric(f"{hero_2} covers {hero_1}'s needs", f"{coverage_pct_1:.0f}%")

with col2:
    st.metric(f"{hero_1} covers {hero_2}'s needs", f"{coverage_pct_2:.0f}%")

avg_coverage = (coverage_pct_1 + coverage_pct_2) / 2
if avg_coverage > 75:
    st.success("✅ Excellent pairing! They complement each other very well.")
elif avg_coverage > 50:
    st.info("ℹ️ Good pairing! They cover some of each other's weaknesses.")
else:
    st.warning("⚠️ Mediocre pairing. They don't cover each other's weaknesses well.")

render_footer()
