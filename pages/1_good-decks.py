"""
Deck Lists - Browse MarvelCDB deck lists for every hero
"""

import streamlit as st
import requests
import json
import re
import random
import os
import base64
from urllib.parse import quote
import numpy as np
from html import escape as html_escape
from data.hero_decks import hero_decks
from data.hero_image_urls import hero_image_urls
from data.constants import HERO_ALTER_EGOS
from components.nav_banner import render_nav_banner, render_page_header, render_footer
from components.hero_card_viewer import get_obligation_nemesis, open_hero_cards_dialog
from components.github_storage import load_json
from data.hero_release_order import HERO_RELEASE_INDEX, HERO_WAVE, WAVE_ORDER

render_nav_banner("good-decks")

# ─── Custom CSS ───
st.markdown("""
<style>
    .deck-title {
        font-family: 'Bangers', cursive, Impact, sans-serif;
        font-size: 26px;
        font-weight: bold;
        color: white;
        margin-bottom: 6px;
        letter-spacing: 1.2px;
        text-shadow: 1px 1px 0 #000;
        line-height: 1.15;
    }
    .deck-summary-note {
        font-size: 13px;
        color: #d0d0d0;
        margin-bottom: 10px;
        letter-spacing: 0.02em;
    }
    .aspect-badge {
        display: inline-block;
        padding: 3px 11px;
        border-radius: 3px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: white;
        margin-left: 8px;
        vertical-align: middle;
        text-shadow: 0 1px 1px rgba(0,0,0,0.4);
        box-shadow: 1px 1px 0 rgba(0,0,0,0.45);
    }
    .aspect-aggression { background-color: #c0392b; }
    .aspect-justice { background-color: #d4a017; }
    .aspect-leadership { background-color: #2471a3; }
    .aspect-protection { background-color: #27ae60; }
    .aspect-basic { background-color: #7f8c8d; }
    .aspect-pool { background-color: #8e44ad; }

    .card-type-header {
        font-size: 13px;
        font-weight: bold;
        padding: 3px 8px;
        border-radius: 4px;
        margin: 8px 0 3px 0;
        border-left: 3px solid;
        opacity: 0.9;
    }
    .faction-header {
        font-size: 15px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 6px 10px;
        border-radius: 8px;
        margin: 0 0 8px 0;
        border: 1px solid;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06);
    }
    .type-hero { border-color: #9b59b6; background: rgba(155,89,182,0.18); color: #d6a8e6; }
    .type-aggression { border-color: #c0392b; background: rgba(192,57,43,0.12); color: #e74c3c; }
    .type-justice { border-color: #d4a017; background: rgba(212,160,23,0.12); color: #f1c40f; }
    .type-leadership { border-color: #2471a3; background: rgba(36,113,163,0.12); color: #3498db; }
    .type-protection { border-color: #27ae60; background: rgba(39,174,96,0.12); color: #2ecc71; }
    .type-basic { border-color: #7f8c8d; background: rgba(127,140,141,0.12); color: #bdc3c7; }
    .type-pool { border-color: #8e44ad; background: rgba(142,68,173,0.12); color: #a569bd; }

    .card-row {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 2px 8px;
        border-radius: 3px;
        margin-bottom: 0px;
        position: relative;
        border-left: 2px solid transparent;
        transition: background 0.12s ease, border-color 0.12s ease;
    }
    .card-row:hover {
        background: rgba(255,255,255,0.07);
        border-left-color: #ed1c24;
    }
    .card-qty {
        font-weight: bold;
        font-size: 13px;
        color: #f0f0f0;
        min-width: 20px;
        text-align: center;
    }
    .card-name {
        font-size: 13px;
        color: #e0e0e0;
        flex-grow: 1;
        position: relative;
    }
    .card-name a {
        color: #e0e0e0;
        text-decoration: none;
    }
    .card-name a:hover {
        color: #3498db;
        text-decoration: underline;
    }
    .card-cost {
        font-size: 11px;
        color: #aaa;
        min-width: 30px;
        text-align: right;
    }
    .aspect-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .dot-aggression { background: #c0392b; }
    .dot-justice { background: #d4a017; }
    .dot-leadership { background: #2471a3; }
    .dot-protection { background: #27ae60; }
    .dot-basic { background: #7f8c8d; }
    .dot-pool { background: #8e44ad; }
    .dot-hero { background: #95a5a6; }
    /* Hover image tooltip */
    .card-hover-wrap {
        position: relative;
        display: inline;
    }
    .card-hover-wrap .card-tooltip-img {
        display: none;
        position: fixed;
        z-index: 9999;
        width: 250px;
        border-radius: 6px;
        border: 2px solid #555;
        box-shadow: 0 4px 20px rgba(0,0,0,0.7);
        pointer-events: none;
        top: 50%;
        right: 20px;
        transform: translateY(-50%);
    }
    .card-hover-wrap:hover .card-tooltip-img {
        display: block;
    }
    .deck-stats {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        align-items: center;
        margin: 6px 0 12px 0;
    }
    .deck-stat {
        background: rgba(255,255,255,0.05);
        padding: 4px 12px;
        border-radius: 3px;
        font-size: 12px;
        color: #ccc;
        border: 1px solid rgba(255,255,255,0.07);
        border-left: 3px solid rgba(237,28,36,0.6);
    }
    .deck-stat strong {
        color: #f7c948;
        font-family: 'Bangers', cursive, Impact, sans-serif;
        letter-spacing: 0.8px;
        font-size: 14px;
        margin-right: 3px;
    }
    .mcdb-link {
        display: inline-block;
        padding: 4px 14px;
        background: linear-gradient(180deg, #2980b9 0%, #1a5276 100%);
        color: white !important;
        border-radius: 3px;
        text-decoration: none;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
        margin-top: 2px;
        box-shadow: 1px 1px 0 rgba(0,0,0,0.4);
        transition: transform 0.12s ease, box-shadow 0.12s ease;
    }
    .mcdb-link:hover {
        background: linear-gradient(180deg, #3498db 0%, #2471a3 100%);
        color: white !important;
        transform: translate(-1px, -1px);
        box-shadow: 2px 2px 0 rgba(0,0,0,0.5);
    }
    .section-divider {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.1);
        margin: 6px 0;
    }
    /* Two-column deck layout */
    .deck-section-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 20px;
        align-items: start;
        margin-bottom: 10px;
    }
    .deck-section-column {
        min-width: 0;
    }
    .faction-section {
        margin-bottom: 4px;
    }
    @media (max-width: 900px) {
        .deck-section-grid {
            grid-template-columns: 1fr;
            gap: 0;
        }
    }

    /* ── Hero browse grid: cropped (compact) hero cards with centered button below ── */
    [data-testid="stVerticalBlock"]:has(.deck-hero-browse) [data-testid="stImage"] {
        overflow: hidden !important;
        aspect-ratio: 1.153;
        border-radius: 6px;
        width: 100% !important;
    }
    [data-testid="stVerticalBlock"]:has(.deck-hero-browse) [data-testid="stImage"] img {
        width: 100% !important;
        height: 100% !important;
        object-fit: cover !important;
        object-position: center top !important;
        display: block !important;
    }
    [data-testid="stVerticalBlock"]:has(.deck-hero-browse) [data-testid="stColumn"] {
        padding: 0 !important;
    }
    [data-testid="stVerticalBlock"]:has(.deck-hero-browse) [data-testid="stColumn"] [data-testid="stVerticalBlock"] {
        gap: 2px !important;
    }
    /* Centered, obvious select button below the image */
    [data-testid="stVerticalBlock"]:has(.deck-hero-browse) [data-testid="stColumn"] .stButton {
        margin: 2px 0 0 0 !important;
        padding: 0 !important;
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
    }
    [data-testid="stVerticalBlock"]:has(.deck-hero-browse) [data-testid="stColumn"] .stButton > button {
        width: 100% !important;
        background: #2471a3 !important;
        color: #fff !important;
        border: 2px solid #222 !important;
        border-bottom: 3px solid #222 !important;
        border-radius: 4px !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        padding: 4px 0 !important;
        margin: 0 !important;
        text-align: center !important;
        line-height: 1.1 !important;
        white-space: nowrap !important;
        box-shadow: 1px 1px 0 rgba(0,0,0,0.4) !important;
    }
    [data-testid="stVerticalBlock"]:has(.deck-hero-browse) [data-testid="stColumn"] .stButton > button:hover {
        background: #1a5276 !important;
        border-color: #fff !important;
    }
    /* Highlight currently-selected hero with primary button styling */
    [data-testid="stVerticalBlock"]:has(.deck-hero-browse) [data-testid="stColumn"] .stButton > button[kind="primary"] {
        background: #ed1c24 !important;
        border-color: #fff !important;
    }
    [data-testid="stVerticalBlock"]:has(.deck-hero-browse) [data-testid="stHorizontalBlock"] {
        gap: 6px !important;
        margin-bottom: 8px !important;
    }
    [data-testid="stVerticalBlock"]:has(.deck-hero-browse) [data-testid="stCaptionContainer"] {
        text-align: center;
        font-size: 11px !important;
        margin: 2px 0 4px 0 !important;
        padding: 0 !important;
    }
</style>
""", unsafe_allow_html=True)


# ─── API helpers ───

@st.cache_data(ttl=3600, show_spinner="Loading card database...")
def fetch_all_cards():
    """Fetch the full card database from MarvelCDB and index by code."""
    resp = requests.get("https://marvelcdb.com/api/public/cards/", timeout=30)
    resp.raise_for_status()
    cards = resp.json()
    return {card["code"]: card for card in cards}


@st.cache_data(ttl=300, show_spinner="Loading deck...")
def fetch_deck(deck_id, api_type):
    """Fetch a single deck or decklist from MarvelCDB.

    Short TTL (5 min) so authors who update their decks on MarvelCDB don't
    have to wait for a server reboot to see the latest version.
    """
    if api_type == "decklist":
        url = f"https://marvelcdb.com/api/public/decklist/{deck_id}"
    else:
        url = f"https://marvelcdb.com/api/public/deck/{deck_id}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ─── Community tier helper ──────────────────────────────────────────────────
_TIER_PTS_DECK = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1}


@st.cache_data(ttl=600, show_spinner=False)
def _community_hero_avg():
    """Return {hero: avg_tier_pts} from the community Hero Power tier list."""
    try:
        data, _ = load_json("community_tier_lists.json", default={})
    except Exception:
        return {}
    subs = (data.get("hero_power", {}) or {}).get("submissions", []) or []
    if len(subs) < 2:
        return {}
    pts = {}
    for s in subs:
        for t, hl in (s or {}).items():
            p = _TIER_PTS_DECK.get(t)
            if p is None:
                continue
            for h in (hl or []):
                pts.setdefault(h, []).append(p)
    return {h: float(np.mean(v)) for h, v in pts.items() if v}


def _community_tier_for(hero_name):
    """Return ('S' | 'A' | ... | None, avg_score | None) for a hero."""
    avg_map = _community_hero_avg()
    if hero_name not in avg_map:
        return None, None
    avg = avg_map[hero_name]
    tier = min(_TIER_PTS_DECK.keys(), key=lambda t: abs(_TIER_PTS_DECK[t] - avg))
    return tier, avg


# ─── Display helpers ───

ASPECT_COLORS = {
    "aggression": "aggression",
    "justice": "justice",
    "leadership": "leadership",
    "protection": "protection",
    "basic": "basic",
    "hero": "hero",
    "encounter": "basic",
    "campaign": "basic",
    "pool": "pool",
}

ASPECT_DISPLAY = {
    "aggression": "Aggression",
    "justice": "Justice",
    "leadership": "Leadership",
    "protection": "Protection",
    "basic": "Basic",
    "pool": "'Pool",
}

TYPE_ORDER = ["ally", "support", "upgrade", "event", "resource", "player_side_scheme"]
TYPE_LABELS = {
    "ally": "Allies",
    "event": "Events",
    "support": "Supports",
    "upgrade": "Upgrades",
    "resource": "Resources",
    "player_side_scheme": "Side Schemes",
}


def get_aspect_from_meta(meta_str):
    """Parse the aspect from the deck's meta JSON string."""
    if not meta_str:
        return "basic"
    try:
        meta = json.loads(meta_str)
        return meta.get("aspect", "basic")
    except (json.JSONDecodeError, TypeError):
        return "basic"


def fix_description_links(md_text):
    """Rewrite MarvelCDB relative card links to absolute URLs."""
    if not md_text:
        return ""
    return re.sub(r'\]\(/card/', '](https://marvelcdb.com/card/', md_text)


def card_image_url(card):
    """Get the full image URL for a card."""
    imagesrc = card.get("imagesrc", "")
    if imagesrc:
        return f"https://marvelcdb.com{imagesrc}"
    return ""


def inject_hero_art_background(deck_data, card_db):
    """Show the hero card on the left and alter-ego on the right as fixed thumbnails."""
    hero_code = deck_data.get("hero_code", "")
    hero_card = card_db.get(hero_code)
    if not hero_card:
        return
    hero_url = card_image_url(hero_card)
    if not hero_url:
        return
    hero_name = html_escape(hero_card.get("name", ""))
    hero_link = f"https://marvelcdb.com/card/{hero_code}"

    # Alter-ego is typically the 'b' variant of the hero code
    alter_code = hero_code[:-1] + "b" if hero_code.endswith("a") else ""
    alter_card = card_db.get(alter_code) if alter_code else None
    alter_url = card_image_url(alter_card) if alter_card else ""
    alter_name = html_escape(alter_card.get("name", "")) if alter_card else ""
    alter_link = f"https://marvelcdb.com/card/{alter_code}" if alter_card else ""

    alter_html = ""
    if alter_url:
        alter_html = (
            f'<a href="{alter_link}" target="_blank" class="card-float card-float-right" title="{alter_name}">'
            f'<img src="{alter_url}" alt="{alter_name}">'
            f'</a>'
        )

    st.markdown(
        f"""<style>
.card-float {{
    position: fixed;
    bottom: 20px;
    z-index: 999;
    transition: left 0.3s ease, transform 0.3s ease, box-shadow 0.3s ease;
}}
.card-float-left {{
    left: 20px;
    transform-origin: bottom left;
}}
.stApp:has([data-testid="stSidebar"][aria-expanded="true"]) .card-float-left {{
    left: 340px;
}}
.card-float-right {{
    right: 20px;
    transform-origin: bottom right;
}}
.card-float img {{
    width: 160px;
    border-radius: 10px;
    border: 2px solid rgba(255,255,255,0.6);
    box-shadow: 0 6px 25px rgba(0,0,0,0.6), 0 0 8px rgba(255,255,255,0.15);
    display: block;
    transition: border 0.3s ease, box-shadow 0.3s ease;
}}
.card-float:hover {{
    transform: scale(1.6);
}}
.card-float:hover img {{
    border-color: rgba(255,255,255,0.9);
    box-shadow: 0 0 15px rgba(255,255,255,0.5), 0 0 30px rgba(255,255,255,0.2), 0 12px 40px rgba(0,0,0,0.8);
}}
@media (max-width: 1200px) {{
    .card-float {{
        display: none;
    }}
}}
</style>
<a href="{hero_link}" target="_blank" class="card-float card-float-left" title="{hero_name}">
<img src="{hero_url}" alt="{hero_name}">
</a>
{alter_html}""",
        unsafe_allow_html=True,
    )


def build_card_row(card, qty, show_aspect_dot=False):
    """Build HTML for a compact card row with hover image tooltip."""
    img_url = card_image_url(card)
    name = html_escape(card.get("name", "Unknown"))
    code = card.get("code", "")
    cost = card.get("cost")
    cost_str = f"({cost})" if cost is not None else ""
    card_url = f"https://marvelcdb.com/card/{code}"
    faction = card.get("faction_code", "basic")
    dot_class = ASPECT_COLORS.get(faction, "basic")

    tooltip_img = f'<img class="card-tooltip-img" src="{html_escape(img_url)}" alt="{name}" loading="lazy">' if img_url else ''
    dot_html = f'<span class="aspect-dot dot-{dot_class}" title="{ASPECT_DISPLAY.get(faction, faction.title())}"></span>' if show_aspect_dot else ''

    return f"""<div class="card-row">
        {dot_html}<span class="card-qty">{qty}×</span>
        <span class="card-name"><span class="card-hover-wrap"><a href="{card_url}" target="_blank">{name}</a>{tooltip_img}</span></span>
        <span class="card-cost">{cost_str}</span>
    </div>
    """


def section_weight(cards_with_qty, include_header=False):
    """Estimate a section's vertical weight for balanced two-column rendering."""
    type_groups = {card.get("type_code", "unknown") for card, _ in cards_with_qty}
    return len(cards_with_qty) + len(type_groups) + (1 if include_header else 0)


def render_section_grid_html(section_blocks):
    """Render weighted HTML blocks into a stable two-column grid."""
    if not section_blocks:
        return ""

    columns = [[], []]
    weights = [0, 0]

    for html_block, weight in section_blocks:
        column_idx = 0 if weights[0] <= weights[1] else 1
        columns[column_idx].append(html_block)
        weights[column_idx] += weight

    return (
        '<div class="deck-section-grid">'
        f'<div class="deck-section-column">{"".join(columns[0])}</div>'
        f'<div class="deck-section-column">{"".join(columns[1])}</div>'
        '</div>'
    )


def build_section_block(cards_with_qty, section_class, header_html="", show_aspect_dot=False):
    """Build one deck-list section for the two-column grid."""
    return (
        '<div class="faction-section">'
        f'{header_html}'
        f'{render_card_section_html(cards_with_qty, section_class, show_aspect_dot=show_aspect_dot)}'
        '</div>'
    )


def render_card_section_html(cards_with_qty, section_class, show_aspect_dot=False):
    """Build HTML for a group of cards, grouped by type. Returns HTML string."""
    html_parts = []
    by_type = {}
    for card, qty in cards_with_qty:
        tc = card.get("type_code", "unknown")
        by_type.setdefault(tc, []).append((card, qty))

    for type_code in TYPE_ORDER:
        if type_code not in by_type:
            continue
        group = by_type[type_code]
        label = TYPE_LABELS.get(type_code, type_code.replace("_", " ").title())
        total = sum(q for _, q in group)
        html_parts.append(f'<div class="card-type-header type-{section_class}">{label} ({total})</div>')
        group.sort(key=lambda x: x[0].get("name", ""))
        html_parts.extend(build_card_row(c, q, show_aspect_dot=show_aspect_dot) for c, q in group)

    for type_code, group in by_type.items():
        if type_code in TYPE_ORDER:
            continue
        label = type_code.replace("_", " ").title()
        total = sum(q for _, q in group)
        html_parts.append(f'<div class="card-type-header type-{section_class}">{label} ({total})</div>')
        group.sort(key=lambda x: x[0].get("name", ""))
        html_parts.extend(build_card_row(c, q, show_aspect_dot=show_aspect_dot) for c, q in group)

    return "".join(html_parts)


def render_sorted_cards_html(cards_with_qty, sort_mode, show_aspect_dot=False, prepend_blocks=None):
    """Build HTML for cards sorted/grouped by the chosen mode. Returns HTML string."""
    section_blocks = list(prepend_blocks) if prepend_blocks else []

    if sort_mode == "name":
        sorted_cards = sorted(cards_with_qty, key=lambda x: x[0].get("name", "").lower())
        midpoint = (len(sorted_cards) + 1) // 2
        for chunk in (sorted_cards[:midpoint], sorted_cards[midpoint:]):
            if not chunk:
                continue
            section_blocks.append((
                '<div class="faction-section">'
                f'{"".join(build_card_row(c, q, show_aspect_dot=show_aspect_dot) for c, q in chunk)}'
                '</div>',
                len(chunk),
            ))

    elif sort_mode == "cost":
        by_cost = {}
        for card, qty in cards_with_qty:
            cost = card.get("cost")
            cost_key = cost if cost is not None else -1
            by_cost.setdefault(cost_key, []).append((card, qty))
        for cost_key in sorted(by_cost.keys()):
            group = by_cost[cost_key]
            group.sort(key=lambda x: x[0].get("name", "").lower())
            total = sum(q for _, q in group)
            label = f"Cost {cost_key}" if cost_key >= 0 else "No Cost"
            header_html = f'<div class="faction-header type-basic">{label} ({total})</div>'
            section_blocks.append((
                build_section_block(group, "basic", header_html=header_html, show_aspect_dot=show_aspect_dot),
                section_weight(group, include_header=True),
            ))

    elif sort_mode == "aspect":
        by_faction = {}
        for card, qty in cards_with_qty:
            f = card.get("faction_code", "basic")
            by_faction.setdefault(f, []).append((card, qty))
        for faction in sorted(by_faction.keys()):
            group = by_faction[faction]
            group.sort(key=lambda x: x[0].get("name", "").lower())
            total = sum(q for _, q in group)
            css_f = ASPECT_COLORS.get(faction, "basic")
            label_f = ASPECT_DISPLAY.get(faction, faction.title())
            header_html = f'<div class="faction-header type-{css_f}">{label_f} ({total})</div>'
            section_blocks.append((
                build_section_block(group, css_f, header_html=header_html, show_aspect_dot=show_aspect_dot),
                section_weight(group, include_header=True),
            ))

    elif sort_mode == "set":
        by_set = {}
        for card, qty in cards_with_qty:
            pack = card.get("pack_name", "Unknown")
            by_set.setdefault(pack, []).append((card, qty))
        for pack in sorted(by_set.keys()):
            group = by_set[pack]
            group.sort(key=lambda x: x[0].get("name", "").lower())
            total = sum(q for _, q in group)
            header_html = f'<div class="faction-header type-basic">{html_escape(pack)} ({total})</div>'
            section_blocks.append((
                build_section_block(group, "basic", header_html=header_html, show_aspect_dot=show_aspect_dot),
                section_weight(group, include_header=True),
            ))

    return render_section_grid_html(section_blocks)


def render_deck(deck_data, card_db, show_header=True):
    """Render a full deck display with flowing two-column layout."""
    deck_name = html_escape(deck_data.get("name", "Unnamed Deck"))
    aspect = get_aspect_from_meta(deck_data.get("meta"))
    description = fix_description_links(deck_data.get("description_md", ""))
    deck_url = deck_data.get("url", "")
    slots = deck_data.get("slots", {})

    # Parse aspect
    aspect_class = ASPECT_COLORS.get(aspect, "basic")
    aspect_label = ASPECT_DISPLAY.get(aspect, aspect.title() if aspect else "Basic")

    # Build card lists
    hero_cards = []
    aspect_cards = []
    unknown_codes = []

    for code, qty in slots.items():
        card = card_db.get(code)
        if card is None:
            unknown_codes.append(code)
            continue
        faction = card.get("faction_code", "basic")
        if faction == "hero":
            hero_cards.append((card, qty))
        else:
            aspect_cards.append((card, qty))

    # Merge duplicate printings (same card name) into a single row with summed qty
    def _merge_by_name(cards_with_qty):
        merged = {}
        order = []
        for card, qty in cards_with_qty:
            key = card.get("name", "")
            if key in merged:
                existing_card, existing_qty = merged[key]
                # Prefer a printing that has an image so the hover preview works
                if not existing_card.get("imagesrc") and card.get("imagesrc"):
                    existing_card = card
                merged[key] = (existing_card, existing_qty + qty)
            else:
                merged[key] = (card, qty)
                order.append(key)
        return [merged[k] for k in order]

    hero_cards = _merge_by_name(hero_cards)
    aspect_cards = _merge_by_name(aspect_cards)

    total_cards = sum(slots.values())
    hero_count = sum(q for _, q in hero_cards)
    aspect_count = sum(q for _, q in aspect_cards)

    # ── Deck title + aspect badge + stats + link + view cards ──
    if show_header:
        link_html = f' &nbsp; <a class="mcdb-link" href="{deck_url}" target="_blank">MarvelCDB ↗</a>' if deck_url else ""
        # Community tier badge
        hero_code_h = deck_data.get("hero_code", "")
        hero_card_h = card_db.get(hero_code_h, {}) if hero_code_h else {}
        hero_display_name = hero_card_h.get("name") or st.session_state.get("deck_hero", "")
        comm_tier, comm_avg = _community_tier_for(hero_display_name)
        tier_badge_html = ""
        if comm_tier:
            tier_color = {"S": "#e74c3c", "A": "#e67e22", "B": "#f1c40f",
                          "C": "#2ecc71", "D": "#3498db", "F": "#95a5a6"}.get(comm_tier, "#95a5a6")
            tier_badge_html = (
                f'<span class="aspect-badge" style="background:{tier_color};" '
                f'title="Community Hero Power avg {comm_avg:.2f}/6">'
                f'Community Tier {comm_tier}</span>'
            )
        st.markdown(
            f'<div class="deck-title">{deck_name}'
            f'<span class="aspect-badge aspect-{aspect_class}">{aspect_label}</span>'
            f'{tier_badge_html}'
            f'</div>'
            f'<div class="deck-stats">'
            f'<div class="deck-stat"><strong>{total_cards}</strong> cards</div>'
            f'<div class="deck-stat"><strong>{aspect_count}</strong> aspect/basic</div>'
            f'{link_html}</div>',
            unsafe_allow_html=True
        )

    # ── Sort selector ──
    deck_id = deck_data.get("id", "unknown")
    sort_col, combine_col, view_col = st.columns([3, 1, 1])
    with sort_col:
        sort_choice = st.radio(
            "Sort by",
            ["Type", "Name", "Cost", "Set"],
            index=0,
            horizontal=True,
            key=f"deck_sort_{deck_id}",
        )
    sort_mode = sort_choice.lower() if sort_choice != "Type" else "default"
    with combine_col:
        combine_aspects = st.checkbox("Combine aspects", value=False, key=f"deck_combine_{deck_id}")
    with view_col:
        st.write("")
        hero_code_btn = deck_data.get("hero_code", "")
        hero_card_btn = card_db.get(hero_code_btn, {}) if hero_code_btn else {}
        hero_name_btn = hero_card_btn.get("name") or st.session_state.get("deck_hero", "")
        if hero_name_btn and st.button("View Hero Cards", key=f"view_hero_cards_{deck_id}"):
            open_hero_cards_dialog(hero_name_btn, HERO_ALTER_EGOS.get(hero_name_btn, ""))

    # ── Hero block (always pinned to top-left of the card grid) ──
    hero_prepend_blocks = []
    if hero_cards:
        hero_header_html = f'<div class="faction-header type-hero">Hero Cards ({hero_count})</div>'
        hero_prepend_blocks.append((
            build_section_block(hero_cards, "hero", header_html=hero_header_html),
            section_weight(hero_cards, include_header=True),
        ))

    # ── Card display ──
    if aspect_cards or hero_prepend_blocks:
        if sort_mode == "default" and not combine_aspects:
            # Balanced two-column card layout grouped by aspect then type
            cards_by_faction = {}
            for card, qty in aspect_cards:
                f = card.get("faction_code", "basic")
                cards_by_faction.setdefault(f, []).append((card, qty))

            factions = sorted(cards_by_faction.keys())
            section_blocks = list(hero_prepend_blocks)

            for faction in factions:
                cards_f = cards_by_faction[faction]
                css_f = ASPECT_COLORS.get(faction, "basic")
                label_f = ASPECT_DISPLAY.get(faction, faction.title())
                include_header = len(factions) > 1
                header_html = ""
                if include_header:
                    header_html = f'<div class="faction-header type-{css_f}">{label_f} ({sum(q for _, q in cards_f)})</div>'
                section_blocks.append((
                    build_section_block(cards_f, css_f, header_html=header_html),
                    section_weight(cards_f, include_header=include_header),
                ))

            st.markdown(render_section_grid_html(section_blocks), unsafe_allow_html=True)
        elif sort_mode == "default" and combine_aspects:
            # Combined: all aspect/basic cards grouped by type only
            css_combined = ASPECT_COLORS.get(aspect, "basic")
            combined_blocks = list(hero_prepend_blocks)
            if aspect_cards:
                combined_blocks.append((
                    build_section_block(aspect_cards, css_combined, show_aspect_dot=True),
                    section_weight(aspect_cards),
                ))
            st.markdown(render_section_grid_html(combined_blocks), unsafe_allow_html=True)
        else:
            st.markdown(
                render_sorted_cards_html(
                    aspect_cards, sort_mode,
                    show_aspect_dot=combine_aspects,
                    prepend_blocks=hero_prepend_blocks,
                ),
                unsafe_allow_html=True,
            )

    # ── Description (below the deck card grid) ──
    if show_header and description.strip():
        with st.expander("Deck Description"):
            st.markdown(description)

    # ── Obligation & Nemesis Set (inline, like aspect cards) ──
    hero_code = deck_data.get("hero_code", "")
    if hero_code:
        obligation_cards, nemesis_cards = get_obligation_nemesis(hero_code, card_db)
        if obligation_cards or nemesis_cards:
            total_enc = (sum(c.get("quantity", 1) for c in obligation_cards)
                         + sum(c.get("quantity", 1) for c in nemesis_cards))
            html_parts = [f'<div class="faction-header type-hero">Obligation &amp; Nemesis ({total_enc})</div>']
            if obligation_cards:
                html_parts.append('<div class="card-type-header type-hero">Obligation</div>')
                for c in obligation_cards:
                    html_parts.append(build_card_row(c, c.get("quantity", 1)))
            if nemesis_cards:
                html_parts.append('<div class="card-type-header type-hero">Nemesis Set</div>')
                for c in nemesis_cards:
                    html_parts.append(build_card_row(c, c.get("quantity", 1)))
            st.markdown("".join(html_parts), unsafe_allow_html=True)

    if unknown_codes:
        with st.expander(f"{len(unknown_codes)} card(s) not found in database"):
            st.code(", ".join(unknown_codes))


# ─── Main Page ───

render_page_header("A GOOD Deck For Every Hero", "Browse Daring Lime's Deck Lists For Every Hero")

# ── Hero selector (compact top bar) ──
_SORT_OPTIONS = ["Alphabetical (A→Z)", "Oldest → Newest", "Newest → Oldest"]
if "_decks_sort_val" not in st.session_state:
    st.session_state._decks_sort_val = "Alphabetical (A→Z)"

hero_names = sorted(hero_decks.keys())

# Sort + wave filter
_sort_val = st.session_state.get("_decks_sort_val", "Alphabetical (A→Z)")
_sort_idx = _SORT_OPTIONS.index(_sort_val) if _sort_val in _SORT_OPTIONS else 0
sort_col, wave_col, _ = st.columns([1, 1, 2])
with sort_col:
    decks_sort_order = st.selectbox(
        "Sort order",
        _SORT_OPTIONS,
        index=_sort_idx,
        key="decks_sort_order",
    )
    st.session_state._decks_sort_val = decks_sort_order
with wave_col:
    decks_wave_filter = st.multiselect(
        "Filter by waves",
        WAVE_ORDER,
        key="decks_wave_filter",
        placeholder="All Waves",
    )
if decks_wave_filter:
    hero_names = [h for h in hero_names if HERO_WAVE.get(h) in decks_wave_filter]

if decks_sort_order == "Oldest → Newest":
    hero_names.sort(key=lambda h: HERO_RELEASE_INDEX.get(h, 9999))
elif decks_sort_order == "Newest → Oldest":
    hero_names.sort(key=lambda h: HERO_RELEASE_INDEX.get(h, 0), reverse=True)

if not hero_names:
    st.info("No heroes match the selected wave.")
    st.stop()

# Handle ?hero=<HeroName> from clickable grid
_qp_hero = st.query_params.get("hero")
if isinstance(_qp_hero, list):
    _qp_hero = _qp_hero[0] if _qp_hero else None
if _qp_hero and _qp_hero in hero_names:
    st.session_state.deck_hero = _qp_hero
    try:
        del st.query_params["hero"]
    except Exception:
        pass

if "deck_hero" not in st.session_state:
    st.session_state.deck_hero = hero_names[random.randint(0, len(hero_names) - 1)]
elif st.session_state.deck_hero not in hero_names:
    st.session_state.deck_hero = hero_names[0]

selected_hero = st.session_state.deck_hero


@st.cache_data(show_spinner=False)
def _deck_build_uri_map(_urls):
    out = {}
    for hero, path in _urls.items():
        if not path:
            continue
        if path.startswith("http://") or path.startswith("https://"):
            out[hero] = path
            continue
        if not os.path.exists(path):
            continue
        ext = os.path.splitext(path)[1].lower().lstrip(".")
        mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png",
                "gif": "gif", "webp": "webp"}.get(ext, "jpeg")
        with open(path, "rb") as f:
            out[hero] = f"data:image/{mime};base64,{base64.b64encode(f.read()).decode()}"
    return out


_DECK_URI_MAP = _deck_build_uri_map(dict(hero_image_urls))

# ── Search box + refresh button ──
search_col, refresh_col = st.columns([3, 1])
with search_col:
    _hero_search = st.text_input(
        "Search hero",
        key="_deck_hero_search",
        placeholder="🔍 Search hero by name…",
        label_visibility="collapsed",
    )
with refresh_col:
    if st.button(
        "🔄 Refresh deck data",
        key="_deck_refresh_btn",
        help="Re-fetch decks and cards from MarvelCDB so updates appear without restarting the site.",
        width="stretch",
    ):
        fetch_deck.clear()
        fetch_all_cards.clear()
        st.toast("✅ Deck data refreshed from MarvelCDB.")
        st.rerun()

# Apply search filter to the visible grid (selected hero remains valid)
filtered_names = hero_names
if _hero_search:
    _q = _hero_search.strip().lower()
    filtered_names = [h for h in hero_names if _q in h.lower()]
    if not filtered_names:
        st.info(f"No heroes match '{_hero_search}'.")
        filtered_names = hero_names

# ── Hero image grid (always visible, cropped, clickable) ──
st.markdown(
    """<style>
    .dhg-wrap {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
        gap: 8px;
        width: 100%;
        margin-bottom: 8px;
    }
    .dhg-card {
        position: relative;
        display: block;
        text-decoration: none !important;
        color: inherit !important;
        border-radius: 7px;
        overflow: hidden;
        background: rgba(0,0,0,0.4);
        border: 2px solid rgba(255,255,255,0.08);
        transition: transform 0.12s ease, border-color 0.12s ease, box-shadow 0.12s ease;
    }
    .dhg-card:hover {
        transform: translateY(-2px);
        border-color: #2471a3;
        box-shadow: 0 6px 16px rgba(36,113,163,0.4);
    }
    .dhg-card.selected {
        border-color: #2471a3;
        box-shadow: 0 0 0 2px #2471a3, 0 6px 16px rgba(36,113,163,0.5);
    }
    .dhg-imgwrap {
        width: 100%;
        aspect-ratio: 1.3;
        background-color: #111;
        background-size: 135% auto;
        background-position: center 16%;
        background-repeat: no-repeat;
        display: block;
    }
    .dhg-name {
        text-align: center;
        font-size: 11px;
        font-weight: 700;
        color: #f0f0f0;
        padding: 3px 3px 5px;
        line-height: 1.15;
        background: rgba(0,0,0,0.55);
    }
    .dhg-card.selected .dhg-name {
        background: #2471a3;
        color: #fff;
    }
    .dhg-badge {
        position: absolute;
        top: 4px;
        left: 4px;
        background: #2471a3;
        color: #fff;
        font-size: 10px;
        font-weight: 800;
        padding: 2px 6px;
        border-radius: 3px;
        box-shadow: 1px 1px 0 rgba(0,0,0,0.5);
    }
    </style>""",
    unsafe_allow_html=True,
)

cards_html = ['<div class="dhg-wrap">']
for hero in filtered_names:
    uri = _DECK_URI_MAP.get(hero)
    if not uri:
        continue
    href = f"?hero={quote(hero)}"
    safe_name = html_escape(hero)
    is_sel = hero == selected_hero
    cls = "dhg-card selected" if is_sel else "dhg-card"
    badge = '<div class="dhg-badge">✓</div>' if is_sel else ""
    cards_html.append(
        f'<a class="{cls}" href="{href}" target="_self" title="View decks for {safe_name}">'
        f'{badge}'
        f'<div class="dhg-imgwrap" style="background-image:url({uri});"></div>'
        f'<div class="dhg-name">{safe_name}</div>'
        f'</a>'
    )
cards_html.append("</div>")

_exp_label = f"🦸 Choose hero — currently: {selected_hero}"
with st.expander(_exp_label, expanded=True):
    st.markdown("".join(cards_html), unsafe_allow_html=True)

st.markdown("---")

# ── Deck display ──
if selected_hero:
    decks_for_hero = hero_decks.get(selected_hero, [])

    if not decks_for_hero:
        st.warning(f"No deck list found for {selected_hero}.")
    else:
        # Load card database
        try:
            card_db = fetch_all_cards()
        except requests.RequestException as e:
            st.error(f"Failed to load card database from MarvelCDB: {e}")
            st.stop()

        if len(decks_for_hero) == 1:
            entry = decks_for_hero[0]
            try:
                deck_data = fetch_deck(entry["deck_id"], entry["api_type"])
                if not deck_data.get("url"):
                    deck_data["url"] = entry["url"]
                inject_hero_art_background(deck_data, card_db)
                render_deck(deck_data, card_db)
            except requests.RequestException as e:
                st.error(f"Failed to load deck from MarvelCDB: {e}")
        else:
            loaded_decks = []
            load_errors = []
            for entry in decks_for_hero:
                try:
                    deck_data = fetch_deck(entry["deck_id"], entry["api_type"])
                    if not deck_data.get("url"):
                        deck_data["url"] = entry["url"]
                    loaded_decks.append((entry, deck_data))
                except requests.RequestException as e:
                    load_errors.append((entry, e))

            if loaded_decks:
                inject_hero_art_background(loaded_decks[0][1], card_db)
                st.markdown(
                    f'<div class="deck-summary-note">{len(loaded_decks)} deck lists available. Pick a tab below.</div>',
                    unsafe_allow_html=True
                )
                tab_labels = [entry.get("name", f"Deck {i+1}") for i, (entry, _) in enumerate(loaded_decks)]
                tabs = st.tabs(tab_labels)
                for tab, (_, deck_data) in zip(tabs, loaded_decks):
                    with tab:
                        render_deck(deck_data, card_db)

            for entry, error in load_errors:
                entry_name = entry.get("name") or entry.get("deck_id", "deck")
                st.error(f"Failed to load {entry_name} from MarvelCDB: {error}")

# ── MarvelCDB Credit ──
st.markdown("---")

# ── Quick deck import by URL (secondary feature) ──
with st.expander("📋 Import any deck by URL"):
    deck_url_input = st.text_input(
        "Paste a MarvelCDB deck or decklist URL",
        placeholder="https://marvelcdb.com/decklist/view/12345/my-deck-1.0",
        key="deck_url_import",
    )
    if deck_url_input:
        _url_match = re.search(r'marvelcdb\.com/(deck(?:list)?)/view/(\d+)', deck_url_input)
        if _url_match:
            _api_type = "decklist" if _url_match.group(1) == "decklist" else "deck"
            _import_id = _url_match.group(2)
            try:
                _card_db = fetch_all_cards()
                _import_deck = fetch_deck(_import_id, _api_type)
                if not _import_deck.get("url"):
                    _import_deck["url"] = deck_url_input
                inject_hero_art_background(_import_deck, _card_db)
                render_deck(_import_deck, _card_db)
            except requests.RequestException as e:
                st.error(f"Failed to load deck: {e}")
        else:
            st.warning("Couldn't parse that URL. Expected format: `https://marvelcdb.com/decklist/view/12345/...` or `https://marvelcdb.com/deck/view/12345/...`")

render_footer()
