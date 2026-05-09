"""
Hero Cards — Click any hero's cropped portrait to view all of their MarvelCDB
cards (identity, alter-ego, signature cards, obligation, and nemesis set).

Implementation note: The hero grid is rendered as pure HTML with anchor links
that set a `?cards=<name>` query param. We catch that param at the top of the
page and open the dialog. This avoids fragile CSS overrides on Streamlit
buttons and gives a predictable, fully-cropped, very-clickable grid.
"""

import os
import base64
from urllib.parse import quote
from html import escape as html_escape

import streamlit as st
from data.hero_image_urls import hero_image_urls
from data.constants import HERO_ALTER_EGOS
from data.hero_release_order import HERO_RELEASE_INDEX, HERO_WAVE, WAVE_ORDER, HERO_LEGACY
from components.nav_banner import render_nav_banner, render_page_header, render_footer
from components.hero_card_viewer import open_hero_cards_dialog

render_nav_banner("hero-cards")

render_page_header(
    "Hero Cards",
    "Click any hero to view their identity, alter-ego, signature cards, obligation, and nemesis set.",
)


# ─── Convert local image paths to data URIs so they render inside our HTML ───
@st.cache_data(show_spinner=False)
def _build_uri_map(_urls):
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


_URI_MAP = _build_uri_map(dict(hero_image_urls))


# ─── Catch ?cards=<HeroName> and open the dialog ───
_qp_cards = st.query_params.get("cards")
if isinstance(_qp_cards, list):
    _qp_cards = _qp_cards[0] if _qp_cards else None
if _qp_cards:
    # Clear the param so reloads don't re-trigger the dialog
    try:
        del st.query_params["cards"]
    except Exception:
        pass
    if _qp_cards in hero_image_urls:
        open_hero_cards_dialog(_qp_cards, HERO_ALTER_EGOS.get(_qp_cards, ""))


# ─── Filters ───
_SORT_OPTIONS = ["Alphabetical (A→Z)", "Oldest → Newest", "Newest → Oldest"]
_sort_val = st.session_state.get("_hero_cards_sort_val", "Alphabetical (A→Z)")
_sort_idx = _SORT_OPTIONS.index(_sort_val) if _sort_val in _SORT_OPTIONS else 0

sort_col, fmt_col, wave_col, search_col = st.columns([1, 1, 1.2, 1.5])
with sort_col:
    sort_order = st.selectbox(
        "Sort order", _SORT_OPTIONS, index=_sort_idx, key="hero_cards_sort_order"
    )
    st.session_state._hero_cards_sort_val = sort_order
with fmt_col:
    fmt_filter = st.selectbox("Format", ["Current", "Legacy"], index=1, key="hero_cards_fmt")
with wave_col:
    if fmt_filter == "Legacy":
        wave_filter = st.multiselect(
            "Filter by waves", WAVE_ORDER, key="hero_cards_wave", placeholder="All Waves"
        )
    else:
        wave_filter = []
with search_col:
    search_q = st.text_input("Search", key="hero_cards_search", placeholder="🔍 Search hero name…")

hero_names = sorted(hero_image_urls.keys())
if fmt_filter == "Current":
    hero_names = [h for h in hero_names if not HERO_LEGACY.get(h, False)]
if wave_filter:
    hero_names = [h for h in hero_names if HERO_WAVE.get(h) in wave_filter]
if search_q:
    _q = search_q.strip().lower()
    hero_names = [h for h in hero_names if _q in h.lower()]

if sort_order == "Oldest → Newest":
    hero_names.sort(key=lambda h: HERO_RELEASE_INDEX.get(h, 9999))
elif sort_order == "Newest → Oldest":
    hero_names.sort(key=lambda h: HERO_RELEASE_INDEX.get(h, 0), reverse=True)

st.markdown("---")

if not hero_names:
    st.info("No heroes match the current filters.")
else:
    # ─── Pure-HTML grid: cropped, clickable hero portraits ───
    cards_html = ['<div class="hcg-wrap">']
    for hero in hero_names:
        uri = _URI_MAP.get(hero)
        if not uri:
            continue
        href = f"?cards={quote(hero)}"
        safe_name = html_escape(hero)
        cards_html.append(
            f'<a class="hcg-card" href="{href}" target="_self" title="View {safe_name} cards">'
            f'<div class="hcg-imgwrap" style="background-image:url({uri});"></div>'
            f'<div class="hcg-name">{safe_name}</div>'
            f'<div class="hcg-overlay"><span>View Cards</span></div>'
            f'</a>'
        )
    cards_html.append("</div>")

    st.markdown(
        """<style>
        .hcg-wrap {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 10px;
            width: 100%;
        }
        .hcg-card {
            position: relative;
            display: block;
            text-decoration: none !important;
            color: inherit !important;
            border-radius: 8px;
            overflow: hidden;
            background: rgba(0,0,0,0.4);
            border: 2px solid rgba(255,255,255,0.08);
            transition: transform 0.12s ease, border-color 0.12s ease, box-shadow 0.12s ease;
        }
        .hcg-card:hover {
            transform: translateY(-2px);
            border-color: #ed1c24;
            box-shadow: 0 6px 18px rgba(237,28,36,0.35);
        }
        .hcg-imgwrap {
            width: 100%;
            aspect-ratio: 1.3;
            background-color: #111;
            background-size: 135% auto;
            background-position: center 16%;
            background-repeat: no-repeat;
            display: block;
        }
        .hcg-name {
            text-align: center;
            font-size: 12px;
            font-weight: 700;
            color: #f0f0f0;
            padding: 4px 4px 6px;
            line-height: 1.15;
            background: rgba(0,0,0,0.55);
        }
        .hcg-overlay {
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(0,0,0,0.55);
            opacity: 0;
            transition: opacity 0.12s ease;
            pointer-events: none;
        }
        .hcg-overlay span {
            background: #ed1c24;
            color: #fff;
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: 800;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 2px 2px 0 rgba(0,0,0,0.5);
            border: 2px solid #222;
        }
        .hcg-card:hover .hcg-overlay {
            opacity: 1;
        }
        /* Touch devices: keep overlay subtle but visible */
        @media (hover: none) {
            .hcg-overlay {
                opacity: 1;
                background: rgba(0,0,0,0.0);
                align-items: flex-start;
                justify-content: flex-end;
                padding: 4px;
            }
            .hcg-overlay span {
                font-size: 10px;
                padding: 3px 6px;
            }
        }
        </style>""",
        unsafe_allow_html=True,
    )
    st.markdown("".join(cards_html), unsafe_allow_html=True)

render_footer()
