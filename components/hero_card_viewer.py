"""
Hero Card Viewer — Fetches and displays hero cards from MarvelCDB in a dialog popup.
Shows the hero identity card, alter-ego card, and signature cards.
Uses card_set_code to correctly group each hero's signature cards.
"""

import re
import streamlit as st
import requests
from html import escape as html_escape


# ─── API helpers (cached) ───

@st.cache_data(ttl=3600, show_spinner="Loading card database…")
def _fetch_all_cards():
    """Fetch every card from MarvelCDB, indexed by code."""
    resp = requests.get("https://marvelcdb.com/api/public/cards/", timeout=30)
    resp.raise_for_status()
    return {card["code"]: card for card in resp.json()}


def _card_image_url(card):
    src = card.get("imagesrc", "")
    return f"https://marvelcdb.com{src}" if src else ""


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_pack_cards(pack_code):
    """Fetch all cards from a specific pack (includes encounter cards)."""
    resp = requests.get(
        f"https://marvelcdb.com/api/public/cards/{pack_code}", timeout=30
    )
    resp.raise_for_status()
    return {card["code"]: card for card in resp.json()}


def get_obligation_nemesis(hero_code, card_db):
    """Return (obligation_cards, nemesis_cards) for a hero.

    Fetches the hero's pack to find encounter cards not in the bulk API.
    """
    hero_card = card_db.get(hero_code)
    if not hero_card:
        return [], []
    pack_code = hero_card.get("pack_code", "")
    set_code = hero_card.get("card_set_code", "")
    if not pack_code or not set_code:
        return [], []
    try:
        pack_db = fetch_pack_cards(pack_code)
    except Exception:
        return [], []
    obligation = sorted(
        [c for c in pack_db.values()
         if c.get("card_set_code") == set_code
         and c.get("faction_code") == "encounter"],
        key=lambda c: c.get("code", ""),
    )
    nemesis = sorted(
        [c for c in pack_db.values()
         if c.get("card_set_code") == f"{set_code}_nemesis"],
        key=lambda c: c.get("code", ""),
    )
    return obligation, nemesis


def _find_hero_cards(hero_name, card_db, alter_ego_hint=""):
    """Return (hero_card, alter_card, [signature_cards]) for *hero_name*.

    Uses card_set_code to find all signature cards belonging to the hero.
    Uses *alter_ego_hint* (e.g. "T'Challa") to disambiguate heroes that
    share the same MarvelCDB name (e.g. two Black Panthers).
    """
    base_name = re.sub(r"\s*\(.*?\)\s*", "", hero_name).strip()

    # Collect all hero-identity cards whose name matches
    candidates = [
        c for c in card_db.values()
        if c.get("type_code") == "hero"
        and c.get("name", "").lower() == base_name.lower()
    ]
    if not candidates:
        candidates = [
            c for c in card_db.values()
            if c.get("type_code") == "hero"
            and base_name.lower() in c.get("name", "").lower()
        ]
    if not candidates:
        return None, None, []

    # Disambiguate with alter-ego name when there are duplicates
    hero_card = candidates[0]
    if len(candidates) > 1 and alter_ego_hint:
        for c in candidates:
            alter_code = c["code"][:-1] + "b" if c["code"].endswith("a") else ""
            ac = card_db.get(alter_code)
            if ac and ac.get("name", "").lower() == alter_ego_hint.lower():
                hero_card = c
                break

    hero_code = hero_card["code"]
    set_code = hero_card.get("card_set_code", "")

    # Alter-ego is the "b" variant
    alter_code = hero_code[:-1] + "b" if hero_code.endswith("a") else ""
    alter_card = card_db.get(alter_code) if alter_code else None

    # Signature cards: same card_set_code, excluding identity / alter-ego
    skip = {hero_code, alter_code}
    sig_cards = sorted(
        [
            c for c in card_db.values()
            if c.get("card_set_code") == set_code
            and c["code"] not in skip
        ],
        key=lambda c: c.get("code", ""),
    )

    return hero_card, alter_card, sig_cards


# ─── Dialog popup ───

_CARD_IMG_STYLE = "width:100%;border-radius:6px;"


def _render_card_grid(cards, cols_per_row=4, show_qty=True):
    """Render a grid of card images with optional quantity badges."""
    for i in range(0, len(cards), cols_per_row):
        row = cards[i : i + cols_per_row]
        cols = st.columns(cols_per_row)
        for j, card in enumerate(row):
            with cols[j]:
                img_url = _card_image_url(card)
                if img_url:
                    card_link = f"https://marvelcdb.com/card/{card['code']}"
                    st.markdown(
                        f'<a href="{card_link}" target="_blank">'
                        f'<img src="{html_escape(img_url)}" '
                        f'style="{_CARD_IMG_STYLE}" '
                        f'alt="{html_escape(card.get("name",""))}">' 
                        f'</a>',
                        unsafe_allow_html=True,
                    )
                qty = card.get("quantity", 1)
                qty_str = f" ×{qty}" if show_qty and qty > 1 else ""
                st.caption(f"{card.get('name', '')}{qty_str}")


@st.dialog("Hero Cards", width="large")
def _hero_cards_dialog(hero_name, alter_ego_hint=""):
    """Render a dialog showing the hero's MarvelCDB cards."""
    try:
        card_db = _fetch_all_cards()
    except Exception as e:
        st.error(f"Could not load card database: {e}")
        return

    hero_card, alter_card, extra_cards = _find_hero_cards(
        hero_name, card_db, alter_ego_hint
    )

    if not hero_card:
        st.warning(f"Could not find cards for **{hero_name}** in MarvelCDB.")
        return

    st.markdown(
        f"<h3 style='margin:0 0 8px;'>{html_escape(hero_name)}</h3>",
        unsafe_allow_html=True,
    )

    # Hero identity + alter-ego side by side
    id_cols = st.columns(2)
    with id_cols[0]:
        hero_url = _card_image_url(hero_card)
        if hero_url:
            hero_link = f"https://marvelcdb.com/card/{hero_card['code']}"
            st.markdown(
                f'<a href="{hero_link}" target="_blank">'
                f'<img src="{html_escape(hero_url)}" style="max-width:200px;width:100%;border-radius:8px;" '
                f'alt="{html_escape(hero_card.get("name",""))}">' 
                f'</a>',
                unsafe_allow_html=True,
            )
            st.caption(hero_card.get('name', ''))
    with id_cols[1]:
        if alter_card:
            alter_url = _card_image_url(alter_card)
            if alter_url:
                alter_link = f"https://marvelcdb.com/card/{alter_card['code']}"
                st.markdown(
                    f'<a href="{alter_link}" target="_blank">'
                    f'<img src="{html_escape(alter_url)}" style="max-width:200px;width:100%;border-radius:8px;" '
                    f'alt="{html_escape(alter_card.get("name",""))}">' 
                    f'</a>',
                    unsafe_allow_html=True,
                )
                st.caption(alter_card.get('name', ''))

    # Signature cards
    if extra_cards:
        st.markdown("---")
        total_sig = sum(c.get("quantity", 1) for c in extra_cards)
        st.markdown(f"**Signature Cards ({total_sig})**")
        _render_card_grid(extra_cards)

    # Obligation & Nemesis
    obligation, nemesis = get_obligation_nemesis(hero_card["code"], card_db)
    if obligation or nemesis:
        st.markdown("---")
        if obligation:
            st.markdown("**Obligation**")
            _render_card_grid(obligation, show_qty=False)
        if nemesis:
            total_nem = sum(c.get("quantity", 1) for c in nemesis)
            st.markdown(f"**Nemesis Set ({total_nem})**")
            _render_card_grid(nemesis)


# ─── Public helpers used by tier-list pages ───

def render_hero_card_viewer(hero_names, alter_egos=None, key_prefix="hcv"):
    """Render a hero-card-viewer bar: search box + View Cards button.

    *hero_names*: iterable of hero display names (same as keys in hero_image_urls).
    *alter_egos*: optional dict mapping hero name → alter-ego name for disambiguation.
    *key_prefix*: unique prefix so widgets don't clash across pages.
    """
    alter_egos = alter_egos or {}
    col1, col2 = st.columns([4, 1])
    with col1:
        selected = st.selectbox(
            "View Hero Cards",
            [""] + sorted(hero_names),
            key=f"{key_prefix}_sel",
            label_visibility="collapsed",
            placeholder="🔍 View hero cards…",
        )
    with col2:
        btn = st.button(
            "View Cards",
            key=f"{key_prefix}_btn",
            disabled=not selected,
            use_container_width=True,
        )
    if btn and selected:
        _hero_cards_dialog(selected, alter_egos.get(selected, ""))


def show_hero_cards_button(hero_name, alter_ego_hint="", key="hcv_inline"):
    """Render a single '🃏 Cards' button that opens the hero card dialog.

    Intended for use inline in control rows (e.g. tier-list edit controls).
    Returns True if the button was clicked.
    """
    if st.button("🃏", key=key, help=f"View {hero_name}'s cards"):
        _hero_cards_dialog(hero_name, alter_ego_hint)
        return True
    return False
