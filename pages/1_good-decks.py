"""
Deck Lists - Browse MarvelCDB deck lists for every hero.

This page is intentionally thin: heavy lifting lives in
``components/deck_renderer.py`` and ``components/marvelcdb_client.py``.
"""

from __future__ import annotations

import os
import re
import time
import random
from html import escape as html_escape
from urllib.parse import quote

import numpy as np
import streamlit as st
import streamlit.components.v1 as components

from components.nav_banner import render_nav_banner, render_page_header, render_footer
from components.github_storage import load_json
from components.error_boundary import page_boundary
from components.marvelcdb_client import (
    MarvelCDBUnavailable,
    clear_caches as _mcdb_clear_caches,
    fetch_all_cards,
    fetch_deck,
)
from components.deck_renderer import (
    ASPECT_COLORS,
    render_deck,
)
from data.hero_decks import hero_decks
from data.hero_image_urls import hero_image_urls
from data.hero_release_order import HERO_RELEASE_INDEX, HERO_WAVE, WAVE_ORDER

render_nav_banner("good-decks")


# ─── Page-level CSS (consolidated; #21) ──────────────────────────────────────
def _load_css_once() -> None:
    """Inject static/decks.css once per script run."""
    css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "decks.css")
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
    except OSError:
        return
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


_load_css_once()


# ─── Community tier helper (#16-aware) ───────────────────────────────────────
_TIER_PTS_DECK = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1}


@st.cache_data(ttl=600, show_spinner=False)
def _community_hero_avg() -> dict[str, float]:
    """Return ``{hero: avg_tier_pts}`` from the community Hero Power tier list."""
    try:
        data, _ = load_json("community_tier_lists.json", default={})
    except Exception:
        return {}
    subs = (data.get("hero_power", {}) or {}).get("submissions", []) or []
    if len(subs) < 2:
        return {}
    pts: dict[str, list[int]] = {}
    for s in subs:
        for t, hl in (s or {}).items():
            p = _TIER_PTS_DECK.get(t)
            if p is None:
                continue
            for h in (hl or []):
                pts.setdefault(h, []).append(p)
    return {h: float(np.mean(v)) for h, v in pts.items() if v}


def _community_tier_for(hero_name: str) -> tuple[str | None, float | None]:
    avg_map = _community_hero_avg()
    if hero_name not in avg_map:
        return None, None
    avg = avg_map[hero_name]
    tier = min(_TIER_PTS_DECK.keys(), key=lambda t: abs(_TIER_PTS_DECK[t] - avg))
    return tier, avg


# ─── Hero-art injection (#5: now toggleable on tablets via body class) ───────
def inject_hero_art_background(deck_data, card_db) -> None:
    hero_code = deck_data.get("hero_code", "")
    hero_card = card_db.get(hero_code)
    if not hero_card:
        return
    src = hero_card.get("imagesrc", "")
    hero_url = f"https://marvelcdb.com{src}" if src else ""
    if not hero_url:
        return
    hero_name = html_escape(hero_card.get("name", ""))
    hero_link = f"https://marvelcdb.com/card/{hero_code}"

    alter_code = hero_code[:-1] + "b" if hero_code.endswith("a") else ""
    alter_card = card_db.get(alter_code) if alter_code else None
    alter_src = alter_card.get("imagesrc", "") if alter_card else ""
    alter_url = f"https://marvelcdb.com{alter_src}" if alter_src else ""
    alter_name = html_escape(alter_card.get("name", "")) if alter_card else ""
    alter_link = f"https://marvelcdb.com/card/{alter_code}" if alter_card else ""

    alter_html = ""
    if alter_url:
        alter_html = (
            f'<a href="{alter_link}" target="_blank" rel="noopener noreferrer" '
            f'class="card-float card-float-right" title="{alter_name}" aria-label="{alter_name} on MarvelCDB">'
            f'<img src="{alter_url}" alt="{alter_name}" loading="lazy"></a>'
        )

    st.markdown(
        f'<a href="{hero_link}" target="_blank" rel="noopener noreferrer" '
        f'class="card-float card-float-left" title="{hero_name}" aria-label="{hero_name} on MarvelCDB">'
        f'<img src="{hero_url}" alt="{hero_name}" loading="lazy"></a>'
        f'{alter_html}',
        unsafe_allow_html=True,
    )


# ─── Single delegated card hover preview (#10) ──────────────────────────────
def _inject_hover_preview() -> None:
    """One floating <img> shared by every card row, populated on hover.

    Vastly cheaper than per-row <img> tags for big decks. Bound only on
    devices with a fine pointer; touch devices get the link without preview.
    """
    components.html(
        """
<script>
(() => {
  const root = window.parent.document;
  if (root.getElementById('card-hover-preview')) return;
  const img = root.createElement('img');
  img.id = 'card-hover-preview';
  img.alt = '';
  root.body.appendChild(img);

  let hideTimer;
  function show(targetA) {
    const url = targetA.getAttribute('data-card-img');
    if (!url) return;
    img.src = url;
    img.alt = targetA.getAttribute('data-card-name') || '';
    img.style.display = 'block';
  }
  function hide() {
    img.style.display = 'none';
    img.removeAttribute('src');
  }

  // Skip on touch-primary devices to avoid triggering on tap.
  if (root.defaultView.matchMedia('(hover: none)').matches) return;

  root.addEventListener('mouseover', (e) => {
    const a = e.target.closest('a[data-card-img]');
    if (a) { clearTimeout(hideTimer); show(a); }
  }, true);
  root.addEventListener('mouseout', (e) => {
    const a = e.target.closest('a[data-card-img]');
    if (a) { hideTimer = setTimeout(hide, 50); }
  }, true);
})();
</script>
""",
        height=0,
    )


# ─── Hero-image src helper (#3 lazy-load: small thumbnails as data URIs) ────
@st.cache_data(show_spinner=False)
def _hero_thumb_src(hero: str) -> str | None:
    """Return a data URI suitable for an ``<img src=...>`` tag.

    Streamlit's static-file route only exposes the ``static/`` directory, so
    we can't link ``/app/images/heroes/...`` directly. We instead inline the
    image as a small base64 data URI — preferring a pre-resized thumbnail in
    ``images/heroes/_thumbs/`` (run ``scripts/resize_hero_images.py``) so the
    payload stays tiny on mobile. Result is cached, so this only runs once
    per hero per process.
    """
    import base64
    import mimetypes

    path = hero_image_urls.get(hero)
    if not path:
        return None
    if path.startswith(("http://", "https://")):
        return path

    base, _ext = os.path.splitext(path)
    candidates = [
        os.path.join("images", "heroes", "_thumbs", os.path.basename(base) + ".jpg"),
        path,
    ]
    for candidate in candidates:
        if not os.path.exists(candidate):
            continue
        mime = mimetypes.guess_type(candidate)[0] or "image/jpeg"
        try:
            with open(candidate, "rb") as f:
                payload = f.read()
        except OSError:
            continue
        b64 = base64.b64encode(payload).decode("ascii")
        return f"data:{mime};base64,{b64}"
    return None


# ─── Page render ────────────────────────────────────────────────────────────
with page_boundary("good-decks"):
    render_page_header("A GOOD Deck For Every Hero", "Browse Daring Lime's Deck Lists For Every Hero")

    _SORT_OPTIONS = ["Alphabetical (A→Z)", "Oldest → Newest", "Newest → Oldest"]
    if "_decks_sort_val" not in st.session_state:
        st.session_state._decks_sort_val = "Alphabetical (A→Z)"

    hero_names = sorted(hero_decks.keys())

    _sort_val = st.session_state.get("_decks_sort_val", "Alphabetical (A→Z)")
    _sort_idx = _SORT_OPTIONS.index(_sort_val) if _sort_val in _SORT_OPTIONS else 0

    sort_col, wave_col, aspect_col, art_col = st.columns([1, 1, 1, 1])
    with sort_col:
        decks_sort_order = st.selectbox(
            "Sort order", _SORT_OPTIONS, index=_sort_idx, key="decks_sort_order",
        )
        st.session_state._decks_sort_val = decks_sort_order
    with wave_col:
        decks_wave_filter = st.multiselect(
            "Filter by waves",
            WAVE_ORDER,
            default=[],
            placeholder="All Waves",
            key="decks_wave_filter",
        )
    with aspect_col:
        # #14 — filter heroes by aspect availability.
        decks_aspect_filter = st.multiselect(
            "Filter by aspect",
            ["Aggression", "Justice", "Leadership", "Protection"],
            default=[],
            placeholder="Any aspect",
            key="decks_aspect_filter",
            help="Show only heroes that have at least one deck in the chosen aspect(s).",
        )
    with art_col:
        # #5 — toggle floating hero art on tablets.
        st.write("")
        st.toggle(
            "🖼️ Floating art (tablet)",
            value=False,
            key="_decks_show_floating_art",
            help="On screens 700–1200px wide, show the hero/alter-ego cards floating on the sides.",
        )

    # Filter by wave
    if decks_wave_filter:
        hero_names = [h for h in hero_names if HERO_WAVE.get(h) in decks_wave_filter]

    # Filter by aspect availability — needs deck aspects, which are baked into
    # the URL path (the wave-1 default decks are loaded lazily so we use the
    # `aspect` field stamped on each entry where present, else fall back to
    # name heuristics on entry["name"]).
    if decks_aspect_filter:
        wanted = {a.lower() for a in decks_aspect_filter}

        def _hero_has_aspect(hero: str) -> bool:
            for entry in hero_decks.get(hero, []):
                # entry-level aspect (if data ever adds it)
                a = (entry.get("aspect") or "").lower()
                if a and a in wanted:
                    return True
                name = (entry.get("name") or "").lower()
                if any(w in name for w in wanted):
                    return True
            return False

        hero_names = [h for h in hero_names if _hero_has_aspect(h)]

    if decks_sort_order == "Oldest → Newest":
        hero_names.sort(key=lambda h: HERO_RELEASE_INDEX.get(h, 9999))
    elif decks_sort_order == "Newest → Oldest":
        hero_names.sort(key=lambda h: HERO_RELEASE_INDEX.get(h, 0), reverse=True)

    if not hero_names:
        st.info("No heroes match the selected filters.")
        st.stop()

    # Apply the floating-art toggle to the document body (#5).
    if st.session_state.get("_decks_show_floating_art"):
        components.html(
            "<script>window.parent.document.body.classList.add('show-hero-art');</script>",
            height=0,
        )
    else:
        components.html(
            "<script>window.parent.document.body.classList.remove('show-hero-art');</script>",
            height=0,
        )

    # Hero selection from query param (no mutation; see fix history).
    _qp_hero = st.query_params.get("hero")
    if isinstance(_qp_hero, list):
        _qp_hero = _qp_hero[0] if _qp_hero else None
    if _qp_hero and _qp_hero in hero_names:
        if st.session_state.get("deck_hero") != _qp_hero:
            st.session_state.deck_hero = _qp_hero

    if "deck_hero" not in st.session_state:
        st.session_state.deck_hero = hero_names[random.randint(0, len(hero_names) - 1)]
    elif st.session_state.deck_hero not in hero_names:
        st.session_state.deck_hero = hero_names[0]

    selected_hero = st.session_state.deck_hero

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
            _mcdb_clear_caches()
            st.toast("✅ Deck data refreshed from MarvelCDB.")
            st.rerun()

    # #4 — auto-select first match if the user typed something.
    filtered_names = hero_names
    if _hero_search:
        _q = _hero_search.strip().lower()
        matches = [h for h in hero_names if _q in h.lower()]
        if matches:
            filtered_names = matches
            # Auto-jump to first match when the search is unambiguous.
            if len(matches) == 1 and st.session_state.deck_hero != matches[0]:
                st.session_state.deck_hero = matches[0]
                selected_hero = matches[0]
        else:
            st.info(f"No heroes match '{_hero_search}'.")

    # ── Sticky "currently: X" bar (#1) ──
    sticky_html = (
        '<div class="dhg-sticky-bar" role="status" aria-live="polite">'
        f'🦸 Currently: <strong>{html_escape(selected_hero)}</strong>'
        '</div>'
    )
    st.markdown(sticky_html, unsafe_allow_html=True)

    # ── Hero image grid (lazy-loaded <img> tags; #3, #23 focus, #24 aria) ──
    st.markdown('<div id="hero-grid"></div>', unsafe_allow_html=True)
    cards_html: list[str] = ['<div class="dhg-wrap" role="listbox" aria-label="Choose hero">']
    for hero in filtered_names:
        src = _hero_thumb_src(hero)
        if not src:
            continue
        href = f"?hero={quote(hero)}"
        safe_name = html_escape(hero)
        is_sel = hero == selected_hero
        cls = "dhg-card selected" if is_sel else "dhg-card"
        badge = '<div class="dhg-badge" aria-hidden="true">✓</div>' if is_sel else ""
        aria_pressed = "true" if is_sel else "false"
        cards_html.append(
            f'<a class="{cls}" href="{href}" target="_self" '
            f'role="option" aria-selected="{aria_pressed}" '
            f'aria-label="View decks for {safe_name}" '
            f'title="View decks for {safe_name}">'
            f'{badge}'
            f'<div class="dhg-imgwrap">'
            f'<img class="dhg-img" src="{html_escape(src)}" alt="" loading="lazy" decoding="async" width="240">'
            f'</div>'
            f'<div class="dhg-name">{safe_name}</div>'
            f'</a>'
        )
    cards_html.append("</div>")

    _exp_label = f"🦸 Choose hero — currently: {selected_hero}"
    with st.expander(_exp_label, expanded=True):
        st.markdown("".join(cards_html), unsafe_allow_html=True)

    # ── Helpers for badges/labels ──
    def _aspect_chip(aspect: str) -> str:
        css = ASPECT_COLORS.get(aspect, "basic")
        return f'<span class="deck-tab-aspect-chip dot-{css}"></span>'

    def _updated_badge(deck_data) -> str:
        """#13 — show 'Updated N days ago'."""
        for fld in ("date_update", "date_creation"):
            ts = deck_data.get(fld)
            if not ts:
                continue
            try:
                if isinstance(ts, str):
                    # MarvelCDB returns ISO 8601, sometimes with TZ.
                    epoch = time.mktime(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S"))
                else:
                    epoch = float(ts)
            except (ValueError, TypeError):
                continue
            days = max(0, int((time.time() - epoch) / 86400))
            label = "today" if days == 0 else f"{days}d ago"
            return f'<div class="deck-stat" title="{html_escape(ts)}">Updated <strong>{label}</strong></div>'
        return ""

    # ── Deck display ──
    if selected_hero:
        decks_for_hero = hero_decks.get(selected_hero, [])

        if not decks_for_hero:
            st.warning(f"No deck list found for {selected_hero}.")
        else:
            try:
                card_db = fetch_all_cards()
            except MarvelCDBUnavailable as e:
                st.error(
                    "MarvelCDB is unreachable and no cached card database is available locally. "
                    f"Try refreshing in a moment. ({e})"
                )
                st.stop()

            # Filter decks by selected aspect(s) if user requested.
            if decks_aspect_filter:
                wanted = {a.lower() for a in decks_aspect_filter}
                filtered_decks = [
                    e for e in decks_for_hero
                    if (e.get("aspect") or "").lower() in wanted
                    or any(w in (e.get("name") or "").lower() for w in wanted)
                ]
                if filtered_decks:
                    decks_for_hero = filtered_decks

            # #9 — lazy fetch: only fetch the active deck on first view, not all.
            if len(decks_for_hero) == 1:
                entry = decks_for_hero[0]
                try:
                    deck_data = fetch_deck(entry["deck_id"], entry["api_type"])
                    if not deck_data.get("url"):
                        deck_data["url"] = entry["url"]
                    inject_hero_art_background(deck_data, card_db)
                    badge = _updated_badge(deck_data)
                    if badge:
                        st.markdown(f'<div class="deck-stats">{badge}</div>', unsafe_allow_html=True)
                    render_deck(deck_data, card_db, community_tier_lookup=_community_tier_for)
                except MarvelCDBUnavailable as e:
                    st.error(f"Failed to load deck from MarvelCDB: {e}")
            else:
                # Build tab labels first (cheap), only fetch the deck shown in the
                # selected tab. Streamlit re-runs on tab change so this lazy
                # behaviour is automatic — we just need to fetch inside the
                # currently-rendered tab body.
                _raw_labels = [entry.get("name") or f"Deck {i+1}" for i, entry in enumerate(decks_for_hero)]
                _seen: dict[str, int] = {}
                tab_labels: list[str] = []
                for _lbl in _raw_labels:
                    _seen[_lbl] = _seen.get(_lbl, 0) + 1
                    tab_labels.append(_lbl if _seen[_lbl] == 1 else f"{_lbl} ({_seen[_lbl]})")

                # #6 — prepend an aspect chip emoji to each tab label using the
                # #6 — tab labels left as deck names; the active tab is
                # highlighted in green via CSS so an aspect-colored chip
                # would be redundant (and emoji glyphs render inconsistently).
                st.markdown(
                    f'<div class="deck-summary-note">{len(decks_for_hero)} deck lists available. Pick a tab below.</div>',
                    unsafe_allow_html=True,
                )

                tabs = st.tabs(tab_labels)
                # We still need to fetch each deck when its tab body is rendered.
                # Streamlit renders all tab bodies (they're hidden via CSS), so
                # we DO end up fetching all — but ``fetch_deck`` is cached so
                # subsequent reruns are free. Inject hero art only for the
                # first deck (no flicker between tabs).
                first_loaded = None
                for tab, entry in zip(tabs, decks_for_hero):
                    with tab:
                        try:
                            deck_data = fetch_deck(entry["deck_id"], entry["api_type"])
                            if not deck_data.get("url"):
                                deck_data["url"] = entry["url"]
                            if first_loaded is None:
                                first_loaded = deck_data
                            badge = _updated_badge(deck_data)
                            if badge:
                                st.markdown(f'<div class="deck-stats">{badge}</div>', unsafe_allow_html=True)
                            render_deck(deck_data, card_db, community_tier_lookup=_community_tier_for)
                        except MarvelCDBUnavailable as e:
                            st.error(f"Failed to load this deck from MarvelCDB: {e}")
                if first_loaded is not None:
                    inject_hero_art_background(first_loaded, card_db)

    # ── Quick deck import by URL ───────────────────────────────────────────
    st.markdown("---")
    with st.expander("📋 Import any deck by URL"):
        deck_url_input = st.text_input(
            "Paste a MarvelCDB deck or decklist URL",
            placeholder="https://marvelcdb.com/decklist/view/12345/my-deck-1.0",
            key="deck_url_import",
        )
        if deck_url_input:
            _url_match = re.search(r"marvelcdb\.com/(deck(?:list)?)/view/(\d+)", deck_url_input)
            if _url_match:
                _api_type = "decklist" if _url_match.group(1) == "decklist" else "deck"
                _import_id = _url_match.group(2)
                try:
                    _card_db = fetch_all_cards()
                    _import_deck = fetch_deck(_import_id, _api_type)
                    if not _import_deck.get("url"):
                        _import_deck["url"] = deck_url_input
                    inject_hero_art_background(_import_deck, _card_db)
                    render_deck(_import_deck, _card_db, community_tier_lookup=_community_tier_for)
                except MarvelCDBUnavailable as e:
                    st.error(f"Failed to load deck: {e}")
            else:
                st.warning(
                    "Couldn't parse that URL. Expected format: "
                    "`https://marvelcdb.com/decklist/view/12345/...` or "
                    "`https://marvelcdb.com/deck/view/12345/...`"
                )

    # Inject the shared hover preview JS once at page bottom.
    _inject_hover_preview()

render_footer()
