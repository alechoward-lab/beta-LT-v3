"""
The Limited Card Pool Marvel Champions Tier List

"""
#%%
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import copy
import io
import json
from html import escape as html_escape
from data.hero_image_urls import hero_image_urls
from data.default_heroes import default_heroes
from data.preset_options import preset_options
from data.help_tips import help_tips
from data.constants import STAT_NAMES, TIER_COLORS, DEFAULT_WEIGHTS, HERO_ALTER_EGOS
from components.github_storage import load_json
from components.weighting_utils import update_preset
from data.hero_release_order import HERO_WAVE, WAVE_ORDER, HERO_LEGACY, LEGACY_WAVE_ORDER
from components.nav_banner import render_nav_banner, render_page_header, render_footer
from components.hero_card_viewer import render_hero_card_viewer

# Use shared hero_alter_egos from constants
hero_alter_egos = HERO_ALTER_EGOS

render_nav_banner("hero-tier-list")

# ----------------------------------------
# Load weighting from shared URL query params (if present)
# ----------------------------------------
_WEIGHT_KEYS = STAT_NAMES

query_params = st.query_params
if "w" in query_params and not st.session_state.get("_shared_loaded"):
    try:
        shared_weights = [int(x) for x in query_params["w"].split(",")]
        if len(shared_weights) == len(_WEIGHT_KEYS):
            for key, val in zip(_WEIGHT_KEYS, shared_weights):
                st.session_state[key] = val
            st.session_state["preset_choice"] = "Custom"
            st.session_state["_shared_loaded"] = True
            st.toast("🔗 Loaded tier list from shared link!")
    except (ValueError, AttributeError):
        pass

# ----------------------------------------
# Main App Content Header
# ----------------------------------------
render_page_header("Out of the Box Tier List", "Card-pool and deck agnostic hero rankings for Marvel Champions")

# ----------------------------------------
# Initialize hero stats if not set
# ----------------------------------------
if "heroes" not in st.session_state:
    st.session_state.heroes = copy.deepcopy(default_heroes)
    st.session_state.default_heroes = copy.deepcopy(default_heroes)

# ----------------------------------------
# Compact top bar: preset selector + customize toggle
# ----------------------------------------
_defaults = DEFAULT_WEIGHTS
# Ensure all weight keys exist in session state
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

bar_col1, bar_col2, bar_col3, bar_col4 = st.columns([3, 1.2, 1.2, 1])
with bar_col1:
    preset_choice = st.selectbox(
        "Weighting Preset",
        list(preset_options.keys()) + ["Custom"],
        key="preset_choice",
        on_change=update_preset
    )
with bar_col2:
    st.write("")  # spacing
    customize_open = st.toggle("⚙️ Customize", value=st.session_state.get("_customize_open", False), key="_customize_open")
with bar_col3:
    if "hd_view" not in st.session_state:
        st.session_state.hd_view = True
    st.markdown("<div style='font-size:12px;text-align:center;color:#888;margin-bottom:-8px;'>View Mode</div>", unsafe_allow_html=True)
    st.toggle("hd_toggle", key="hd_view", label_visibility="collapsed")
    # Icons flanking the toggle
    st.markdown(
        "<div style='display:flex;justify-content:center;align-items:center;margin-top:-42px;pointer-events:none;font-size:14px;'>"
        "<span style='margin-right:28px;' title='Dynamic'>⚡</span>"
        "<span style='margin-left:28px;' title='HD View'>🖼️</span>"
        "</div>",
        unsafe_allow_html=True,
    )
with bar_col4:
    st.write("")  # spacing
    if st.button("Tutorial"):
        st.session_state["_show_tutorial"] = not st.session_state.get("_show_tutorial", False)
        st.rerun()

# Build weighting array from session state (always available for tier list calc)
weighting = np.array([st.session_state.get(k, _defaults[k]) for k in _WEIGHT_KEYS])

if preset_choice != "Custom":
    plot_title = f"{preset_choice}"
else:
    plot_title = "Custom Weighting"

# ----------------------------------------
# Tutorial / info section (toggled)
# ----------------------------------------
if st.session_state.get("_show_tutorial", False):
    st.markdown("""
<div id="onboarding-overlay" style="background: linear-gradient(135deg, rgba(10,10,30,0.95), rgba(15,52,96,0.92)); border: 2px solid rgba(52,152,219,0.6); border-radius: 14px; padding: 24px 28px; margin-bottom: 20px; box-shadow: 0 8px 40px rgba(0,0,0,0.6);">
<div style="font-size:22px; font-weight:bold; color:#fff; margin-bottom:14px; text-align:center;">🚀 How the Out of the Box Tier List Works</div>
<div style="display:flex; gap:16px; flex-wrap:wrap; justify-content:center; margin-bottom:18px;">
  <div style="flex:1; min-width:180px; background:rgba(52,152,219,0.15); border:1px solid rgba(52,152,219,0.3); border-radius:10px; padding:14px;">
    <div style="font-size:28px; text-align:center; margin-bottom:6px;">⚖️</div>
    <div style="font-weight:bold; color:#3498db; font-size:14px; text-align:center; margin-bottom:4px;">Weighting Factors</div>
    <div style="color:#c8cdd5; font-size:13px; text-align:center;">How much you care about each category (Economy, Survivability, etc.). Higher = more important. Set to 0 to ignore.</div>
  </div>
  <div style="flex:1; min-width:180px; background:rgba(155,89,182,0.15); border:1px solid rgba(155,89,182,0.3); border-radius:10px; padding:14px;">
    <div style="font-size:28px; text-align:center; margin-bottom:6px;">📊</div>
    <div style="font-weight:bold; color:#9b59b6; font-size:14px; text-align:center; margin-bottom:4px;">Hero Stats</div>
    <div style="color:#c8cdd5; font-size:13px; text-align:center;">Each hero is pre-rated by Daring Lime on a <b style="color:#fff;">−5 to 5</b> scale (<b style="color:#fff;">6 = best-in-class</b>). Disagree? Edit them in Customize.</div>
  </div>
  <div style="flex:1; min-width:180px; background:rgba(46,204,113,0.15); border:1px solid rgba(46,204,113,0.3); border-radius:10px; padding:14px;">
    <div style="font-size:28px; text-align:center; margin-bottom:6px;">🏆</div>
    <div style="font-weight:bold; color:#2ecc71; font-size:14px; text-align:center; margin-bottom:4px;">Your Tier List</div>
    <div style="color:#c8cdd5; font-size:13px; text-align:center;">Score = hero stats × your weights. Change the preset above or hit <b style="color:#fff;">⚙️ Customize</b> to fine-tune everything.</div>
  </div>
</div>
<div style="display:flex; gap:16px; flex-wrap:wrap; justify-content:center; margin-bottom:12px;">
  <div style="flex:1; min-width:200px; background:rgba(241,196,15,0.12); border:1px solid rgba(241,196,15,0.3); border-radius:10px; padding:12px;">
    <div style="font-weight:bold; color:#f1c40f; font-size:13px; text-align:center; margin-bottom:4px;">💡 Quick Start</div>
    <div style="color:#c8cdd5; font-size:12px; text-align:center;">
      • Choose a <b style="color:#fff;">preset</b> from the dropdown (e.g., "True Solo", "Thwart-Heavy")<br>
      • The tier list updates instantly based on that playstyle<br>
      • Use <b style="color:#fff;">Format</b> filter to switch between Current/Legacy heroes<br>
      • Click <b style="color:#fff;">⚙️ Customize</b> to fine-tune weights & hero stats
    </div>
  </div>
  <div style="flex:1; min-width:200px; background:rgba(231,76,60,0.12); border:1px solid rgba(231,76,60,0.3); border-radius:10px; padding:12px;">
    <div style="font-weight:bold; color:#e74c3c; font-size:13px; text-align:center; margin-bottom:4px;">📥 Save & Share</div>
    <div style="color:#c8cdd5; font-size:12px; text-align:center;">
      • <b style="color:#fff;">Download PNG</b> — save tier list as an image<br>
      • <b style="color:#fff;">Download Settings</b> — save your custom weights<br>
      • <b style="color:#fff;">Upload Settings</b> — load saved configurations<br>
      • Hover a hero for <b style="color:#fff;">detailed stat breakdown</b>
    </div>
  </div>
</div>
<div style="text-align:center; margin-top:4px;">
<span style="color:#a0a8b8; font-size:13px;">📺 <a href="https://youtu.be/TxU1NcryRS8" target="_blank" style="color:#3498db;">Video tutorial</a> &nbsp;|&nbsp; 💬 <a href="https://discord.gg/ReF5jDSHqV" target="_blank" style="color:#3498db;">Discord</a></span>
</div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------
# Customization panel (toggled)
# ----------------------------------------
if customize_open:
    st.checkbox("Show help tooltips", value=st.session_state.get("show_help", True), key="show_help")
    col1, col2 = st.columns(2)
    # ----------------------------------------
    # Column 1: Weighting settings
    # ----------------------------------------
    with col1:
        with st.expander("Edit Weighting Factors", expanded=True):
            st.markdown(
                "If you don't want a category to affect the list, set it to 0. "
                "If you set something negative, the heroes with negative stats will go up, "
                "and the heroes with positive stats will go down."
            )

            for _wk in _WEIGHT_KEYS:
                st.slider(
                    _wk,
                    min_value=-10,
                    max_value=10,
                    value=st.session_state.get(_wk, _defaults.get(_wk, 0)),
                    key=_wk,
                    help=help_tips.get(_wk, "") if st.session_state.get("show_help", True) else None,
                )

            # Update weighting from sliders
            weighting = np.array([st.session_state.get(k, _defaults[k]) for k in _WEIGHT_KEYS])

            # Preset controls: reset and save
            col_reset, col_name = st.columns([1, 2])
            with col_reset:
                if st.button("Reset Weighting to Defaults"):
                    for k, v in _defaults.items():
                        st.session_state[k] = v
                    st.rerun()
            with col_name:
                preset_name = st.text_input("Preset Name (for save)", value="")
            # Download button to save weighting settings
            weighting_settings = {k: st.session_state.get(k, _defaults.get(k, 0)) for k in _WEIGHT_KEYS}
            weighting_settings["preset_choice"] = st.session_state.get("preset_choice", "Custom")
            weighting_settings["weighting"] = weighting.tolist()
            weighting_json = json.dumps(weighting_settings)
            st.download_button("Download Weighting Settings", weighting_json, "weighting_settings.json")
            filename = f"{preset_name or 'preset'}_weighting.json"
            st.download_button("Save Preset", weighting_json, filename)

    # ----------------------------------------
    # Column 2: Hero Stats
    # ----------------------------------------
    with col2:
        with st.expander("⚙️ Edit Hero Stats — *optional, for power users*", expanded=True):
            st.markdown("""
**Happy with the default ratings? You can skip this entirely!**

Every hero has been pre-rated by Daring Lime on a **−5 to 5** scale (with **6 = best-in-class**).
The inputs below allow **−10 to 10** so you can exaggerate differences if you want.
Changes here carry over to all pages in your session.
""")
            # List of stat names
            stat_names = STAT_NAMES

            # Select a hero to modify
            hero_to_modify = st.selectbox("Select a Hero to Modify", list(st.session_state.heroes.keys()), key="hero_choice")

            # Callback to update the current hero's stats automatically
            def update_current_hero_stats():
                new_stats = []
                for stat in stat_names:
                    new_stats.append(st.session_state.get(f"{hero_to_modify}_{stat}", 0))
                st.session_state.heroes[hero_to_modify] = np.array(new_stats)

            # Display number inputs with help tips for each stat
            current_stats = st.session_state.heroes[hero_to_modify]
            for i, stat in enumerate(stat_names):
                st.number_input(
                    f"{hero_to_modify} - {stat}",
                    value=int(current_stats[i]),
                    min_value=-10,
                    max_value=10,
                    key=f"{hero_to_modify}_{stat}",
                    on_change=update_current_hero_stats,
                    help=help_tips.get(stat, "") if st.session_state.get("show_help", True) else None,
                )

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
                "default_heroes": {hero: stats.tolist() for hero, stats in st.session_state.default_heroes.items()},
            }
            hero_stats_json = json.dumps(hero_stats_to_save)
            st.download_button("Download Hero Stats", hero_stats_json, "hero_stats.json")

# ----------------------------------------
# Continue with Tier List Calculations & Display
# ----------------------------------------
heroes = st.session_state.heroes

# Compute raw dot products once for the current weight vector.
raw_scores = {hero: float(np.dot(stats, weighting)) for hero, stats in heroes.items()}

# Format filter (primary) + Wave filter (secondary — Legacy-aware)
fmt_col, wave_col, _ = st.columns([1, 1, 1])
with fmt_col:
    home_fmt_filter = st.selectbox(
        "Format",
        ["Current", "Legacy"],
        index=1,
        key="home_fmt_filter",
        label_visibility="collapsed",
    )
if home_fmt_filter == "Current":
    heroes = {h: s for h, s in heroes.items() if not HERO_LEGACY.get(h, False)}
else:
    # Legacy includes ALL heroes (current + legacy)
    with wave_col:
        home_wave_filter = st.multiselect(
            "Filter by waves",
            WAVE_ORDER,
            key="home_wave_filter",
            placeholder="All Waves",
            label_visibility="collapsed",
        )
    if home_wave_filter:
        heroes = {h: s for h, s in heroes.items() if HERO_WAVE.get(h) in home_wave_filter}

# ----------------------------------------
# Calculate Scores and Tiers using weighting and hero stats
# ----------------------------------------
scores = {hero: raw_scores[hero] for hero in heroes}
sorted_scores = dict(sorted(scores.items(), key=lambda item: (item[1], item[0])))

hero_scores = np.array(list(scores.values()), dtype=float)
mean_score = np.mean(hero_scores)
std_score = max(np.std(hero_scores), 1e-6)
threshold_S = mean_score + 1.5 * std_score
threshold_A = mean_score + 0.5 * std_score
threshold_B_lower = mean_score - 0.5 * std_score
threshold_C = mean_score - 1.0 * std_score
threshold_D = mean_score - 1.5 * std_score

tiers = {"S": [], "A": [], "B": [], "C": [], "D": [], "F": []}
for hero, score in scores.items():
    if score >= threshold_S:
        tiers["S"].append((hero, score))
    elif score >= threshold_A:
        tiers["A"].append((hero, score))
    elif score >= threshold_B_lower:
        tiers["B"].append((hero, score))
    elif score >= threshold_C:
        tiers["C"].append((hero, score))
    elif score >= threshold_D:
        tiers["D"].append((hero, score))
    else:
        tiers["F"].append((hero, score))

for tier in tiers:
    tiers[tier] = sorted(tiers[tier], key=lambda x: (-x[1], x[0]))

hero_to_tier = {}
for tier, heroes_list in tiers.items():
    for hero, _ in heroes_list:
        hero_to_tier[hero] = tier

# ----------------------------------------
# Display Tier List with Images
# ----------------------------------------
tier_colors = TIER_COLORS

if st.session_state.hd_view:
    # ── Pure HTML view (compact, pretty) ──
    st.markdown("""
<style>
.home-tier-section {
    display: flex;
    flex-direction: column;
    gap: 0px;
    max-width: 100%;
}
.tier-row {
    display: flex;
    flex-direction: row;
    align-items: stretch;
    gap: 0px;
    min-height: 0;
}
.tier-label-block {
    background: var(--tier-color);
    color: #fff;
    font-weight: 900;
    font-size: 28px;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 52px;
    max-width: 52px;
    flex-shrink: 0;
}
.tier-heroes {
    display: flex;
    flex-wrap: wrap;
    gap: 0px;
    align-items: flex-start;
    flex: 1;
    min-height: 0;
}
.tier-heroes img {
    display: block;
    height: 120px;
    width: auto;
    object-fit: cover;
    object-position: top;
    cursor: pointer;
}
.tier-heroes .hero-card {
    position: relative;
    height: 74px;
    overflow: hidden;
    transition: transform 0.15s ease;
}
.hero-card:hover {
    transform: scale(1.08) rotate(var(--hover-rotate, -1deg));
    z-index: 10;
}
.hero-name-overlay {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    background: linear-gradient(transparent, rgba(0,0,0,0.88));
    color: #fff !important;
    text-align: center;
    padding: 18px 4px 6px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.3px;
    opacity: 0;
    transition: opacity 0.2s ease;
    pointer-events: none;
}
.hero-card:hover .hero-name-overlay {
    opacity: 1;
}
</style>
""", unsafe_allow_html=True)

    import base64, os

    @st.cache_resource(show_spinner=False)
    def _build_data_uri_map():
        result = {}
        for hero, path in hero_image_urls.items():
            if not path or not os.path.exists(path):
                continue
            ext = os.path.splitext(path)[1].lower().lstrip(".")
            mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp"}.get(ext, "jpeg")
            with open(path, "rb") as f:
                result[hero] = f"data:image/{mime};base64,{base64.b64encode(f.read()).decode()}"
        return result

    _data_uri_map = _build_data_uri_map()

    tier_html_parts = ['<div class="home-tier-section">']
    for tier in ["S", "A", "B", "C", "D", "F"]:
        members = tiers[tier]
        tier_html_parts.append('<div class="tier-row">')
        light = st.session_state.get("_light_mode", False)
        label_extra = "color:#fff !important;text-shadow:2px 2px 0 #000,-1px -1px 0 rgba(0,0,0,0.3);" if light else ""
        tier_html_parts.append(f'<div class="tier-label-block" style="--tier-color:{tier_colors[tier]};{label_extra}">{tier}</div>')
        tier_html_parts.append('<div class="tier-heroes">')
        for hero, score in members:
            alter = hero_alter_egos.get(hero, "")
            data_uri = _data_uri_map.get(hero, "")
            if data_uri:
                safe_hero = html_escape(hero, quote=True)
                safe_alter = html_escape(alter, quote=True)
                tier_html_parts.append(
                    f'<div class="hero-card" data-hero="{safe_hero}" data-alter="{safe_alter}">'
                    f'<img src="{data_uri}" alt="{safe_hero}">'
                    f'<div class="hero-name-overlay">{safe_hero}</div>'
                    f'</div>'
                )
        tier_html_parts.append('</div></div>')
    tier_html_parts.append('</div>')
    st.markdown(''.join(tier_html_parts), unsafe_allow_html=True)

else:
    # ── Streamlit native view (dynamic, reactive) ──
    num_cols = 8
    for tier in ["S", "A", "B", "C", "D", "F"]:
        members = tiers[tier]
        if not members:
            st.markdown(f"**<span style='color:{tier_colors[tier]};font-size:24px;'>{tier}</span>**", unsafe_allow_html=True)
            continue
        rows = [members[i:i + num_cols] for i in range(0, len(members), num_cols)]
        for r_idx, row in enumerate(rows):
            cols = st.columns([0.4] + [1] * num_cols)
            with cols[0]:
                if r_idx == 0:
                    st.markdown(
                        f"<div style='background:{tier_colors[tier]};color:#fff;font-weight:900;"
                        f"font-size:24px;text-align:center;border-radius:4px;padding:8px 0;"
                        f"height:100%;display:flex;align-items:center;justify-content:center;'>{tier}</div>",
                        unsafe_allow_html=True,
                    )
            for k, (hero, score) in enumerate(row):
                with cols[k + 1]:
                    if hero in hero_image_urls:
                        st.image(hero_image_urls[hero], width="stretch")

# ── Hero Card Viewer ──
all_hero_names = [hero for tier in ["S", "A", "B", "C", "D", "F"] for hero, _ in tiers[tier]]
if all_hero_names:
    render_hero_card_viewer(all_hero_names, alter_egos=hero_alter_egos, key_prefix="tier_hcv")

# ── Download tier list as PNG ──
def build_tier_list_image(tiers, tier_colors, plot_title):
    """Render the tier list as a vertical image with hero card thumbnails."""
    from PIL import Image
    import urllib.request
    import os

    tier_order = ["S", "A", "B", "C", "D", "F"]
    cards_per_row = 6
    card_w, card_h = 120, 168  # approximate card proportions
    tier_label_w = 60
    padding = 4
    row_h = card_h + padding

    # Gather rows: list of (tier_label_for_display, tier_letter, [hero_names])
    all_rows = []  # (display_label, tier_letter, [hero_name, ...])
    for t in tier_order:
        members = tiers[t]
        if not members:
            continue
        hero_names = [h for h, _ in members]
        for chunk_start in range(0, len(hero_names), cards_per_row):
            chunk = hero_names[chunk_start:chunk_start + cards_per_row]
            label = t if chunk_start == 0 else ""
            all_rows.append((label, t, chunk))

    if not all_rows:
        return None

    img_w = tier_label_w + cards_per_row * (card_w + padding) + padding
    img_h = len(all_rows) * row_h + padding

    canvas = Image.new("RGB", (img_w, img_h), color=(26, 26, 46))

    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(canvas)
    try:
        font_tier = ImageFont.truetype("arialbd.ttf", 32)
    except OSError:
        try:
            font_tier = ImageFont.truetype("arial.ttf", 32)
        except OSError:
            font_tier = ImageFont.load_default()

    # Map tier colors to RGB tuples
    _COLOR_NAME_TO_RGB = {
        "red": (255, 0, 0), "orange": (255, 165, 0), "green": (0, 128, 0),
        "blue": (0, 0, 255), "purple": (128, 0, 128), "yellow": (255, 255, 0),
        "pink": (255, 192, 203), "white": (255, 255, 255), "gray": (128, 128, 128),
    }

    def color_to_rgb(c):
        c = c.strip().lower()
        if c in _COLOR_NAME_TO_RGB:
            return _COLOR_NAME_TO_RGB[c]
        c = c.lstrip("#")
        return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))

    tier_rgb = {t: color_to_rgb(c) for t, c in tier_colors.items()}

    # Load hero card images (cached)
    card_cache = {}
    for _, _, heroes_in_row in all_rows:
        for hero in heroes_in_row:
            if hero in card_cache:
                continue
            img_path = hero_image_urls.get(hero, "")
            if img_path and os.path.exists(img_path):
                try:
                    card_img = Image.open(img_path).convert("RGB")
                    card_img = card_img.resize((card_w, card_h), Image.LANCZOS)
                    card_cache[hero] = card_img
                except Exception:
                    pass

    y = 0
    for tier_label, tier_letter, heroes_in_row in all_rows:
        color = tier_rgb.get(tier_letter, (100, 100, 100))
        draw.rectangle([0, y, tier_label_w - 1, y + row_h - 1], fill=color)
        if tier_label:
            cx, cy = tier_label_w // 2, y + row_h // 2
            # Comic-style text shadow / outline
            for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2), (-1, 0), (1, 0), (0, -1), (0, 1)]:
                draw.text((cx + dx, cy + dy), tier_label,
                           fill=(0, 0, 0), font=font_tier, anchor="mm")
            draw.text((cx, cy), tier_label,
                       fill="white", font=font_tier, anchor="mm")

        # Paste hero cards
        x = tier_label_w + padding
        for hero in heroes_in_row:
            card_img = card_cache.get(hero)
            if card_img:
                canvas.paste(card_img, (x, y + padding // 2))
            x += card_w + padding

        y += row_h

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()

png_bytes = build_tier_list_image(tiers, tier_colors, plot_title)
dl_col, share_col = st.columns([1, 1])
with dl_col:
    if png_bytes:
        st.download_button("⬇️ Download Tier List as PNG", png_bytes, file_name="tier_list.png", mime="image/png")
with share_col:
    weight_vals = ",".join(str(st.session_state.get(k, 0)) for k in _WEIGHT_KEYS)
    share_url = f"?w={weight_vals}"
    st.markdown(
        f'<a href="{share_url}" target="_blank" style="display:inline-block;padding:8px 16px;'
        f'background:#222;color:#fff !important;border:2px solid #222;border-bottom:3px solid #ed1c24;'
        f'text-decoration:none;font-weight:bold;font-size:14px;margin-top:4px;'
        f'box-shadow:2px 2px 0 rgba(0,0,0,0.3);font-family:Bangers,cursive;letter-spacing:1px;">'
        f'🔗 Share This Tier List</a>',
        unsafe_allow_html=True
    )

# ----------------------------------------
# Hot Takes — compare user tier list vs community average
# ----------------------------------------
try:
    _community_data, _ = load_json("community_tier_lists.json", default={})
    _submissions = _community_data.get("hero_power", {}).get("submissions", [])
    if len(_submissions) >= 2:
        _TIER_PTS = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1}
        _hero_scores_community = {}
        for sub in _submissions:
            for tier_name, hero_list in sub.items():
                for h in hero_list:
                    _hero_scores_community.setdefault(h, []).append(_TIER_PTS.get(tier_name, 3))
        _community_avg = {h: np.mean(scores_list) for h, scores_list in _hero_scores_community.items()}

        _hot_takes = []
        for hero, user_tier in hero_to_tier.items():
            if hero in _community_avg:
                user_pts = _TIER_PTS[user_tier]
                comm_pts = _community_avg[hero]
                diff = user_pts - comm_pts
                if abs(diff) >= 1.0:
                    comm_tier = min(_TIER_PTS.keys(), key=lambda t: abs(_TIER_PTS[t] - comm_pts))
                    _hot_takes.append((hero, user_tier, comm_tier, diff))

        if _hot_takes:
            _hot_takes.sort(key=lambda x: abs(x[3]), reverse=True)
            _top_takes = _hot_takes[:5]
            takes_html = ""
            for hero, u_tier, c_tier, diff in _top_takes:
                direction = "↑" if diff > 0 else "↓"
                takes_html += (
                    f'<span style="display:inline-block;background:rgba(255,255,255,0.08);'
                    f'padding:4px 10px;border-radius:6px;margin:3px 4px;font-size:13px;">'
                    f'<b>{hero}</b> — You: <b>{u_tier}</b> {direction} Community: <b>{c_tier}</b></span>'
                )
            st.markdown(
                f'<div style="background:linear-gradient(135deg,rgba(142,68,173,0.2),rgba(231,76,60,0.15));'
                f'border:1px solid rgba(142,68,173,0.3);border-radius:10px;padding:12px 16px;margin:12px 0;">'
                f'<span style="font-size:15px;font-weight:bold;">🔥 Your Hot Takes</span><br>'
                f'<span style="font-size:12px;color:#a0a8b8;">Heroes where your ranking differs most from the community</span><br>'
                f'<div style="margin-top:6px;">{takes_html}</div></div>',
                unsafe_allow_html=True,
            )
except Exception:
    pass  # Gracefully skip if community data is unavailable

# ----------------------------------------
# Plotting
# ----------------------------------------
st.markdown('<div class="comic-banner">Hero Scores</div>', unsafe_allow_html=True)
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

_light = st.session_state.get("_light_mode", False)
_txt = "#23272a" if _light else "white"
_bg = "#ffffff" if _light else "none"
fig.patch.set_facecolor(_bg)
ax.set_facecolor("#f8f8f8" if _light else "#0e1117")
ax.set_ylabel("Scores", fontsize="x-large", color=_txt)
ax.set_title(plot_title, fontweight='bold', fontsize=18, color=_txt)
ax.tick_params(colors=_txt)
for spine in ax.spines.values():
    spine.set_color(_txt)

legend_handles = [Patch(color=tier_colors[tier], label=f"Tier {tier}") for tier in tier_colors]
ax.legend(handles=legend_handles, title="Tier Colors", loc="upper left", fontsize='x-large',
          facecolor=_bg, edgecolor=_txt, labelcolor=_txt, title_fontproperties={'size': 'x-large', 'weight': 'bold'})
plt.tight_layout()
ax.grid(axis='y', linestyle='--', alpha=0.7)
st.pyplot(fig)
plt.close(fig)
st.markdown("<hr>", unsafe_allow_html=True)

st.markdown('<div class="comic-banner">About This Tier List</div>', unsafe_allow_html=True)
st.markdown(
    "**What is the Out of the Box tier list?** This tier list is card-pool agnostic — it ranks heroes "
    "independent of what deck you build around them or what cards you own. "
    "Heroes are rated on their inherent strengths, so the rankings apply no matter your collection."
)
st.markdown(
    "The hero stats were determined by the merits of their identity-specific cards. You can modify any hero's stats "
    "along with the weighting sliders to create your own custom tier list. Upload your saved files to restore your settings."
)
st.markdown(
    "If you want to have input on the future of this tier list, please join the [Daring Lime Discord](https://discord.gg/ReF5jDSHqV). "
    "I'll be updating the weighting factor presets and default hero stats based on community feedback."
)
st.markdown("-Stay Zesty")
st.markdown("<hr>", unsafe_allow_html=True)

# ----------------------------------------
# Upload / Restore saved settings (at bottom for power users)
# ----------------------------------------
with st.expander("📂 Upload Saved Settings"):
    st.markdown("Restore your previously saved weighting or hero stat files.")
    up_col1, up_col2 = st.columns(2)
    with up_col1:
        st.markdown("**Weighting Settings**")
        uploaded_weighting = st.file_uploader("Upload Weighting Settings", type="json", key="upload_weighting")
        if uploaded_weighting is not None:
            raw_bytes = uploaded_weighting.read()
            if raw_bytes:
                weighting_settings_file = json.loads(raw_bytes)
                for file_key, file_value in weighting_settings_file.items():
                    if file_key in ("weighting",):
                        st.session_state.weighting = np.array(file_value)
                    else:
                        st.session_state[file_key] = file_value
                st.success("Weighting settings loaded successfully!")
    with up_col2:
        st.markdown("**Hero Stats**")
        uploaded_hero_stats = st.file_uploader("Upload Hero Stats", type="json", key="upload_hero_stats")
        if uploaded_hero_stats is not None:
            raw_bytes = uploaded_hero_stats.read()
            if raw_bytes:
                hero_stats_settings = json.loads(raw_bytes)
                if "heroes" in hero_stats_settings:
                    st.session_state.heroes = {hero: np.array(stats) for hero, stats in hero_stats_settings["heroes"].items()}
                if "default_heroes" in hero_stats_settings:
                    st.session_state.default_heroes = {hero: np.array(stats) for hero, stats in hero_stats_settings["default_heroes"].items()}
                st.success("Hero stats loaded successfully!")

render_footer(show_card_credits=True)
