"""
Deck Lists - Browse MarvelCDB deck lists for every hero
"""

import streamlit as st
import requests
import json
import re
import random
from html import escape as html_escape
from data.hero_decks import hero_decks
from data.hero_image_urls import hero_image_urls
from components.collection_filter import render_collection_filter
from components.nav_banner import render_nav_banner, render_page_header, render_footer
from data.hero_release_order import HERO_WAVE, WAVE_ORDER

render_nav_banner("good-decks")
render_collection_filter()

# ─── Custom CSS ───
st.markdown("""
<style>
    .deck-title {
        font-size: 22px;
        font-weight: bold;
        color: white;
        margin-bottom: 4px;
    }
    .deck-summary-note {
        font-size: 13px;
        color: #d0d0d0;
        margin-bottom: 10px;
        letter-spacing: 0.02em;
    }
    .aspect-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 10px;
        font-size: 12px;
        font-weight: bold;
        color: white;
        margin-left: 6px;
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
    .type-hero { border-color: #95a5a6; background: rgba(149,165,166,0.15); color: #bdc3c7; }
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
        padding: 1px 6px;
        border-radius: 3px;
        margin-bottom: 0px;
        position: relative;
    }
    .card-row:hover {
        background: rgba(255,255,255,0.06);
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
        gap: 12px;
        flex-wrap: wrap;
        margin: 4px 0 8px 0;
    }
    .deck-stat {
        background: rgba(255,255,255,0.05);
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 12px;
        color: #ccc;
    }
    .deck-stat strong {
        color: white;
    }
    .mcdb-link {
        display: inline-block;
        padding: 4px 12px;
        background: #2471a3;
        color: white !important;
        border-radius: 5px;
        text-decoration: none;
        font-size: 12px;
        font-weight: bold;
        margin-top: 2px;
        transition: background 0.2s;
    }
    .mcdb-link:hover {
        background: #1a5276;
        color: white !important;
    }
    .section-divider {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.1);
        margin: 6px 0;
    }
    /* Two-column flowing layout */
    .deck-columns {
        column-count: 2;
        column-gap: 20px;
    }
    .faction-section {
        break-inside: avoid;
        -webkit-column-break-inside: avoid;
        margin-bottom: 4px;
    }

    /* ── Hero browse grid: overlay Select button on hover ── */
    [data-testid="stVerticalBlock"]:has(.deck-hero-browse) [data-testid="stColumn"] {
        position: relative;
        padding: 0 !important;
        overflow: hidden;
    }
    /* The inner vertical block inside each column: no gaps, relative for containment */
    [data-testid="stVerticalBlock"]:has(.deck-hero-browse) [data-testid="stColumn"] > [data-testid="stVerticalBlockBorderWrapper"] {
        position: relative;
    }
    [data-testid="stVerticalBlock"]:has(.deck-hero-browse) [data-testid="stColumn"] > [data-testid="stVerticalBlockBorderWrapper"] > div > [data-testid="stVerticalBlock"] {
        position: relative;
    }
    /* Button container: fill column, sit on top of image */
    [data-testid="stVerticalBlock"]:has(.deck-hero-browse) [data-testid="stColumn"] .stButton {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        z-index: 10;
        opacity: 0;
        transition: opacity 0.2s ease;
        pointer-events: none;
        margin: 0 !important;
        padding: 0 !important;
    }
    [data-testid="stVerticalBlock"]:has(.deck-hero-browse) [data-testid="stColumn"]:hover .stButton {
        opacity: 1;
        pointer-events: auto;
    }
    [data-testid="stVerticalBlock"]:has(.deck-hero-browse) [data-testid="stColumn"] .stButton > button {
        width: 100% !important;
        height: 100% !important;
        background: rgba(0, 0, 0, 0.5) !important;
        color: #fff !important;
        border: 2px solid rgba(255,255,255,0.4) !important;
        border-radius: 8px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    [data-testid="stVerticalBlock"]:has(.deck-hero-browse) [data-testid="stHorizontalBlock"] {
        gap: 4px !important;
        margin-bottom: 2px !important;
    }
    [data-testid="stVerticalBlock"]:has(.deck-hero-browse) [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stVerticalBlock"]:has(.deck-hero-browse) [data-testid="stVerticalBlock"] {
        gap: 0 !important;
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


@st.cache_data(ttl=3600, show_spinner="Loading deck...")
def fetch_deck(deck_id, api_type):
    """Fetch a single deck or decklist from MarvelCDB."""
    if api_type == "decklist":
        url = f"https://marvelcdb.com/api/public/decklist/{deck_id}"
    else:
        url = f"https://marvelcdb.com/api/public/deck/{deck_id}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


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


def render_sorted_cards_html(cards_with_qty, sort_mode, show_aspect_dot=False):
    """Build HTML for cards sorted/grouped by the chosen mode. Returns HTML string."""
    html_parts = ['<div class="deck-columns">']

    if sort_mode == "name":
        sorted_cards = sorted(cards_with_qty, key=lambda x: x[0].get("name", "").lower())
        html_parts.append('<div class="faction-section">')
        html_parts.extend(build_card_row(c, q, show_aspect_dot=show_aspect_dot) for c, q in sorted_cards)
        html_parts.append('</div>')

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
            html_parts.append('<div class="faction-section">')
            html_parts.append(f'<div class="faction-header type-basic">{label} ({total})</div>')
            html_parts.extend(build_card_row(c, q, show_aspect_dot=show_aspect_dot) for c, q in group)
            html_parts.append('</div>')

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
            html_parts.append('<div class="faction-section">')
            html_parts.append(f'<div class="faction-header type-{css_f}">{label_f} ({total})</div>')
            html_parts.extend(build_card_row(c, q, show_aspect_dot=show_aspect_dot) for c, q in group)
            html_parts.append('</div>')

    elif sort_mode == "set":
        by_set = {}
        for card, qty in cards_with_qty:
            pack = card.get("pack_name", "Unknown")
            by_set.setdefault(pack, []).append((card, qty))
        for pack in sorted(by_set.keys()):
            group = by_set[pack]
            group.sort(key=lambda x: x[0].get("name", "").lower())
            total = sum(q for _, q in group)
            html_parts.append('<div class="faction-section">')
            html_parts.append(f'<div class="faction-header type-basic">{html_escape(pack)} ({total})</div>')
            html_parts.extend(build_card_row(c, q, show_aspect_dot=show_aspect_dot) for c, q in group)
            html_parts.append('</div>')

    html_parts.append('</div>')
    return "".join(html_parts)


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

    total_cards = sum(slots.values())
    hero_count = sum(q for _, q in hero_cards)
    aspect_count = sum(q for _, q in aspect_cards)

    # ── Deck title + aspect badge + stats + link ──
    if show_header:
        link_html = f' &nbsp; <a class="mcdb-link" href="{deck_url}" target="_blank">MarvelCDB ↗</a>' if deck_url else ""
        st.markdown(
            f'<div class="deck-title">{deck_name}'
            f'<span class="aspect-badge aspect-{aspect_class}">{aspect_label}</span>'
            f'</div>'
            f'<div class="deck-stats">'
            f'<div class="deck-stat"><strong>{total_cards}</strong> cards</div>'
            f'<div class="deck-stat"><strong>{aspect_count}</strong> aspect/basic</div>'
            f'{link_html}</div>',
            unsafe_allow_html=True
        )

    # ── Sort selector ──
    deck_id = deck_data.get("id", "unknown")
    sort_col, combine_col = st.columns([3, 1])
    with sort_col:
        sort_choice = st.radio(
            "Sort by",
            ["Type", "Name", "Cost", "Aspect", "Set"],
            index=0,
            horizontal=True,
            key=f"deck_sort_{deck_id}",
        )
    sort_mode = sort_choice.lower() if sort_choice != "Type" else "default"
    with combine_col:
        combine_aspects = st.checkbox("Combine aspects", value=False, key=f"deck_combine_{deck_id}")

    # ── Card display ──
    if aspect_cards:
        if sort_mode == "default" and not combine_aspects:
            # Flowing two-column card layout grouped by aspect then type
            cards_by_faction = {}
            for card, qty in aspect_cards:
                f = card.get("faction_code", "basic")
                cards_by_faction.setdefault(f, []).append((card, qty))

            factions = sorted(cards_by_faction.keys())
            html_parts = ['<div class="deck-columns">']

            for faction in factions:
                cards_f = cards_by_faction[faction]
                css_f = ASPECT_COLORS.get(faction, "basic")
                label_f = ASPECT_DISPLAY.get(faction, faction.title())
                html_parts.append('<div class="faction-section">')
                if len(factions) > 1:
                    html_parts.append(f'<div class="faction-header type-{css_f}">{label_f} ({sum(q for _, q in cards_f)})</div>')
                html_parts.append(render_card_section_html(cards_f, css_f))
                html_parts.append('</div>')

            html_parts.append('</div>')
            st.markdown("".join(html_parts), unsafe_allow_html=True)
        elif sort_mode == "default" and combine_aspects:
            # Combined: all aspect/basic cards grouped by type only
            css_combined = ASPECT_COLORS.get(aspect, "basic")
            st.markdown(render_card_section_html(aspect_cards, css_combined, show_aspect_dot=True), unsafe_allow_html=True)
        else:
            st.markdown(render_sorted_cards_html(aspect_cards, sort_mode, show_aspect_dot=combine_aspects), unsafe_allow_html=True)

    # ── Description (between aspect cards and hero cards) ──
    if show_header and description.strip():
        with st.expander("Deck Description"):
            st.markdown(description)

    # ── Hero Cards (collapsed at bottom) ──
    if hero_cards:
        with st.expander(f"Hero Cards ({hero_count})"):
            st.markdown(render_card_section_html(hero_cards, "hero"), unsafe_allow_html=True)

    if unknown_codes:
        with st.expander(f"{len(unknown_codes)} card(s) not found in database"):
            st.code(", ".join(unknown_codes))


# ─── Main Page ───

render_page_header("A GOOD Deck For Every Hero", "Browse recommended MarvelCDB deck lists for every hero")

# ── Hero selector (compact top bar) ──
hero_names = sorted(hero_decks.keys())

# Apply collection filter
owned = st.session_state.get("owned_heroes")
if owned is not None:
    hero_names = [h for h in hero_names if h in owned]

# Wave filter
wave_col, _ = st.columns([1, 2])
with wave_col:
    decks_wave_filter = st.multiselect(
        "Filter by waves",
        WAVE_ORDER,
        key="decks_wave_filter",
        placeholder="All Waves",
    )
if decks_wave_filter:
    hero_names = [h for h in hero_names if HERO_WAVE.get(h) in decks_wave_filter]

if not hero_names:
    st.info("No heroes match the selected wave.")
    st.stop()

if "deck_hero" not in st.session_state:
    st.session_state.deck_hero = hero_names[random.randint(0, len(hero_names) - 1)]

def _on_hero_search_change():
    st.session_state.deck_hero = st.session_state._deck_hero_search

selected_hero = st.session_state.deck_hero
sel_col, _ = st.columns([1, 3])
with sel_col:
    st.selectbox(
        "Hero",
        hero_names,
        index=hero_names.index(selected_hero) if selected_hero in hero_names else 0,
        key="_deck_hero_search",
        on_change=_on_hero_search_change,
    )
selected_hero = st.session_state.deck_hero

with st.expander("Browse all heroes", expanded=False):
    st.markdown('<div class="deck-hero-browse"></div>', unsafe_allow_html=True)
    cols_per_row = 8
    for i in range(0, len(hero_names), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(hero_names):
                break
            hero = hero_names[idx]
            with col:
                if st.button("Select", key=f"hero_btn_{idx}", width="stretch"):
                    st.session_state.deck_hero = hero
                    st.rerun()
                img_path = hero_image_urls.get(hero, "")
                if img_path:
                    st.image(img_path, width="stretch")

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
            st.markdown(
                f'<div class="deck-summary-note">{len(decks_for_hero)} deck lists available. Pick a tab below.</div>',
                unsafe_allow_html=True
            )
            tab_labels = [entry.get("name", f"Deck {i+1}") for i, entry in enumerate(decks_for_hero)]
            tabs = st.tabs(tab_labels)
            bg_injected = False
            for tab, entry in zip(tabs, decks_for_hero):
                with tab:
                    try:
                        deck_data = fetch_deck(entry["deck_id"], entry["api_type"])
                        if not deck_data.get("url"):
                            deck_data["url"] = entry["url"]
                        if not bg_injected:
                            inject_hero_art_background(deck_data, card_db)
                            bg_injected = True
                        render_deck(deck_data, card_db)
                    except requests.RequestException as e:
                        st.error(f"Failed to load deck from MarvelCDB: {e}")

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
