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
from data.constants import TIER_COLORS, HERO_ALTER_EGOS
from data.preset_options import preset_options
from data.hero_release_order import HERO_RELEASE_INDEX, HERO_WAVE, WAVE_ORDER, HERO_LEGACY, LEGACY_WAVE_ORDER
from data.villain_release_order import VILLAIN_RELEASE_INDEX, VILLAIN_WAVE, VILLAIN_WAVE_ORDER, VILLAIN_LEGACY
from components.github_storage import load_json, save_json
from components.nav_banner import render_nav_banner, render_page_header, render_footer
from components.hero_card_viewer import render_hero_card_viewer, show_hero_cards_button
from components import supabase_saved_lists as saved_lists

render_nav_banner("home")

TIERS = ["S", "A", "B", "C", "D", "F"]
TIER_POINTS = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1}
RATINGS_FILE = "community_tier_lists.json"

# Player count options (hero_power and villain_difficulty only)
PLAYER_COUNTS = ["Any", "Solo", "2-Player", "3-4 Player"]
PLAYER_COUNT_TYPES = {"hero_power", "villain_difficulty"}  # types that support player count

# Tier list type options
TIER_LIST_TYPES = {
    "hero_power": {"label": "🦸 Hero Power", "subject": "heroes", "metric": "power/strength"},
    "hero_fun": {"label": "🎮 Hero Fun", "subject": "heroes", "metric": "fun to play"},
    "villain_difficulty": {"label": "👿 Villain Difficulty", "subject": "villains", "metric": "difficulty"},
    "villain_fun": {"label": "🎭 Villain Fun", "subject": "villains", "metric": "fun to play against"},
}



render_page_header("Community Tier Lists", "Rate heroes and villains by power or fun — your voice shapes the rankings!")

_light = st.session_state.get("_light_mode", False)
_tier_label_extra = "color:#fff !important;text-shadow:2px 2px 0 #000,-1px -1px 0 rgba(0,0,0,0.3);" if _light else ""

# ─── Persistence helpers ───
def _subs_key(player_count):
    """Return the submissions key for a player count (e.g. 'submissions_solo')."""
    if player_count == "Any":
        return "submissions"
    return f"submissions_{player_count.lower().replace('-', '')}"

def _draft_key(tl_type, player_count="Any"):
    """Return the session-state key for a draft/undo bucket."""
    if tl_type in PLAYER_COUNT_TYPES:
        return f"{tl_type}:{_subs_key(player_count)}"
    return tl_type


def _draft_keys_for_type(tl_type):
    if tl_type in PLAYER_COUNT_TYPES:
        return [_draft_key(tl_type, player_count=pc) for pc in PLAYER_COUNTS]
    return [_draft_key(tl_type)]


def _normalize_data(data):
    """Ensure the community data matches the current schema."""
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
        # Ensure player-count sub-keys for applicable types
        if k in PLAYER_COUNT_TYPES:
            for pc in PLAYER_COUNTS:
                sk = _subs_key(pc)
                if sk not in data[k]:
                    data[k][sk] = []
    return data


def load_data(include_sha=False):
    data, sha = load_json(RATINGS_FILE, default={})
    data = _normalize_data(data)
    if include_sha:
        return data, sha
    return data


def save_data(data, sha=None):
    return save_json(data, RATINGS_FILE, sha=sha)


def submit_data(tl_type, player_count, submission):
    """Load the latest community data, merge the new submission, and save it."""
    supports_player_count = tl_type in PLAYER_COUNT_TYPES
    active_subs_key = _subs_key(player_count) if supports_player_count else "submissions"
    last_error = "Could not save your submission."

    for _ in range(3):
        all_data, data_sha = load_data(include_sha=True)
        data = all_data.get(tl_type, {"submissions": []})
        data.setdefault(active_subs_key, []).append(submission)
        if supports_player_count and active_subs_key != "submissions":
            data.setdefault("submissions", []).append(submission)
        all_data[tl_type] = data

        saved, error_message, retryable = save_data(all_data, sha=data_sha)
        if saved:
            return True, all_data, None

        last_error = error_message or last_error
        if not retryable:
            break

    return False, None, last_error


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


def build_community_tier_png(tiers, tier_colors, subject_images, title="Community Tier List", compact=False):
    """Render a tier list as a PNG image and return the bytes."""
    from PIL import Image, ImageDraw, ImageFont
    import io as _io

    tier_order = ["S", "A", "B", "C", "D", "F"]
    cards_per_row = 8
    full_card_h = 168
    card_w = 120
    card_h = int(full_card_h * 0.62) if compact else full_card_h
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
    img_h = len(all_rows) * row_h + padding

    canvas = Image.new("RGB", (img_w, img_h), color=(26, 26, 46))
    draw = ImageDraw.Draw(canvas)
    try:
        font_tier = ImageFont.truetype("arialbd.ttf", 32)
    except OSError:
        try:
            font_tier = ImageFont.truetype("arial.ttf", 32)
        except OSError:
            font_tier = ImageFont.load_default()

    def color_to_rgb(c):
        c = c.strip().lower()
        _map = {"red": (255, 0, 0), "orange": (255, 165, 0), "green": (0, 128, 0),
                "blue": (0, 0, 255), "purple": (128, 0, 128), "gray": (128, 128, 128)}
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
                    card_img = card_img.resize((card_w, full_card_h), Image.LANCZOS)
                    if compact:
                        card_img = card_img.crop((0, 0, card_w, card_h))
                    card_cache[name] = card_img
                except Exception:
                    pass

    y = 0
    for tier_label, tier_letter, names_in_row in all_rows:
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
    for draft_key in _draft_keys_for_type(tl_type):
        if draft_key not in st.session_state.my_tier_placement:
            st.session_state.my_tier_placement[draft_key] = {t: [] for t in TIERS}

if "assign_tier" not in st.session_state:
    st.session_state.assign_tier = "S"

# Player count for applicable tier list types
if "player_count" not in st.session_state:
    st.session_state.player_count = "Any"

# Track which tier list types the user has already submitted this session
if "submitted_types" not in st.session_state:
    st.session_state.submitted_types = set()

if "tl_undo_stack" not in st.session_state:
    st.session_state.tl_undo_stack = {}  # keyed by tier_list_type
for tl_type in TIER_LIST_TYPES.keys():
    for draft_key in _draft_keys_for_type(tl_type):
        if draft_key not in st.session_state.tl_undo_stack:
            st.session_state.tl_undo_stack[draft_key] = []

if "page_mode" not in st.session_state:
    st.session_state.page_mode = "view"  # "build" or "view"

# Sort-order source of truth — stored in plain (non-widget) session-state
# keys so they are never garbage-collected when st.rerun() terminates the
# script before the selectbox widget has been rendered.
for _sort_key in ("_hero_sort_val", "_villain_sort_val"):
    if _sort_key not in st.session_state:
        st.session_state[_sort_key] = "Oldest → Newest"

# Group-select mode for batch placement
if "tl_group_sel" not in st.session_state:
    st.session_state.tl_group_sel = set()
if "tl_group_mode" not in st.session_state:
    st.session_state.tl_group_mode = False

# Compact card view (crop text area)
if "tl_compact" not in st.session_state:
    st.session_state.tl_compact = True

# ─── Shared link ingest (?list=<slug>&edit=<token>) ──────────────────────────
# One-time per slug: fetch saved list from Supabase, overwrite current draft
# for the saved tier_list_type, switch to that type, set Build mode.
# Player-count is NOT auto-switched (per locked decision); we just warn on
# mismatch via _loaded_list_pc_warning.
if saved_lists.is_enabled():
    _qp = st.query_params
    _qp_slug = _qp.get("list")
    _qp_edit = _qp.get("edit")
    if isinstance(_qp_slug, list):  # defensive (older streamlit)
        _qp_slug = _qp_slug[0] if _qp_slug else None
    if isinstance(_qp_edit, list):
        _qp_edit = _qp_edit[0] if _qp_edit else None

    if _qp_slug and st.session_state.get("_loaded_list_slug") != _qp_slug:
        if not saved_lists.is_valid_slug(_qp_slug):
            st.session_state["_loaded_list_slug"] = _qp_slug  # don't retry
            st.warning("That share link doesn't look valid.")
        else:
            ok, row, err = saved_lists.get_saved_list_by_slug(_qp_slug)
            if not ok:
                st.session_state["_loaded_list_slug"] = _qp_slug
                st.error(f"Could not load shared tier list: {err}")
            elif row is None:
                st.session_state["_loaded_list_slug"] = _qp_slug
                st.warning("Shared tier list not found. It may have been deleted.")
            else:
                _saved_type = row.get("tier_list_type") or "hero_power"
                _saved_pc = row.get("player_count") or "Any"
                _payload = row.get("payload_json") or {}

                # Pick valid catalog for type-aware normalization
                if TIER_LIST_TYPES.get(_saved_type, {}).get("subject") == "villains":
                    _valid = set(all_villains)
                else:
                    _valid = set(all_heroes)
                _norm = saved_lists.normalize_payload(_payload, _valid)

                # Apply: type switch, draft overwrite for that type's bucket
                st.session_state.tier_list_type = _saved_type
                _supports_pc = _saved_type in PLAYER_COUNT_TYPES
                # Overwrite the bucket that matches the saved type+pc so it is
                # findable when the user changes player count later.
                _target_pc = _saved_pc if _supports_pc else "Any"
                _target_key = _draft_key(_saved_type, _target_pc)
                st.session_state.my_tier_placement[_target_key] = {
                    t: list(_norm["tiers"].get(t, [])) for t in TIERS
                }
                st.session_state.tl_undo_stack[_target_key] = []

                # Warn (not switch) if current player_count differs
                if _supports_pc and st.session_state.get("player_count", "Any") != _target_pc:
                    st.session_state["_loaded_list_pc_warning"] = (
                        f"This shared list was saved for **{_target_pc}**. "
                        f"Switch player count to view it in that context."
                    )
                else:
                    st.session_state.pop("_loaded_list_pc_warning", None)

                # Remember slug so the share-link box can re-show it
                st.session_state["_loaded_list_slug"] = _qp_slug
                st.session_state["saved_list_known_slug"] = _qp_slug

                # Force Build mode so user sees the loaded draft
                st.session_state.page_mode = "build"
                st.toast("📥 Loaded shared tier list.")
                st.rerun()

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

# Player count selector (hero_power and villain_difficulty only)
supports_player_count = current_tl_type in PLAYER_COUNT_TYPES
if supports_player_count:
    pc_cols = st.columns(len(PLAYER_COUNTS))
    for i, pc in enumerate(PLAYER_COUNTS):
        with pc_cols[i]:
            is_active = st.session_state.player_count == pc
            btn_type = "primary" if is_active else "secondary"
            if st.button(pc, key=f"pc_{pc}", width="stretch", type=btn_type):
                st.session_state.player_count = pc
                st.rerun()

current_player_count = st.session_state.player_count if supports_player_count else "Any"
current_draft_key = _draft_key(current_tl_type, current_player_count)

# Get data and placement for current tier list type
all_data = st.session_state.community_tl_data
data = all_data.get(current_tl_type, {"submissions": []})
# Resolve the active submissions list for the current player count
active_subs_key = _subs_key(current_player_count) if supports_player_count else "submissions"
active_submissions = data.get(active_subs_key, [])
placement = st.session_state.my_tier_placement[current_draft_key]
undo_stack = st.session_state.tl_undo_stack[current_draft_key]

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
    <div style="color:#c8cdd5; font-size:13px; text-align:center;">{subject_display} are grouped into <b style="color:#fff;">S, A, B, C, D, F</b> tiers based on their average score. Higher = better.</div>
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
    <div style="color:#c8cdd5; font-size:13px; text-align:center;">Use the <b style="color:#fff;">tier buttons (S, A, B, C, D, F)</b> to choose which tier you want to place {subject_display} into.</div>
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
    _community_row_h = "74px" if st.session_state.get("tl_compact", True) else "120px"
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
        min-height: %s;
    }
    </style>
    """ % _community_row_h, unsafe_allow_html=True)
    
    st.markdown("### 🏆 Community Tier List")
    if not active_submissions:
        st.info("No submissions yet — be the first to contribute!")
    else:
        # Compute interpolated average per subject across all submissions
        subject_scores_all = {s: [] for s in all_subjects}
        for sub in active_submissions:
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
            mean, std = vals.mean(), max(vals.std(), 1e-6)

            comm_tiers = {"S": [], "A": [], "B": [], "C": [], "D": [], "F": []}
            for subj, avg in subject_avg.items():
                if avg >= mean + 1.0 * std:
                    comm_tiers["S"].append((subj, avg))
                elif avg >= mean + 0.3 * std:
                    comm_tiers["A"].append((subj, avg))
                elif avg >= mean - 0.3 * std:
                    comm_tiers["B"].append((subj, avg))
                elif avg >= mean - 1.0 * std:
                    comm_tiers["C"].append((subj, avg))
                elif avg >= mean - 1.5 * std:
                    comm_tiers["D"].append((subj, avg))
                else:
                    comm_tiers["F"].append((subj, avg))

            for tier in TIERS:
                comm_tiers[tier].sort(key=lambda x: x[1], reverse=True)

            _pc_label = f" ({current_player_count})" if supports_player_count and current_player_count != "Any" else ""
            st.caption(f"Based on **{len(active_submissions)}** community submission(s){_pc_label}")

            import base64 as _b64_view, os as _os_view
            @st.cache_data(show_spinner=False)
            def _img_data_uri_view(path):
                if not path or not _os_view.path.exists(path):
                    return ""
                ext = _os_view.path.splitext(path)[1].lower().lstrip(".")
                mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp"}.get(ext, "jpeg")
                with open(path, "rb") as f:
                    return f"data:image/{mime};base64,{_b64_view.b64encode(f.read()).decode()}"

            _comm_compact_cls = " compact-view" if st.session_state.get("tl_compact", True) else ""
            _comm_card_h = "74px" if st.session_state.get("tl_compact", True) else "120px"
            comm_html = [f'<div class="tier-view-wrap{_comm_compact_cls}" style="display:flex;flex-direction:column;gap:0;">']
            for tier in TIERS:
                members = comm_tiers[tier]
                if not members:
                    continue
                comm_html.append(f'<div style="display:flex;align-items:stretch;gap:0;">')
                comm_html.append(f'<div class="tier-label-block" style="--tier-color:{TIER_COLORS[tier]};min-width:52px;max-width:52px;flex-shrink:0;{_tier_label_extra}">{tier}</div>')
                comm_html.append('<div style="display:flex;flex-wrap:wrap;gap:0;flex:1;align-items:flex-start;">')
                for subj, avg in members:
                    uri = _img_data_uri_view(subject_images.get(subj, ""))
                    if uri:
                        comm_html.append(
                            f'<div class="hero-card" style="position:relative;height:{_comm_card_h};overflow:hidden;cursor:pointer;" title="{subj}">'
                            f'<img src="{uri}" alt="{subj}" style="display:block;height:120px;width:auto;">'
                            f'</div>'
                        )
                comm_html.append('</div></div>')
            comm_html.append('</div>')
            st.markdown(''.join(comm_html), unsafe_allow_html=True)

            # Hero card viewer (hero lists only)
            if not is_villain_list:
                render_hero_card_viewer(
                    [subj for tier in TIERS for subj, _ in comm_tiers[tier]],
                    alter_egos=HERO_ALTER_EGOS,
                    key_prefix="comm_view_hcv",
                )

            # PNG download for community tier list
            tl_label = TIER_LIST_TYPES[current_tl_type]["label"]
            png_bytes = build_community_tier_png(comm_tiers, TIER_COLORS, subject_images, title=f"{tl_label} — Community", compact=st.session_state.get("tl_compact", False))
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
st.info(f"**{len(active_submissions)}** community submission(s) on file. Build yours below!")

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
/* ─── Compact mode: crop card images to art only (top ~62%) ─── */
[data-testid="stVerticalBlock"]:has(.compact-cards) [data-testid="stImage"] {
    overflow: hidden !important;
    aspect-ratio: 1.153;
}
[data-testid="stVerticalBlock"]:has(.compact-cards) [data-testid="stImage"] img {
    width: 100% !important;
    height: auto !important;
}
[data-testid="stVerticalBlock"]:has(.compact-cards) .tier-label-block {
    aspect-ratio: 1.153;
    font-size: 22px;
}
/* Compact mode for HTML view tier rows */
.compact-view .hero-card {
    overflow: hidden;
}
.compact-view .hero-card img {
    object-fit: cover;
    object-position: top;
}
</style>
""", unsafe_allow_html=True)

# ─── Show current placement as horizontal tier rows ───
placed_count = len(placed_subjects)
if placed_count > 0:
    # Toggle between Edit and View modes
    if "tl_view_mode" not in st.session_state:
        st.session_state.tl_view_mode = False
    view_col1, view_col2, view_col3 = st.columns([4, 1, 1])
    with view_col1:
        st.markdown("### Your Tier List")
    with view_col2:
        compact_label = "📋 Full" if st.session_state.tl_compact else "🔍 Compact"
        if st.button(compact_label, key="toggle_compact", width="stretch"):
            st.session_state.tl_compact = not st.session_state.tl_compact
            st.rerun()
    with view_col3:
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

        _compact_cls = " compact-view" if st.session_state.tl_compact else ""
        view_parts = [f'<div class="tier-view-wrap{_compact_cls}" style="display:flex;flex-direction:column;gap:0;">']
        _view_card_h = "74px" if st.session_state.tl_compact else "120px"
        for tier in TIERS:
            members = placement[tier]
            view_parts.append('<div style="display:flex;align-items:stretch;gap:0;">')
            view_parts.append(f'<div class="tier-label-block" style="--tier-color:{TIER_COLORS[tier]};min-width:52px;max-width:52px;flex-shrink:0;{_tier_label_extra}">{tier}</div>')
            view_parts.append('<div style="display:flex;flex-wrap:wrap;gap:0;flex:1;align-items:flex-start;">')
            for subj in members:
                uri = _uri_map.get(subj, "")
                if uri:
                    view_parts.append(
                        f'<div class="hero-card" style="position:relative;height:{_view_card_h};overflow:hidden;">'
                        f'<img src="{uri}" alt="{subj}" style="display:block;height:120px;width:auto;">'
                        f'</div>'
                    )
            view_parts.append('</div></div>')
        view_parts.append('</div>')
        st.markdown(''.join(view_parts), unsafe_allow_html=True)
        st.caption(f"{placed_count} / {len(all_subjects)} {subject_name_plural} placed")
    else:
        # ─── Interactive edit mode ───
        _compact_edit = " compact-cards" if st.session_state.tl_compact else ""
        tier_container = st.container()
        with tier_container:
            st.markdown(f'<div class="tier-placement-section{_compact_edit}"></div>', unsafe_allow_html=True)
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
                            f'<div class="tier-label-block" style="--tier-color:{TIER_COLORS[tier]};{_tier_label_extra}">{tier}</div>',
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
                            ctrl_cols = st.columns([2, 1, 1, 1, 1, 1, 1] + ([0.6] if not is_villain_list else []))
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
                            if not is_villain_list:
                                with ctrl_cols[7]:
                                    show_hero_cards_button(sel_subj, alter_ego_hint=HERO_ALTER_EGOS.get(sel_subj, ""), key="ctrl_cards")

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
    _SORT_OPTIONS = ["Alphabetical (A→Z)", "Oldest → Newest", "Newest → Oldest"]
    # ─── Sort + Format + Wave filter ───
    if is_villain_list:
        # Villains: Sort + Format filter (primary) + Wave filter (secondary — Legacy-aware)
        _v_val = st.session_state.get("_villain_sort_val", "Oldest → Newest")
        _v_sort_idx = _SORT_OPTIONS.index(_v_val) if _v_val in _SORT_OPTIONS else 1
        sort_col, fmt_col, wave_col = st.columns([1, 1, 1])
        with sort_col:
            sort_option = st.selectbox(
                "Sort order",
                _SORT_OPTIONS,
                index=_v_sort_idx,
                key="villain_sort_order",
                label_visibility="collapsed",
            )
            st.session_state._villain_sort_val = sort_option
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
        _h_val = st.session_state.get("_hero_sort_val", "Oldest → Newest")
        _h_sort_idx = _SORT_OPTIONS.index(_h_val) if _h_val in _SORT_OPTIONS else 1
        sort_col, fmt_col, wave_col = st.columns([1, 1, 1])
        with sort_col:
            sort_option = st.selectbox(
                "Sort order",
                _SORT_OPTIONS,
                index=_h_sort_idx,
                key="hero_sort_order",
                label_visibility="collapsed",
            )
            st.session_state._hero_sort_val = sort_option
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

    # ─── Controls row: search, undo, group select, bulk assign ───
    group_mode = st.session_state.tl_group_mode
    group_sel = st.session_state.tl_group_sel
    # Prune stale selections (already placed heroes)
    group_sel -= placed_subjects

    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([3, 1, 1, 1])
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
        gs_label = f"☑ Select ({len(group_sel)})" if group_mode else "☐ Select"
        if st.button(gs_label, key="toggle_group_mode", width="stretch",
                     help="Toggle group-select mode to pick multiple, then place them together"):
            st.session_state.tl_group_mode = not group_mode
            if not group_mode is False:
                pass  # keep selections when toggling on
            st.rerun()
    with ctrl4:
        if group_mode and group_sel:
            if st.button(f"Place {len(group_sel)} → {current_tier}", key="group_place",
                         width="stretch"):
                for s in unplaced_subjects:
                    if s in group_sel:
                        placement[current_tier].append(s)
                        undo_stack.append((current_tier, s))
                group_sel.clear()
                st.session_state.tl_group_mode = False
                st.rerun()
        else:
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

    _compact_grid = " compact-cards" if st.session_state.tl_compact else ""
    st.markdown(f'<div class="hero-assignment-section{_compact_grid}"></div>', unsafe_allow_html=True)
    st.caption(f"{len(filtered_subjects)} of {len(unplaced_subjects)} {subject_name_plural} remaining"
               + (f" (filtered)" if search_filter else ""))

    # Hero card viewer (hero lists only)
    if not is_villain_list:
        render_hero_card_viewer(all_subjects, alter_egos=HERO_ALTER_EGOS, key_prefix="build_hcv")

    if filtered_subjects:
        for i in range(0, len(filtered_subjects), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                idx = i + j
                if idx >= len(filtered_subjects):
                    break
                subj = filtered_subjects[idx]
                with col:
                    is_selected = group_mode and subj in group_sel
                    img = subject_images.get(subj, "")
                    if img:
                        st.image(img, width="stretch")

                    if group_mode:
                        btn_label = f"✓ {subj}" if is_selected else subj
                        if st.button(btn_label, key=f"place_{subj}", width="stretch",
                                     type="primary" if is_selected else "secondary"):
                            if subj in group_sel:
                                group_sel.discard(subj)
                            else:
                                group_sel.add(subj)
                            st.rerun()
                    else:
                        if st.button(f"{subj}", key=f"place_{subj}", width="stretch"):
                            placement[current_tier].append(subj)
                            undo_stack.append((current_tier, subj))
                            st.session_state.tl_selected = None
                            st.rerun()
    elif search_filter:
        st.info(f'No {subject_name_plural} matching "{search_filter}"')
else:
    st.success(f"All {subject_name_plural} placed!")

# ─── Submit / Export ───
st.markdown("---")
_submit_key = f"{current_tl_type}_{current_player_count}" if supports_player_count else current_tl_type
already_submitted = _submit_key in st.session_state.submitted_types

col_sub, col_clear, col_png = st.columns(3)
with col_sub:
    if already_submitted:
        st.info("✅ Already submitted this session")
    elif placed_count == 0:
        st.button("Place at least 1 to submit", disabled=True, width="stretch")
    elif st.button("✅ Submit My Tier List", type="primary", width="stretch"):
        # Store as {tier: [ordered subjects]}
        submission = {t: list(placement[t]) for t in TIERS}
        saved, updated_data, error_message = submit_data(current_tl_type, current_player_count, submission)
        if saved:
            st.session_state.community_tl_data = updated_data
            st.session_state.submitted_types.add(_submit_key)
            st.success("Submitted!")
        else:
            st.error(error_message)
with col_clear:
    if st.button("🗑️ Clear My Placements", width="stretch"):
        st.session_state.my_tier_placement[current_draft_key] = {t: [] for t in TIERS}
        st.session_state.tl_undo_stack[current_draft_key] = []
        st.rerun()
with col_png:
    if placed_count > 0:
        my_tiers = {t: list(placement[t]) for t in TIERS}
        tl_label = TIER_LIST_TYPES[current_tl_type]["label"]
        my_png = build_community_tier_png(my_tiers, TIER_COLORS, subject_images, title=f"My {tl_label}", compact=st.session_state.get("tl_compact", False))
        if my_png:
            st.download_button("⬇️ Download as PNG", my_png,
                               file_name=f"my_{current_tl_type}.png", mime="image/png")

# ─── Save & Share (Supabase) ─────────────────────────────────────────────────
if saved_lists.is_enabled():
    if st.session_state.get("_loaded_list_pc_warning"):
        st.warning(st.session_state["_loaded_list_pc_warning"])

    with st.expander("🔗 Save & Share This Tier List", expanded=False):
        st.caption(
            "Save your tier list to a permanent link you can share, or paste a "
            "link someone shared with you to load their tier list."
        )

        # ── Load a shared tier list ──
        st.markdown("**📥 Load a shared tier list**")
        import urllib.parse as _urlparse
        _load_input = st.text_input(
            "Paste a shared link",
            key="saved_list_load_input",
            placeholder="e.g. https://...?list=gRPnZxPX  or just  gRPnZxPX",
            help="Paste any share link or code. We'll auto-load it onto the tier list.",
        )
        if st.button(
            "Load tier list",
            key="saved_list_load_btn",
            disabled=not _load_input.strip(),
            width="stretch",
        ):
            _raw = _load_input.strip()
            _parsed = _urlparse.parse_qs(_urlparse.urlparse(_raw).query)
            _slug = (_parsed.get("list") or [""])[0].strip()
            if not _slug:
                # No query string — treat as bare slug (strip any leading "?list=")
                _slug = _raw.split("?list=")[-1].split("&")[0].strip().lstrip("/")
            if not saved_lists.is_valid_slug(_slug):
                st.error("That doesn't look like a valid share link or code.")
            else:
                # Clear any previous load marker so the ingest block re-runs
                st.session_state.pop("_loaded_list_slug", None)
                st.query_params["list"] = _slug
                st.rerun()

        st.markdown("---")

        # ── Save current tier list ──
        st.markdown("**💾 Save & share this tier list**")

        # Per-session save-rate guard
        st.session_state.setdefault("_saved_list_save_times", [])
        SAVE_RATE_WINDOW_SEC = 3600
        SAVE_RATE_MAX = 5

        new_title = st.text_input(
            "Title (optional)",
            key="saved_list_new_title",
            max_chars=80,
            placeholder="e.g. My Solo Power Rankings",
        )
        create_disabled = placed_count == 0
        if st.button(
            "Save & get share link",
            key="saved_list_create_btn",
            type="primary",
            disabled=create_disabled,
            help="Place at least one hero/villain first." if create_disabled else None,
            width="stretch",
        ):
            import time as _time
            _now = _time.time()
            _recent = [t for t in st.session_state["_saved_list_save_times"] if _now - t < SAVE_RATE_WINDOW_SEC]
            if len(_recent) >= SAVE_RATE_MAX:
                st.error("You've saved a lot recently. Please wait a bit before saving again.")
            else:
                ok, info, err = saved_lists.create_saved_list(
                    tiers={t: list(placement[t]) for t in TIERS},
                    tier_list_type=current_tl_type,
                    player_count=current_player_count,
                    title=new_title or None,
                )
                if ok and info:
                    _recent.append(_now)
                    st.session_state["_saved_list_save_times"] = _recent
                    st.session_state["saved_list_known_slug"] = info["slug"]
                    st.success("Saved! Your share link is below.")
                else:
                    st.error(err or "Could not save.")

        # ── Show share link as a full URL (built client-side via JS) ──
        _last_slug = st.session_state.get("saved_list_known_slug")
        if _last_slug:
            import streamlit.components.v1 as _components
            import json as _json
            _slug_js = _json.dumps(_last_slug)
            _components.html(
                f"""
                <div style="font-family: 'Source Sans Pro', sans-serif; margin-top: 4px;">
                  <label style="font-size: 14px; color: rgba(250,250,250,0.85);
                                display:block; margin-bottom: 4px;">
                    Your share link:
                  </label>
                  <div style="display: flex; gap: 6px;">
                    <input id="shareLinkBox" type="text" readonly
                      style="flex:1; padding: 8px 10px; border-radius: 6px;
                             border: 1px solid rgba(250,250,250,0.2);
                             background: rgba(38,39,48,1); color: #fafafa;
                             font-family: 'Source Code Pro', monospace; font-size: 13px;"/>
                    <button id="copyShareBtn"
                      style="padding: 8px 14px; border-radius: 6px; border: none;
                             background: #ff4b4b; color: white; cursor: pointer;
                             font-weight: 600;">Copy</button>
                  </div>
                  <div id="copyShareMsg" style="font-size:12px; color:#7ee787;
                       margin-top:4px; min-height:16px;"></div>
                </div>
                <script>
                  const slug = {_slug_js};
                  // Streamlit embeds this in an iframe; use parent location.
                  const loc = window.parent.location;
                  const url = loc.origin + loc.pathname + "?list=" + slug;
                  const box = document.getElementById("shareLinkBox");
                  const btn = document.getElementById("copyShareBtn");
                  const msg = document.getElementById("copyShareMsg");
                  box.value = url;
                  btn.addEventListener("click", async () => {{
                    try {{
                      await navigator.clipboard.writeText(url);
                      msg.textContent = "✓ Copied!";
                      setTimeout(() => {{ msg.textContent = ""; }}, 2000);
                    }} catch (e) {{
                      box.select(); document.execCommand("copy");
                      msg.textContent = "✓ Copied!";
                      setTimeout(() => {{ msg.textContent = ""; }}, 2000);
                    }}
                  }});
                </script>
                """,
                height=110,
            )
            st.caption(
                "Anyone with this link can view your tier list. "
                "Saving again will create a new link — old links keep working."
            )
else:
    # Feature not configured — keep silent in UI to avoid noise.
    pass

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
                elif sc >= mean_s - 1.0 * std_s:
                    new_placement["C"].append(hero)
                elif sc >= mean_s - 1.5 * std_s:
                    new_placement["D"].append(hero)
                else:
                    new_placement["F"].append(hero)
            # Sort within each tier by score descending
            for t in TIERS:
                new_placement[t].sort(key=lambda h: scores[h], reverse=True)
            st.session_state.my_tier_placement[current_draft_key] = new_placement
            st.session_state.tl_undo_stack[current_draft_key] = []
            st.rerun()
    else:
        st.markdown("**Quick Actions**")
        st.caption("Tools for managing your tier list placements.")

render_footer()
