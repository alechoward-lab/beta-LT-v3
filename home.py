"""
Community Tier List — Build your own tier list by placing heroes into tiers,
reorder them within each tier, then submit. Scores interpolate within tiers.
"""

import streamlit as st
import numpy as np
import json
import os
from data.default_heroes import default_heroes
from data.hero_image_urls import hero_image_urls
from data.villain_image_urls import villain_image_urls
from data.constants import TIER_COLORS
from data.preset_options import preset_options
from data.hero_release_order import HERO_RELEASE_INDEX, HERO_WAVE, WAVE_ORDER, HERO_LEGACY, LEGACY_WAVE_ORDER
from data.villain_release_order import VILLAIN_RELEASE_INDEX, VILLAIN_WAVE, VILLAIN_WAVE_ORDER, VILLAIN_LEGACY
from components.github_storage import load_json, save_json
from components.nav_banner import render_nav_banner, render_page_header, render_footer

render_nav_banner("home")

TIERS = ["S", "A", "B", "C", "D"]
TIER_POINTS = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}
RATINGS_FILE = "community_tier_lists.json"

# Tier list type options
TIER_LIST_TYPES = {
    "hero_power": {"label": "🦸 Hero Power", "subject": "heroes", "metric": "power/strength"},
    "hero_fun": {"label": "🎮 Hero Fun", "subject": "heroes", "metric": "fun to play"},
    "villain_difficulty": {"label": "👿 Villain Difficulty", "subject": "villains", "metric": "difficulty"},
    "villain_fun": {"label": "🎭 Villain Fun", "subject": "villains", "metric": "fun to play against"},
}



render_page_header("Community Tier Lists", "Rate heroes and villains by power or fun — your voice shapes the rankings!")


# ─── Persistence helpers ───
def load_data():
    data, sha = load_json(RATINGS_FILE, default={})
    # Migrate old format to new format if needed
    if "submissions" in data and not any(k in data for k in TIER_LIST_TYPES.keys()):
        # Old format: {"submissions": [...]} -> move to hero_power
        old_submissions = data.get("submissions", [])
        data = {k: {"submissions": []} for k in TIER_LIST_TYPES.keys()}
        data["hero_power"]["submissions"] = old_submissions
    # Ensure all keys exist
    for k in TIER_LIST_TYPES.keys():
        if k not in data:
            data[k] = {"submissions": []}
        elif "submissions" not in data[k]:
            data[k] = {"submissions": []}
    return data


def save_data(data):
    save_json(data, RATINGS_FILE)


def interpolate_scores(submission):
    """Given a submission {tier: [ordered heroes]}, return {hero: float score}.

    Within each tier the top hero gets tier_base + 0.4 and the bottom gets
    tier_base - 0.4, linearly interpolated. A single hero in a tier gets the
    base value exactly.
    """
    hero_scores = {}
    for tier in TIERS:
        heroes = submission.get(tier, [])
        base = TIER_POINTS[tier]
        n = len(heroes)
        for i, hero in enumerate(heroes):
            if n == 1:
                hero_scores[hero] = float(base)
            else:
                # i=0 is the best in the tier, i=n-1 is the worst
                hero_scores[hero] = base + 0.4 - 0.8 * (i / (n - 1))
    return hero_scores


def build_community_tier_png(tiers, tier_colors, subject_images, title="Community Tier List"):
    """Render a tier list as a PNG image and return the bytes."""
    from PIL import Image, ImageDraw, ImageFont
    import io as _io

    tier_order = ["S", "A", "B", "C", "D"]
    cards_per_row = 8
    card_w, card_h = 120, 168
    tier_label_w = 60
    padding = 4
    row_h = card_h + padding

    all_rows = []
    for t in tier_order:
        members = tiers.get(t, [])
        if not members:
            continue
        names = [m[0] if isinstance(m, (list, tuple)) else m for m in members]
        for chunk_start in range(0, len(names), cards_per_row):
            chunk = names[chunk_start:chunk_start + cards_per_row]
            label = t if chunk_start == 0 else ""
            all_rows.append((label, t, chunk))

    if not all_rows:
        return None

    img_w = tier_label_w + cards_per_row * (card_w + padding) + padding
    title_h = 50
    img_h = title_h + len(all_rows) * row_h + padding

    canvas = Image.new("RGB", (img_w, img_h), color=(26, 26, 46))
    draw = ImageDraw.Draw(canvas)
    try:
        font_title = ImageFont.truetype("arial.ttf", 22)
        font_tier = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font_title = ImageFont.load_default()
        font_tier = font_title
    draw.text((img_w // 2, 10), title, fill="white", font=font_title, anchor="mt")

    def color_to_rgb(c):
        c = c.strip().lower()
        _map = {"red": (255, 0, 0), "orange": (255, 165, 0), "green": (0, 128, 0),
                "blue": (0, 0, 255), "purple": (128, 0, 128)}
        if c in _map:
            return _map[c]
        c = c.lstrip("#")
        return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))

    tier_rgb = {t: color_to_rgb(c) for t, c in tier_colors.items()}

    card_cache = {}
    for _, _, names_in_row in all_rows:
        for name in names_in_row:
            if name in card_cache:
                continue
            img_path = subject_images.get(name, "")
            if img_path and os.path.exists(img_path):
                try:
                    card_img = Image.open(img_path).convert("RGB")
                    card_img = card_img.resize((card_w, card_h), Image.LANCZOS)
                    card_cache[name] = card_img
                except Exception:
                    pass

    y = title_h
    for tier_label, tier_letter, names_in_row in all_rows:
        color = tier_rgb.get(tier_letter, (100, 100, 100))
        draw.rectangle([0, y, tier_label_w - 1, y + row_h - 1], fill=color)
        if tier_label:
            draw.text((tier_label_w // 2, y + row_h // 2), tier_label,
                       fill="white", font=font_tier, anchor="mm")
        x = tier_label_w + padding
        for name in names_in_row:
            card_img = card_cache.get(name)
            if card_img:
                canvas.paste(card_img, (x, y + padding // 2))
            x += card_w + padding
        y += row_h

    buf = _io.BytesIO()
    canvas.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


# ─── Session init ───
if "community_tl_data" not in st.session_state:
    st.session_state.community_tl_data = load_data()

if "tier_list_type" not in st.session_state:
    st.session_state.tier_list_type = "hero_power"

all_heroes = sorted(default_heroes.keys())
all_villains = sorted(villain_image_urls.keys())

# Placement: {tier: [ordered hero list]} - keyed by tier_list_type
if "my_tier_placement" not in st.session_state:
    st.session_state.my_tier_placement = {}
for tl_type in TIER_LIST_TYPES.keys():
    if tl_type not in st.session_state.my_tier_placement:
        st.session_state.my_tier_placement[tl_type] = {t: [] for t in TIERS}

if "assign_tier" not in st.session_state:
    st.session_state.assign_tier = "S"

# Track which tier list types the user has already submitted this session
if "submitted_types" not in st.session_state:
    st.session_state.submitted_types = set()

if "tl_undo_stack" not in st.session_state:
    st.session_state.tl_undo_stack = {}  # keyed by tier_list_type
for tl_type in TIER_LIST_TYPES.keys():
    if tl_type not in st.session_state.tl_undo_stack:
        st.session_state.tl_undo_stack[tl_type] = []

if "page_mode" not in st.session_state:
    st.session_state.page_mode = "view"  # "build" or "view"

# ─── Tier List Type Selector ───
type_options = list(TIER_LIST_TYPES.keys())
type_labels = [TIER_LIST_TYPES[k]["label"] for k in type_options]
current_type_idx = type_options.index(st.session_state.tier_list_type)

selected_label = st.selectbox(
    "Select Tier List",
    type_labels,
    index=current_type_idx,
    key="tier_list_selector",
    label_visibility="collapsed",
)
new_type = type_options[type_labels.index(selected_label)]
if new_type != st.session_state.tier_list_type:
    st.session_state.tier_list_type = new_type
    st.rerun()

# Get current tier list type info
current_tl_type = st.session_state.tier_list_type
tl_info = TIER_LIST_TYPES[current_tl_type]
is_villain_list = tl_info["subject"] == "villains"
is_fun_list = "fun" in tl_info["metric"]

# Get the right subjects (heroes or villains)
all_subjects = all_villains if is_villain_list else all_heroes
subject_images = villain_image_urls if is_villain_list else hero_image_urls
subject_name = "villain" if is_villain_list else "hero"
subject_name_plural = "villains" if is_villain_list else "heroes"

# Get data and placement for current tier list type
all_data = st.session_state.community_tl_data
data = all_data.get(current_tl_type, {"submissions": []})
placement = st.session_state.my_tier_placement[current_tl_type]
undo_stack = st.session_state.tl_undo_stack[current_tl_type]

# Flat set of placed subjects for quick lookup
placed_subjects = set()
for t in TIERS:
    placed_subjects.update(placement[t])

# ─── Top-level Build / View toggle + How it works ───
mode_col1, mode_col2, mode_col3 = st.columns([2, 2, 1])
with mode_col1:
    build_type = "primary" if st.session_state.page_mode == "build" else "secondary"
    if st.button("🛠️ Build Your Tier List", key="mode_build", width="stretch", type=build_type):
        st.session_state.page_mode = "build"
        st.rerun()
with mode_col2:
    view_type = "primary" if st.session_state.page_mode == "view" else "secondary"
    if st.button("🏆 View Community Results", key="mode_view", width="stretch", type=view_type):
        st.session_state.page_mode = "view"
        st.rerun()
with mode_col3:
    if st.button("ℹ️ How it works", key="toggle_tutorial", width="stretch", type="tertiary"):
        st.session_state.show_comm_tutorial = not st.session_state.show_comm_tutorial
        st.rerun()

st.markdown("---")

# ─── Tutorial toggle ───
if "show_comm_tutorial" not in st.session_state:
    st.session_state.show_comm_tutorial = False

if st.session_state.show_comm_tutorial:
    if st.session_state.page_mode == "view":
        # Dynamic subject name based on tier list type
        subject_display = subject_name_plural.capitalize()
        st.markdown(f"""
<div style="background: linear-gradient(135deg, rgba(10,10,30,0.95), rgba(15,52,96,0.92)); border: 2px solid rgba(52,152,219,0.6); border-radius: 14px; padding: 24px 28px; margin-bottom: 20px; box-shadow: 0 8px 40px rgba(0,0,0,0.6);">
<div style="font-size:22px; font-weight:bold; color:#fff; margin-bottom:14px; text-align:center;">🏆 Understanding the Community Rankings</div>
<div style="display:flex; gap:16px; flex-wrap:wrap; justify-content:center; margin-bottom:18px;">
  <div style="flex:1; min-width:200px; background:rgba(52,152,219,0.15); border:1px solid rgba(52,152,219,0.3); border-radius:10px; padding:14px;">
    <div style="font-size:28px; text-align:center; margin-bottom:6px;">📊</div>
    <div style="font-weight:bold; color:#3498db; font-size:14px; text-align:center; margin-bottom:4px;">Aggregated Rankings</div>
    <div style="color:#c8cdd5; font-size:13px; text-align:center;">This tier list combines <b style="color:#fff;">all community submissions</b>. Each {subject_name}'s position reflects the average rating from everyone who contributed.</div>
  </div>
  <div style="flex:1; min-width:200px; background:rgba(155,89,182,0.15); border:1px solid rgba(155,89,182,0.3); border-radius:10px; padding:14px;">
    <div style="font-size:28px; text-align:center; margin-bottom:6px;">🎯</div>
    <div style="font-weight:bold; color:#9b59b6; font-size:14px; text-align:center; margin-bottom:4px;">How Tiers Work</div>
    <div style="color:#c8cdd5; font-size:13px; text-align:center;">{subject_display} are grouped into <b style="color:#fff;">S, A, B, C, D</b> tiers based on their average score. Higher = better.</div>
  </div>
  <div style="flex:1; min-width:200px; background:rgba(46,204,113,0.15); border:1px solid rgba(46,204,113,0.3); border-radius:10px; padding:14px;">
    <div style="font-size:28px; text-align:center; margin-bottom:6px;">🗳️</div>
    <div style="font-weight:bold; color:#2ecc71; font-size:14px; text-align:center; margin-bottom:4px;">Add Your Voice</div>
    <div style="color:#c8cdd5; font-size:13px; text-align:center;">Switch to <b style="color:#fff;">Build Your Tier List</b> mode to create and submit your own rankings and influence the community results!</div>
  </div>
</div>
<div style="text-align:center; margin-top:4px;">
<span style="color:#a0a8b8; font-size:13px;">📺 <a href="https://youtu.be/TxU1NcryRS8" target="_blank" style="color:#3498db;">Video tutorial</a> &nbsp;|&nbsp; 💬 <a href="https://discord.gg/ReF5jDSHqV" target="_blank" style="color:#3498db;">Discord</a></span>
</div>
</div>
""", unsafe_allow_html=True)
    else:
        # Build mode tutorial with dynamic subject names and partial ranking note
        subject_display = subject_name_plural
        st.markdown(f"""
<div style="background: linear-gradient(135deg, rgba(10,10,30,0.95), rgba(15,52,96,0.92)); border: 2px solid rgba(52,152,219,0.6); border-radius: 14px; padding: 24px 28px; margin-bottom: 20px; box-shadow: 0 8px 40px rgba(0,0,0,0.6);">
<div style="font-size:22px; font-weight:bold; color:#fff; margin-bottom:14px; text-align:center;">🛠️ How to Build Your Tier List</div>
<div style="display:flex; gap:16px; flex-wrap:wrap; justify-content:center; margin-bottom:18px;">
  <div style="flex:1; min-width:180px; background:rgba(52,152,219,0.15); border:1px solid rgba(52,152,219,0.3); border-radius:10px; padding:14px;">
    <div style="font-size:28px; text-align:center; margin-bottom:6px;">1️⃣</div>
    <div style="font-weight:bold; color:#3498db; font-size:14px; text-align:center; margin-bottom:4px;">Select a Tier</div>
    <div style="color:#c8cdd5; font-size:13px; text-align:center;">Use the <b style="color:#fff;">tier buttons (S, A, B, C, D)</b> to choose which tier you want to place {subject_display} into.</div>
  </div>
  <div style="flex:1; min-width:180px; background:rgba(155,89,182,0.15); border:1px solid rgba(155,89,182,0.3); border-radius:10px; padding:14px;">
    <div style="font-size:28px; text-align:center; margin-bottom:6px;">2️⃣</div>
    <div style="font-weight:bold; color:#9b59b6; font-size:14px; text-align:center; margin-bottom:4px;">Click to Place</div>
    <div style="color:#c8cdd5; font-size:13px; text-align:center;">Scroll down and <b style="color:#fff;">hover over cards</b> to reveal the "Select" button. Click to place them in your chosen tier.</div>
  </div>
  <div style="flex:1; min-width:180px; background:rgba(46,204,113,0.15); border:1px solid rgba(46,204,113,0.3); border-radius:10px; padding:14px;">
    <div style="font-size:28px; text-align:center; margin-bottom:6px;">3️⃣</div>
    <div style="font-weight:bold; color:#2ecc71; font-size:14px; text-align:center; margin-bottom:4px;">Reorder & Submit</div>
    <div style="color:#c8cdd5; font-size:13px; text-align:center;">Click a {subject_name} in your tier list to <b style="color:#fff;">reorder with ⬅/➡</b> or remove with ✕. When done, hit <b style="color:#fff;">Submit</b>!</div>
  </div>
</div>
<div style="display:flex; gap:16px; flex-wrap:wrap; justify-content:center; margin-bottom:12px;">
  <div style="flex:1; min-width:200px; background:rgba(241,196,15,0.12); border:1px solid rgba(241,196,15,0.3); border-radius:10px; padding:12px;">
    <div style="font-weight:bold; color:#f1c40f; font-size:13px; text-align:center; margin-bottom:4px;">💡 Pro Tips</div>
    <div style="color:#c8cdd5; font-size:12px; text-align:center;">
      • <b style="color:#fff;">Partial rankings are welcome!</b> You don't need to rank every {subject_name} — your submission is valuable even if you only rate the ones you know<br>
      • Use <b style="color:#fff;">"Fill Remaining"</b> to quickly place all unplaced {subject_display} in a tier<br>
      • <b style="color:#fff;">Undo</b> button lets you revert recent placements
    </div>
  </div>
  <div style="flex:1; min-width:200px; background:rgba(231,76,60,0.12); border:1px solid rgba(231,76,60,0.3); border-radius:10px; padding:12px;">
    <div style="font-weight:bold; color:#e74c3c; font-size:13px; text-align:center; margin-bottom:4px;">🛠️ Tools</div>
    <div style="color:#c8cdd5; font-size:12px; text-align:center;">
      • <b style="color:#fff;">Export as PNG</b> — save your tier list as an image<br>
      • <b style="color:#fff;">Copy as Text</b> — share in Discord/text<br>
      • <b style="color:#fff;">Clear All</b> — start fresh
    </div>
  </div>
</div>
<div style="text-align:center; margin-top:4px;">
<span style="color:#a0a8b8; font-size:13px;">📺 <a href="https://youtu.be/TxU1NcryRS8" target="_blank" style="color:#3498db;">Video tutorial</a> &nbsp;|&nbsp; 💬 <a href="https://discord.gg/ReF5jDSHqV" target="_blank" style="color:#3498db;">Discord</a></span>
</div>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# VIEW MODE: Show the aggregated community tier list
# ════════════════════════════════════════════════════════════════════════════
if st.session_state.page_mode == "view":
    # Inject tier-label-block CSS for view mode
    st.markdown("""
    <style>
    .tier-label-block {
        background: var(--tier-color);
        color: #fff;
        font-weight: 900;
        font-size: 26px;
        text-align: center;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 52px;
        max-width: 52px;
        min-height: 120px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🏆 Community Tier List")
    if not data["submissions"]:
        st.info("No submissions yet — be the first to contribute!")
    else:
        # Compute interpolated average per subject across all submissions
        subject_scores_all = {s: [] for s in all_subjects}
        for sub in data["submissions"]:
            if isinstance(sub, dict) and any(isinstance(v, list) for v in sub.values()):
                scores = interpolate_scores(sub)
            else:
                scores = {}
                for subj, tier in sub.items():
                    if tier in TIER_POINTS:
                        scores[subj] = float(TIER_POINTS[tier])
            for subj, score in scores.items():
                if subj in subject_scores_all:
                    subject_scores_all[subj].append(score)

        subject_avg = {}
        for subj, scores_list in subject_scores_all.items():
            if scores_list:
                subject_avg[subj] = np.mean(scores_list)

        if not subject_avg:
            st.write(f"No {subject_name_plural} have been rated yet.")
        else:
            vals = np.array(list(subject_avg.values()))
            mean, std = vals.mean(), vals.std()

            comm_tiers = {"S": [], "A": [], "B": [], "C": [], "D": []}
            for subj, avg in subject_avg.items():
                if avg >= mean + 1.0 * std:
                    comm_tiers["S"].append((subj, avg))
                elif avg >= mean + 0.3 * std:
                    comm_tiers["A"].append((subj, avg))
                elif avg >= mean - 0.3 * std:
                    comm_tiers["B"].append((subj, avg))
                elif avg >= mean - 1.0 * std:
                    comm_tiers["C"].append((subj, avg))
                else:
                    comm_tiers["D"].append((subj, avg))

            for tier in TIERS:
                comm_tiers[tier].sort(key=lambda x: x[1], reverse=True)

            st.caption(f"Based on **{len(data['submissions'])}** community submission(s)")

            import base64 as _b64_view, os as _os_view
            @st.cache_data(show_spinner=False)
            def _img_data_uri_view(path):
                if not path or not _os_view.path.exists(path):
                    return ""
                ext = _os_view.path.splitext(path)[1].lower().lstrip(".")
                mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp"}.get(ext, "jpeg")
                with open(path, "rb") as f:
                    return f"data:image/{mime};base64,{_b64_view.b64encode(f.read()).decode()}"

            comm_html = ['<div style="display:flex;flex-direction:column;gap:0;">']
            for tier in TIERS:
                members = comm_tiers[tier]
                if not members:
                    continue
                comm_html.append(f'<div style="display:flex;align-items:stretch;gap:0;">')
                comm_html.append(f'<div class="tier-label-block" style="--tier-color:{TIER_COLORS[tier]};min-width:52px;max-width:52px;flex-shrink:0;">{tier}</div>')
                comm_html.append('<div style="display:flex;flex-wrap:wrap;gap:0;flex:1;align-items:flex-start;">')
                for subj, avg in members:
                    uri = _img_data_uri_view(subject_images.get(subj, ""))
                    if uri:
                        comm_html.append(
                            f'<div style="position:relative;height:120px;cursor:pointer;" title="{subj}">'
                            f'<img src="{uri}" alt="{subj}" style="display:block;height:100%;width:auto;">'
                            f'</div>'
                        )
                comm_html.append('</div></div>')
            comm_html.append('</div>')
            st.markdown(''.join(comm_html), unsafe_allow_html=True)

            # PNG download for community tier list
            tl_label = TIER_LIST_TYPES[current_tl_type]["label"]
            png_bytes = build_community_tier_png(comm_tiers, TIER_COLORS, subject_images, title=f"{tl_label} — Community")
            if png_bytes:
                st.download_button("⬇️ Download as PNG", png_bytes,
                                   file_name=f"community_{current_tl_type}.png", mime="image/png")

            st.markdown("---")
            st.markdown("**Want to contribute?** Switch to **Build Your Tier List** mode above to create and submit your own rankings!")

    render_footer()
    st.stop()

# ════════════════════════════════════════════════════════════════════════════
# BUILD MODE: Let users create their tier list
# ════════════════════════════════════════════════════════════════════════════
st.info(f"**{len(data['submissions'])}** community submission(s) on file. Build yours below!")

# ─── Build Your Tier List ───
st.markdown("### Build Your Tier List")
st.markdown(f"**Step 1:** Select a tier. **Step 2:** Click {subject_name_plural} to place them. "
            "**Step 3:** Reorder within each tier using ⬆/⬇.")

current_tier = st.session_state.assign_tier

# ─── Hide Select buttons unless hovering over a hero card ───
st.markdown("""
<style>
/* Overlay the Select / hero-name button on top of the hero image.
   Hidden by default, fades in on hover. Card stays full size.
   Applies to BOTH the tier-placement-section AND the hero-assignment-section. */
[data-testid="stVerticalBlock"]:has(.tier-placement-section) [data-testid="stColumn"]:has([data-testid="stImage"]),
[data-testid="stVerticalBlock"]:has(.hero-assignment-section) [data-testid="stColumn"]:has([data-testid="stImage"]) {
    position: relative;
}
[data-testid="stVerticalBlock"]:has(.tier-placement-section) [data-testid="stColumn"]:has([data-testid="stImage"]) .stButton,
[data-testid="stVerticalBlock"]:has(.hero-assignment-section) [data-testid="stColumn"]:has([data-testid="stImage"]) .stButton {
    position: absolute;
    bottom: 4px;
    left: 0;
    right: 0;
    z-index: 10;
    opacity: 0;
    transition: opacity 0.2s ease;
    pointer-events: none;
}
[data-testid="stVerticalBlock"]:has(.tier-placement-section) [data-testid="stColumn"]:has([data-testid="stImage"]):hover .stButton,
[data-testid="stVerticalBlock"]:has(.hero-assignment-section) [data-testid="stColumn"]:has([data-testid="stImage"]):hover .stButton {
    opacity: 1;
    pointer-events: auto;
}
/* Make the overlaid button semi-transparent so the card shows through */
[data-testid="stVerticalBlock"]:has(.tier-placement-section) [data-testid="stColumn"]:has([data-testid="stImage"]) .stButton button,
[data-testid="stVerticalBlock"]:has(.hero-assignment-section) [data-testid="stColumn"]:has([data-testid="stImage"]) .stButton button {
    background: rgba(0, 0, 0, 0.7);
    color: #fff;
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 6px;
    font-size: 12px;
    padding: 4px 0;
}
/* Compact rows: minimal gaps, no extra vertical space */
[data-testid="stVerticalBlock"]:has(.tier-placement-section) [data-testid="stHorizontalBlock"],
[data-testid="stVerticalBlock"]:has(.hero-assignment-section) [data-testid="stHorizontalBlock"] {
    gap: 2px !important;
    margin-bottom: 0 !important;
}
[data-testid="stVerticalBlock"]:has(.tier-placement-section) [data-testid="stColumn"],
[data-testid="stVerticalBlock"]:has(.hero-assignment-section) [data-testid="stColumn"] {
    padding: 0 !important;
}
[data-testid="stVerticalBlock"]:has(.tier-placement-section) [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stVerticalBlock"]:has(.tier-placement-section) [data-testid="stVerticalBlock"],
[data-testid="stVerticalBlock"]:has(.hero-assignment-section) [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stVerticalBlock"]:has(.hero-assignment-section) [data-testid="stVerticalBlock"] {
    gap: 2px !important;
}
/* Remove extra margin/padding on elements inside the sections */
[data-testid="stVerticalBlock"]:has(.tier-placement-section) .stMarkdown,
[data-testid="stVerticalBlock"]:has(.tier-placement-section) [data-testid="stImage"],
[data-testid="stVerticalBlock"]:has(.tier-placement-section) [data-testid="stCaptionContainer"],
[data-testid="stVerticalBlock"]:has(.hero-assignment-section) .stMarkdown,
[data-testid="stVerticalBlock"]:has(.hero-assignment-section) [data-testid="stImage"],
[data-testid="stVerticalBlock"]:has(.hero-assignment-section) [data-testid="stCaptionContainer"] {
    margin: 0 !important;
    padding: 0 !important;
}
/* Tier label block matches hero card height */
.tier-label-block {
    background: var(--tier-color);
    color: #fff;
    font-weight: 900;
    font-size: 26px;
    text-align: center;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    aspect-ratio: 0.715;
}
</style>
""", unsafe_allow_html=True)

# ─── Show current placement as horizontal tier rows ───
placed_count = len(placed_subjects)
if placed_count > 0:
    # Toggle between Edit and View modes
    if "tl_view_mode" not in st.session_state:
        st.session_state.tl_view_mode = False
    view_col1, view_col2 = st.columns([4, 1])
    with view_col1:
        st.markdown("### Your Current Tier List")
    with view_col2:
        view_label = "✏️ Edit" if st.session_state.tl_view_mode else "🖼️ View"
        if st.button(view_label, key="toggle_view_mode", width="stretch"):
            st.session_state.tl_view_mode = not st.session_state.tl_view_mode
            st.session_state.tl_selected = None
            st.rerun()

    if st.session_state.tl_view_mode:
        # ─── Pure HTML view mode ───
        import base64 as _b64v
        @st.cache_data(show_spinner=False)
        def _build_uri_map(_urls):
            out = {}
            for subj, path in _urls.items():
                if not path or not os.path.exists(path):
                    continue
                ext = os.path.splitext(path)[1].lower().lstrip(".")
                mime = {"jpg":"jpeg","jpeg":"jpeg","png":"png","gif":"gif","webp":"webp"}.get(ext,"jpeg")
                with open(path, "rb") as f:
                    out[subj] = f"data:image/{mime};base64,{_b64v.b64encode(f.read()).decode()}"
            return out
        _uri_map = _build_uri_map(dict(subject_images))

        view_parts = ['<div style="display:flex;flex-direction:column;gap:0;">']
        for tier in TIERS:
            members = placement[tier]
            view_parts.append('<div style="display:flex;align-items:stretch;gap:0;">')
            view_parts.append(f'<div class="tier-label-block" style="--tier-color:{TIER_COLORS[tier]};min-width:52px;max-width:52px;flex-shrink:0;">{tier}</div>')
            view_parts.append('<div style="display:flex;flex-wrap:wrap;gap:0;flex:1;align-items:flex-start;">')
            for subj in members:
                uri = _uri_map.get(subj, "")
                if uri:
                    view_parts.append(
                        f'<div style="position:relative;height:120px;">'
                        f'<img src="{uri}" alt="{subj}" style="display:block;height:100%;width:auto;">'
                        f'</div>'
                    )
            view_parts.append('</div></div>')
        view_parts.append('</div>')
        st.markdown(''.join(view_parts), unsafe_allow_html=True)
        st.caption(f"{placed_count} / {len(all_subjects)} {subject_name_plural} placed")
    else:
        # ─── Interactive edit mode ───
        tier_container = st.container()
        with tier_container:
            st.markdown('<div class="tier-placement-section"></div>', unsafe_allow_html=True)
            st.caption(f"{placed_count} / {len(all_subjects)} {subject_name_plural} placed  —  hover to select, then use controls below")

        # Track which subject is selected for editing
        if "tl_selected" not in st.session_state:
            st.session_state.tl_selected = None

        tier_hero_cols = 10  # subjects per row
        sel = st.session_state.tl_selected
        for tier in TIERS:
            members = placement[tier]
            # Always show the tier row (even empty) for the tiermaker look
            for row_start in range(0, max(len(members), 1), tier_hero_cols):
                row = members[row_start:row_start + tier_hero_cols] if members else []
                # First column is the tier label block, rest are subject slots
                col_widths = [0.6] + [1] * tier_hero_cols
                cols = st.columns(col_widths, gap="small")
                # Only show tier label on the first row of each tier
                with cols[0]:
                    if row_start == 0:
                        st.markdown(
                            f'<div class="tier-label-block" style="--tier-color:{TIER_COLORS[tier]};">{tier}</div>',
                            unsafe_allow_html=True,
                        )
                for k, subj in enumerate(row):
                    with cols[k + 1]:
                        img_url = subject_images.get(subj, "")
                        if img_url:
                            st.image(img_url, width="stretch")
                        real_idx = row_start + k
                        is_selected = sel == (tier, real_idx)
                        label = "✓" if is_selected else "Select"
                        if st.button(label, key=f"sel_{tier}_{real_idx}", width="stretch",
                                     help=subj):
                            if is_selected:
                                st.session_state.tl_selected = None
                            else:
                                st.session_state.tl_selected = (tier, real_idx)
                            st.rerun()

                # Show controls inline right after the row that contains the selected subject
                if sel and sel[0] == tier:
                    sel_tier, sel_idx = sel
                    if row_start <= sel_idx < row_start + len(row):
                        if sel_idx < len(placement[sel_tier]):
                            sel_subj = placement[sel_tier][sel_idx]
                            ctrl_cols = st.columns([2, 1, 1, 1, 1, 1, 1])
                            with ctrl_cols[0]:
                                st.markdown(f"**{sel_subj}** — {sel_tier} #{sel_idx + 1}")
                            with ctrl_cols[1]:
                                if sel_idx > 0:
                                    if st.button("⬅", key="ctrl_up", help="Move earlier in this tier"):
                                        m = placement[sel_tier]
                                        m[sel_idx], m[sel_idx - 1] = m[sel_idx - 1], m[sel_idx]
                                        st.session_state.tl_selected = (sel_tier, sel_idx - 1)
                                        st.rerun()
                                else:
                                    ti = TIERS.index(sel_tier)
                                    if ti > 0:
                                        prev_tier = TIERS[ti - 1]
                                        if st.button(f"⬅ {prev_tier}", key="ctrl_up"):
                                            subj = placement[sel_tier].pop(sel_idx)
                                            placement[prev_tier].append(subj)
                                            st.session_state.tl_selected = (prev_tier, len(placement[prev_tier]) - 1)
                                            st.rerun()
                            with ctrl_cols[2]:
                                if sel_idx < len(placement[sel_tier]) - 1:
                                    if st.button("➡", key="ctrl_down", help="Move later in this tier"):
                                        m = placement[sel_tier]
                                        m[sel_idx], m[sel_idx + 1] = m[sel_idx + 1], m[sel_idx]
                                        st.session_state.tl_selected = (sel_tier, sel_idx + 1)
                                        st.rerun()
                                else:
                                    ti = TIERS.index(sel_tier)
                                    if ti < len(TIERS) - 1:
                                        next_tier = TIERS[ti + 1]
                                        if st.button(f"➡ {next_tier}", key="ctrl_down"):
                                            subj = placement[sel_tier].pop(sel_idx)
                                            placement[next_tier].insert(0, subj)
                                            st.session_state.tl_selected = (next_tier, 0)
                                            st.rerun()
                            with ctrl_cols[3]:
                                if st.button("✕", key="ctrl_rm", help="Remove from tier list"):
                                    placement[sel_tier].pop(sel_idx)
                                    st.session_state.tl_selected = None
                                    st.rerun()
                            with ctrl_cols[4]:
                                other_tiers = [t for t in TIERS if t != sel_tier]
                                move_to = st.selectbox("Move to tier", other_tiers, key="ctrl_move_tier",
                                                       label_visibility="collapsed")
                            with ctrl_cols[5]:
                                if st.button(f"➜ {move_to}", key="ctrl_move"):
                                    subj = placement[sel_tier].pop(sel_idx)
                                    placement[move_to].append(subj)
                                    st.session_state.tl_selected = None
                                    st.rerun()
                            with ctrl_cols[6]:
                                if st.button("✓", key="ctrl_done", help="Deselect"):
                                    st.session_state.tl_selected = None
                                    st.rerun()

        # Clear stale selection
        if sel:
            sel_tier, sel_idx = sel
            if sel_tier not in placement or sel_idx >= len(placement[sel_tier]):
                st.session_state.tl_selected = None

    st.markdown("---")

# ─── Tier selector (right above the grid so you don't have to scroll) ───
current_tier = st.session_state.assign_tier
tier_idx = TIERS.index(current_tier) + 1  # 1-based for CSS nth-child

st.markdown(f"""
<style>
/* Style the active tier selector button with tier color */
.tier-selector-row > div:nth-child({tier_idx}) button {{
    background: {TIER_COLORS[current_tier]} !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    border: 2px solid {TIER_COLORS[current_tier]} !important;
    box-shadow: 0 0 10px {TIER_COLORS[current_tier]}66 !important;
    transform: scale(1.05);
    transition: all 0.2s ease;
}}
.tier-selector-row > div button {{
    transition: all 0.2s ease;
}}
</style>
""", unsafe_allow_html=True)

# Marker div so CSS can scope to this row
st.markdown('<div class="tier-selector-row">', unsafe_allow_html=True)
tier_cols = st.columns(len(TIERS))
for i, tier in enumerate(TIERS):
    with tier_cols[i]:
        is_active = st.session_state.assign_tier == tier
        count = len(placement[tier])
        label = f"{'▶ ' if is_active else ''}{tier} Tier ({count})"
        if st.button(label, key=f"tier_sel_{tier}", width="stretch"):
            st.session_state.assign_tier = tier
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ─── Subject image grid for assigning (only unplaced subjects) ───
unplaced_subjects = [s for s in all_subjects if s not in placed_subjects]
cols_per_row = 6

if unplaced_subjects:
    # ─── Sort + Format + Wave filter ───
    if is_villain_list:
        # Villains: Sort + Format filter (primary) + Wave filter (secondary — Legacy-aware)
        sort_col, fmt_col, wave_col = st.columns([1, 1, 1])
        with sort_col:
            sort_option = st.selectbox(
                "Sort order",
                ["Alphabetical (A→Z)", "Oldest → Newest", "Newest → Oldest"],
                key="villain_sort_order",
                label_visibility="collapsed",
            )
        with fmt_col:
            fmt_filter = st.selectbox(
                "Format",
                ["Current", "Legacy"],
                index=1,
                key="villain_fmt_filter",
                label_visibility="collapsed",
            )
        if fmt_filter == "Current":
            unplaced_subjects = [v for v in unplaced_subjects if not VILLAIN_LEGACY.get(v, False)]
        else:
            # Legacy includes ALL villains (current + legacy)
            with wave_col:
                wave_filter = st.multiselect(
                    "Filter by waves",
                    VILLAIN_WAVE_ORDER,
                    key="villain_wave_filter",
                    placeholder="All Waves",
                )
            if wave_filter:
                unplaced_subjects = [v for v in unplaced_subjects if VILLAIN_WAVE.get(v) in wave_filter]

        # Apply sort order for villains
        if sort_option == "Oldest → Newest":
            unplaced_subjects.sort(key=lambda v: VILLAIN_RELEASE_INDEX.get(v, 9999))
        elif sort_option == "Newest → Oldest":
            unplaced_subjects.sort(key=lambda v: VILLAIN_RELEASE_INDEX.get(v, 0), reverse=True)
        # else: already alphabetical from all_subjects
    else:
        # Heroes: Sort + Format filter (primary) + Wave filter (secondary — Legacy-aware)
        sort_col, fmt_col, wave_col = st.columns([1, 1, 1])
        with sort_col:
            sort_option = st.selectbox(
                "Sort order",
                ["Alphabetical (A→Z)", "Oldest → Newest", "Newest → Oldest"],
                key="hero_sort_order",
                label_visibility="collapsed",
            )
        with fmt_col:
            fmt_filter = st.selectbox(
                "Format",
                ["Current", "Legacy"],
                index=1,
                key="hero_fmt_filter",
                label_visibility="collapsed",
            )
        if fmt_filter == "Current":
            unplaced_subjects = [h for h in unplaced_subjects if not HERO_LEGACY.get(h, False)]
        else:
            # Legacy includes ALL heroes (current + legacy)
            with wave_col:
                wave_filter = st.multiselect(
                    "Filter by waves",
                    WAVE_ORDER,
                    key="hero_wave_filter",
                    placeholder="All Waves",
                )
            if wave_filter:
                unplaced_subjects = [h for h in unplaced_subjects if HERO_WAVE.get(h) in wave_filter]

        # Apply sort order
        if sort_option == "Oldest → Newest":
            unplaced_subjects.sort(key=lambda h: HERO_RELEASE_INDEX.get(h, 9999))
        elif sort_option == "Newest → Oldest":
            unplaced_subjects.sort(key=lambda h: HERO_RELEASE_INDEX.get(h, 0), reverse=True)
        # else: already alphabetical from all_subjects

    # ─── Controls row: search, undo, bulk assign ───
    ctrl1, ctrl2, ctrl3 = st.columns([3, 1, 1])
    with ctrl1:
        search_filter = st.text_input(f"🔍 Search {subject_name_plural}", key="subject_search",
                                    placeholder="Type to filter...",
                                    label_visibility="collapsed")
    with ctrl2:
        undo_disabled = len(undo_stack) == 0
        if st.button("↩ Undo", key="undo_place", width="stretch",
                     disabled=undo_disabled):
            tier, subj = undo_stack.pop()
            if subj in placement.get(tier, []):
                placement[tier].remove(subj)
            st.rerun()
    with ctrl3:
        if st.button(f"Place all → {current_tier}", key="bulk_assign",
                     width="stretch",
                     help=f"Put all remaining {subject_name_plural} into {current_tier} tier"):
            for s in unplaced_subjects:
                placement[current_tier].append(s)
                undo_stack.append((current_tier, s))
            st.rerun()

    # Apply search filter
    if search_filter:
        filtered_subjects = [s for s in unplaced_subjects
                           if search_filter.lower() in s.lower()]
    else:
        filtered_subjects = unplaced_subjects

    st.markdown('<div class="hero-assignment-section"></div>', unsafe_allow_html=True)
    st.caption(f"{len(filtered_subjects)} of {len(unplaced_subjects)} {subject_name_plural} remaining"
               + (f" (filtered)" if search_filter else ""))

    if filtered_subjects:
        for i in range(0, len(filtered_subjects), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                idx = i + j
                if idx >= len(filtered_subjects):
                    break
                subj = filtered_subjects[idx]
                with col:
                    img = subject_images.get(subj, "")
                    if img:
                        st.image(img, width="stretch")

                    if st.button(f"{subj}", key=f"place_{subj}", width="stretch"):
                        placement[current_tier].append(subj)
                        undo_stack.append((current_tier, subj))
                        st.rerun()
    elif search_filter:
        st.info(f'No {subject_name_plural} matching "{search_filter}"')
else:
    st.success(f"All {subject_name_plural} placed!")

# ─── Submit / Export ───
st.markdown("---")
already_submitted = current_tl_type in st.session_state.submitted_types

col_sub, col_clear, col_png = st.columns(3)
with col_sub:
    if already_submitted:
        st.info("✅ Already submitted this session")
    elif placed_count == 0:
        st.button("Place at least 1 to submit", disabled=True, width="stretch")
    elif st.button("✅ Submit My Tier List", type="primary", width="stretch"):
        # Store as {tier: [ordered subjects]}
        submission = {t: list(placement[t]) for t in TIERS}
        data["submissions"].append(submission)
        # Save the updated data back to the main data structure
        all_data[current_tl_type] = data
        save_data(all_data)
        st.session_state.community_tl_data = all_data
        st.session_state.submitted_types.add(current_tl_type)
        st.success("Submitted!")
with col_clear:
    if st.button("🗑️ Clear My Placements", width="stretch"):
        st.session_state.my_tier_placement[current_tl_type] = {t: [] for t in TIERS}
        st.session_state.tl_undo_stack[current_tl_type] = []
        st.rerun()
with col_png:
    if placed_count > 0:
        my_tiers = {t: list(placement[t]) for t in TIERS}
        tl_label = TIER_LIST_TYPES[current_tl_type]["label"]
        my_png = build_community_tier_png(my_tiers, TIER_COLORS, subject_images, title=f"My {tl_label}")
        if my_png:
            st.download_button("⬇️ Download as PNG", my_png,
                               file_name=f"my_{current_tl_type}.png", mime="image/png")

# ─── Tools (bottom, discrete) ───
st.markdown("---")
with st.expander("🛠️ Tools", expanded=False):

    # ─── Auto-place from preset (heroes only) ───
    if not is_villain_list:
        st.markdown("**Auto-place from preset**")
        st.caption("Use one of the home-page weighting presets to automatically "
                   "place all heroes into tiers. This will replace your current placements.")
        # Exclude the blank preset
        preset_names = [p for p in preset_options if p != "New (Everything Starts At Zero)"]
        chosen_preset = st.selectbox("Preset", preset_names, key="autoplace_preset")
        if st.button("🎯 Auto-place heroes", key="autoplace_go", width="stretch"):
            weights = preset_options[chosen_preset]
            scores = {hero: float(np.dot(stats, weights))
                      for hero, stats in default_heroes.items()}
            vals = np.array(list(scores.values()))
            mean_s, std_s = vals.mean(), max(vals.std(), 1e-6)
            new_placement = {t: [] for t in TIERS}
            for hero, sc in scores.items():
                if sc >= mean_s + 1.5 * std_s:
                    new_placement["S"].append(hero)
                elif sc >= mean_s + 0.5 * std_s:
                    new_placement["A"].append(hero)
                elif sc >= mean_s - 0.5 * std_s:
                    new_placement["B"].append(hero)
                elif sc >= mean_s - 1.5 * std_s:
                    new_placement["C"].append(hero)
                else:
                    new_placement["D"].append(hero)
            # Sort within each tier by score descending
            for t in TIERS:
                new_placement[t].sort(key=lambda h: scores[h], reverse=True)
            st.session_state.my_tier_placement[current_tl_type] = new_placement
            st.session_state.tl_undo_stack[current_tl_type] = []
            st.rerun()
    else:
        st.markdown("**Quick Actions**")
        st.caption("Tools for managing your tier list placements.")

render_footer()
